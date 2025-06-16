"""
Log forwarder module for Marzban Node Agent.

This module implements the main log forwarding functionality,
including real-time log monitoring, batching, and Redis communication.
"""

import asyncio
import json
import logging
import os
from typing import List, Dict, Any, Optional
import aiofiles
import redis.asyncio as redis
from .config import NodeConfig, ConfigService
from .log_parser import create_log_entry


class LogForwarder:
    """Main log forwarding agent for Marzban nodes."""
    
    def __init__(self, config: NodeConfig):
        """
        Initialize the log forwarder.
        
        Args:
            config: Node configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Redis connection
        self.redis_client: Optional[redis.Redis] = None
        
        # Buffering and batching
        self.log_buffer: List[Dict[str, Any]] = []
        self.last_flush_time = asyncio.get_event_loop().time()
        
        # File position tracking
        self.current_position = 0
        self.position_key = ConfigService.get_redis_position_key(config.node_id)
        self.queue_key = ConfigService.get_redis_queue_key()
        
        # Control flags
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self) -> None:
        """Start the log forwarder agent."""
        if self._running:
            self.logger.warning("LogForwarder is already running")
            return
        
        self.logger.info(f"Starting LogForwarder for node {self.config.node_id}")
        self._running = True
        
        try:
            # Connect to Redis
            await self._connect_redis()
            
            # Restore file position
            await self._restore_position()
            
            # Start background tasks
            self._tasks = [
                asyncio.create_task(self._tail_logs()),
                asyncio.create_task(self._flush_scheduler())
            ]
            
            # Wait for all tasks
            await asyncio.gather(*self._tasks)
            
        except Exception as e:
            self.logger.error(f"Error in LogForwarder: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Gracefully stop the log forwarder."""
        if not self._running:
            return
        
        self.logger.info("Stopping LogForwarder...")
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Flush remaining logs
        if self.log_buffer:
            await self._flush_batch()
        
        # Save current position
        await self._save_position()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info("LogForwarder stopped")
    
    async def _connect_redis(self) -> None:
        """Connect to central Redis server with retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                self.redis_client = redis.from_url(
                    self.config.central_redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                
                # Test connection
                await self.redis_client.ping()
                self.logger.info("Connected to central Redis server")
                return
                
            except Exception as e:
                self.logger.error(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    raise
    
    async def _tail_logs(self) -> None:
        """Monitor access.log file in real-time."""
        self.logger.info(f"Starting to tail {self.config.access_log_path}")
        
        while self._running:
            try:
                # Check if file exists
                if not os.path.exists(self.config.access_log_path):
                    self.logger.warning(f"Log file {self.config.access_log_path} not found, waiting...")
                    await asyncio.sleep(5)
                    continue
                
                # Open file and seek to saved position
                async with aiofiles.open(self.config.access_log_path, 'r') as f:
                    await f.seek(self.current_position)
                    
                    while self._running:
                        line = await f.readline()
                        
                        if not line:
                            # No new data, wait a bit
                            await asyncio.sleep(0.1)
                            continue
                        
                        # Update position
                        self.current_position = await f.tell()
                        
                        # Process the log line
                        await self._process_log_line(line.strip())
                        
            except FileNotFoundError:
                self.logger.warning(f"Log file {self.config.access_log_path} disappeared, waiting...")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Error reading log file: {e}")
                await asyncio.sleep(5)
    
    async def _process_log_line(self, line: str) -> None:
        """
        Process a single log line.
        
        Args:
            line: Raw log line from access.log
        """
        if not line:
            return
        
        # Parse log line
        log_entry = create_log_entry(line, self.config.node_id, self.config.node_name)
        
        if log_entry:
            self.log_buffer.append(log_entry)
            self.logger.debug(f"Buffered log entry: {log_entry['email']} from {log_entry['client_ip']}")
            
            # Check if we should flush
            if len(self.log_buffer) >= self.config.batch_size:
                await self._flush_batch()
    
    async def _flush_batch(self) -> None:
        """Flush batched logs to Redis."""
        if not self.log_buffer:
            return
        
        batch = self.log_buffer.copy()
        self.log_buffer.clear()
        
        for attempt in range(self.config.max_retries):
            try:
                # Serialize logs
                serialized_logs = [json.dumps(log_entry) for log_entry in batch]
                
                # Send to Redis queue
                if serialized_logs:
                    await self.redis_client.lpush(self.queue_key, *serialized_logs)
                    self.logger.info(f"Sent {len(serialized_logs)} log entries to Redis")
                
                # Save position after successful send
                await self._save_position()
                self.last_flush_time = asyncio.get_event_loop().time()
                return
                
            except Exception as e:
                self.logger.error(f"Failed to send logs (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    # Put logs back in buffer for retry
                    self.log_buffer = batch + self.log_buffer
                    self.logger.error(f"Failed to send {len(batch)} logs after {self.config.max_retries} attempts")
    
    async def _flush_scheduler(self) -> None:
        """Periodically flush logs based on time interval."""
        while self._running:
            await asyncio.sleep(self.config.flush_interval)
            
            current_time = asyncio.get_event_loop().time()
            time_since_flush = current_time - self.last_flush_time
            
            if self.log_buffer and time_since_flush >= self.config.flush_interval:
                await self._flush_batch()
    
    async def _restore_position(self) -> None:
        """Restore file position from Redis."""
        try:
            if self.redis_client:
                position_str = await self.redis_client.get(self.position_key)
                if position_str:
                    self.current_position = int(position_str)
                    self.logger.info(f"Restored file position: {self.current_position}")
                else:
                    self.logger.info("No saved position found, starting from end of file")
                    # Start from end of file if no position saved
                    if os.path.exists(self.config.access_log_path):
                        with open(self.config.access_log_path, 'r') as f:
                            f.seek(0, 2)  # Seek to end
                            self.current_position = f.tell()
        except Exception as e:
            self.logger.error(f"Failed to restore position: {e}")
            self.current_position = 0
    
    async def _save_position(self) -> None:
        """Save current file position to Redis."""
        try:
            if self.redis_client:
                await self.redis_client.set(self.position_key, str(self.current_position))
                self.logger.debug(f"Saved position: {self.current_position}")
        except Exception as e:
            self.logger.error(f"Failed to save position: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current forwarder statistics.
        
        Returns:
            Dictionary with current stats
        """
        return {
            'running': self._running,
            'buffer_size': len(self.log_buffer),
            'current_position': self.current_position,
            'redis_connected': self.redis_client is not None,
            'node_id': self.config.node_id,
            'node_name': self.config.node_name
        }
