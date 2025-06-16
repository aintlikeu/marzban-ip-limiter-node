"""
Main entry point for Marzban Node Agent.

This module provides the main NodeAgent class and entry point
for running the log forwarding agent.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
from .config import ConfigService, NodeConfig
from .log_forwarder import LogForwarder


class NodeAgent:
    """Main Node Agent class for managing log forwarding."""
    
    def __init__(self, config: NodeConfig):
        """
        Initialize the Node Agent.
        
        Args:
            config: Node configuration
        """
        self.config = config
        self.log_forwarder: Optional[LogForwarder] = None
        self.logger = self._setup_logging()
        self._shutdown_event = asyncio.Event()
    
    def _setup_logging(self) -> logging.Logger:
        """
        Setup logging configuration.
        
        Returns:
            Configured logger instance
        """
        # Configure logging format
        log_format = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            f'[{self.config.node_id}] - %(message)s'
        )
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Reduce Redis library log level
        logging.getLogger('redis').setLevel(logging.WARNING)
        logging.getLogger('aiofiles').setLevel(logging.WARNING)
        
        return logging.getLogger(__name__)
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    async def start(self) -> None:
        """Start the Node Agent."""
        self.logger.info(f"Starting Marzban Node Agent v1.0.0")
        self.logger.info(f"Node ID: {self.config.node_id}")
        self.logger.info(f"Node Name: {self.config.node_name}")
        self.logger.info(f"Access Log Path: {self.config.access_log_path}")
        self.logger.info(f"Central Redis: {self.config.central_redis_url}")
        self.logger.info(f"Batch Size: {self.config.batch_size}")
        self.logger.info(f"Flush Interval: {self.config.flush_interval}s")
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        retry_count = 0
        max_restarts = 5
        base_delay = 5
        
        while retry_count < max_restarts and not self._shutdown_event.is_set():
            try:
                # Create log forwarder
                self.log_forwarder = LogForwarder(self.config)
                
                # Start forwarder
                forwarder_task = asyncio.create_task(self.log_forwarder.start())
                shutdown_task = asyncio.create_task(self._shutdown_event.wait())
                
                # Wait for either forwarder completion or shutdown signal
                done, pending = await asyncio.wait(
                    [forwarder_task, shutdown_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
                # Check if shutdown was requested
                if self._shutdown_event.is_set():
                    self.logger.info("Shutdown requested")
                    break
                
                # Check if forwarder task completed with exception
                if forwarder_task in done:
                    try:
                        await forwarder_task
                    except Exception as e:
                        self.logger.error(f"LogForwarder crashed: {e}")
                        retry_count += 1
                        if retry_count < max_restarts:
                            delay = base_delay * (2 ** (retry_count - 1))
                            self.logger.info(f"Restarting in {delay} seconds... (attempt {retry_count}/{max_restarts})")
                            await asyncio.sleep(delay)
                        else:
                            self.logger.error("Maximum restart attempts reached, exiting")
                            break
                
            except Exception as e:
                self.logger.error(f"Unexpected error in NodeAgent: {e}")
                retry_count += 1
                if retry_count < max_restarts:
                    delay = base_delay * (2 ** (retry_count - 1))
                    self.logger.info(f"Restarting in {delay} seconds... (attempt {retry_count}/{max_restarts})")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error("Maximum restart attempts reached, exiting")
                    break
            finally:
                # Cleanup
                if self.log_forwarder:
                    try:
                        await self.log_forwarder.stop()
                    except Exception as e:
                        self.logger.error(f"Error stopping log forwarder: {e}")
        
        self.logger.info("Node Agent shutdown complete")
    
    async def stop(self) -> None:
        """Stop the Node Agent."""
        self._shutdown_event.set()
        if self.log_forwarder:
            await self.log_forwarder.stop()


async def main() -> None:
    """Main entry point for the application."""
    try:
        # Load configuration
        config = ConfigService.load_from_env()
        
        # Create and start agent
        agent = NodeAgent(config)
        await agent.start()
        
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Set event loop policy for Windows compatibility
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
