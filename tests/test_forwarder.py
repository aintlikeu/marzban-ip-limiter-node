"""
Tests for log forwarder functionality.

This module contains unit tests for the LogForwarder class,
including Redis communication, batching, and error handling.
"""

import asyncio
import json
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from node_agent.config import NodeConfig
from node_agent.log_forwarder import LogForwarder


class TestLogForwarder:
    """Test cases for LogForwarder class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return NodeConfig(
            node_id="test-node",
            node_name="Test Node",
            central_redis_url="redis://localhost:6379/0",
            access_log_path="/tmp/test_access.log",
            batch_size=3,
            flush_interval=1.0,
            max_retries=2,
            retry_delay=0.1,
            log_level="DEBUG"
        )
    
    @pytest.fixture
    async def forwarder(self, config):
        """Create LogForwarder instance."""
        forwarder = LogForwarder(config)
        yield forwarder
        if forwarder._running:
            await forwarder.stop()
    
    @pytest.mark.asyncio
    async def test_initialization(self, config):
        """Test LogForwarder initialization."""
        forwarder = LogForwarder(config)
        
        assert forwarder.config == config
        assert forwarder.log_buffer == []
        assert forwarder.current_position == 0
        assert not forwarder._running
    
    @pytest.mark.asyncio
    async def test_redis_connection_success(self, forwarder):
        """Test successful Redis connection."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            await forwarder._connect_redis()
            
        assert forwarder.redis_client == mock_redis
        mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_connection_retry(self, forwarder):
        """Test Redis connection with retries."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=[Exception("Connection failed"), None])
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            await forwarder._connect_redis()
        
        assert mock_redis.ping.call_count == 2
    
    @pytest.mark.asyncio
    async def test_redis_connection_max_retries(self, forwarder):
        """Test Redis connection failure after max retries."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            with pytest.raises(Exception):
                await forwarder._connect_redis()
        
        assert mock_redis.ping.call_count == forwarder.config.max_retries
    
    @pytest.mark.asyncio
    async def test_process_log_line_valid(self, forwarder):
        """Test processing valid log line."""
        log_line = "2024/01/15 10:30:45 [info] accepted connection from 192.168.1.100 email: user@example.com"
        
        await forwarder._process_log_line(log_line)
        
        assert len(forwarder.log_buffer) == 1
        log_entry = forwarder.log_buffer[0]
        assert log_entry['email'] == 'user@example.com'
        assert log_entry['client_ip'] == '192.168.1.100'
        assert log_entry['node_id'] == 'test-node'
    
    @pytest.mark.asyncio
    async def test_process_log_line_invalid(self, forwarder):
        """Test processing invalid log line."""
        log_line = "2024/01/15 10:30:45 [info] some other log entry"
        
        await forwarder._process_log_line(log_line)
        
        assert len(forwarder.log_buffer) == 0
    
    @pytest.mark.asyncio
    async def test_batch_flush_trigger(self, forwarder):
        """Test automatic flush when batch size is reached."""
        forwarder.redis_client = AsyncMock()
        forwarder.redis_client.lpush = AsyncMock()
        
        # Add logs to trigger batch flush
        for i in range(forwarder.config.batch_size):
            log_line = f"2024/01/15 10:30:45 [info] accepted connection from 192.168.1.{i} email: user{i}@example.com"
            await forwarder._process_log_line(log_line)
        
        # Should have flushed automatically
        forwarder.redis_client.lpush.assert_called()
        assert len(forwarder.log_buffer) == 0
    
    @pytest.mark.asyncio
    async def test_flush_batch_success(self, forwarder):
        """Test successful batch flush to Redis."""
        forwarder.redis_client = AsyncMock()
        forwarder.redis_client.lpush = AsyncMock()
        forwarder.redis_client.set = AsyncMock()
        
        # Add test logs
        test_log = {
            'timestamp': 1234567890,
            'node_id': 'test-node',
            'email': 'test@example.com',
            'client_ip': '192.168.1.1'
        }
        forwarder.log_buffer = [test_log]
        
        await forwarder._flush_batch()
        
        # Verify Redis calls
        forwarder.redis_client.lpush.assert_called_once()
        forwarder.redis_client.set.assert_called_once()
        assert len(forwarder.log_buffer) == 0
    
    @pytest.mark.asyncio
    async def test_flush_batch_retry_on_failure(self, forwarder):
        """Test batch flush retry on Redis failure."""
        forwarder.redis_client = AsyncMock()
        forwarder.redis_client.lpush = AsyncMock(side_effect=[Exception("Redis error"), None])
        forwarder.redis_client.set = AsyncMock()
        
        test_log = {'test': 'data'}
        forwarder.log_buffer = [test_log]
        
        await forwarder._flush_batch()
        
        # Should have retried
        assert forwarder.redis_client.lpush.call_count == 2
        assert len(forwarder.log_buffer) == 0
    
    @pytest.mark.asyncio
    async def test_position_save_restore(self, forwarder):
        """Test file position save and restore."""
        forwarder.redis_client = AsyncMock()
        forwarder.redis_client.get = AsyncMock(return_value="1000")
        forwarder.redis_client.set = AsyncMock()
        
        # Test restore
        await forwarder._restore_position()
        assert forwarder.current_position == 1000
        
        # Test save
        forwarder.current_position = 2000
        await forwarder._save_position()
        forwarder.redis_client.set.assert_called_with(forwarder.position_key, "2000")
    
    @pytest.mark.asyncio
    async def test_file_tail_functionality(self, forwarder):
        """Test file tailing functionality."""
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            test_log_path = f.name
            f.write("2024/01/15 10:30:45 [info] accepted connection from 192.168.1.1 email: test@example.com\n")
        
        try:
            forwarder.config.access_log_path = test_log_path
            forwarder.redis_client = AsyncMock()
            forwarder.redis_client.lpush = AsyncMock()
            forwarder.redis_client.set = AsyncMock()
            forwarder._running = True
            
            # Mock file processing
            with patch.object(forwarder, '_process_log_line') as mock_process:
                mock_process.return_value = None
                
                # Start tailing (this would normally run indefinitely)
                tail_task = asyncio.create_task(forwarder._tail_logs())
                
                # Let it run briefly
                await asyncio.sleep(0.1)
                
                # Stop tailing
                forwarder._running = False
                tail_task.cancel()
                
                # Verify log line was processed
                mock_process.assert_called()
        
        finally:
            os.unlink(test_log_path)
    
    def test_get_stats(self, config):
        """Test statistics retrieval."""
        forwarder = LogForwarder(config)
        forwarder.log_buffer = [{'test': 'data'}]
        forwarder.current_position = 500
        
        stats = forwarder.get_stats()
        
        assert stats['running'] == False
        assert stats['buffer_size'] == 1
        assert stats['current_position'] == 500
        assert stats['node_id'] == 'test-node'
        assert stats['node_name'] == 'Test Node'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
