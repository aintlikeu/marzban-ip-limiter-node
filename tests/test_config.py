"""
Tests for configuration functionality.

This module contains unit tests for the configuration loading
and validation functionality.
"""

import os
import tempfile
import pytest
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from node_agent.config import NodeConfig, ConfigService


class TestNodeConfig:
    """Test cases for NodeConfig class."""
    
    def test_valid_config(self):
        """Test valid configuration creation."""
        config = NodeConfig(
            node_id="test-001",
            node_name="Test Node",
            central_redis_url="redis://localhost:6379/0",
            access_log_path="/var/lib/marzban-node/access.log"
        )
        
        assert config.node_id == "test-001"
        assert config.node_name == "Test Node"
        assert config.batch_size == 50  # default value
        assert config.flush_interval == 3.0  # default value
        assert config.log_level == "INFO"  # default value
    
    def test_missing_required_fields(self):
        """Test validation of required fields."""
        with pytest.raises(ValueError, match="NODE_ID is required"):
            NodeConfig(
                node_id="",
                node_name="Test Node",
                central_redis_url="redis://localhost:6379/0",
                access_log_path="/var/lib/marzban-node/access.log"
            )
        
        with pytest.raises(ValueError, match="NODE_NAME is required"):
            NodeConfig(
                node_id="test-001",
                node_name="",
                central_redis_url="redis://localhost:6379/0",
                access_log_path="/var/lib/marzban-node/access.log"
            )
    
    def test_invalid_numeric_values(self):
        """Test validation of numeric parameters."""
        with pytest.raises(ValueError, match="BATCH_SIZE must be positive"):
            NodeConfig(
                node_id="test-001",
                node_name="Test Node",
                central_redis_url="redis://localhost:6379/0",
                access_log_path="/var/lib/marzban-node/access.log",
                batch_size=0
            )
        
        with pytest.raises(ValueError, match="FLUSH_INTERVAL must be positive"):
            NodeConfig(
                node_id="test-001",
                node_name="Test Node",
                central_redis_url="redis://localhost:6379/0",
                access_log_path="/var/lib/marzban-node/access.log",
                flush_interval=-1.0
            )
    
    def test_invalid_log_level(self):
        """Test validation of log level."""
        with pytest.raises(ValueError, match="Invalid LOG_LEVEL"):
            NodeConfig(
                node_id="test-001",
                node_name="Test Node",
                central_redis_url="redis://localhost:6379/0",
                access_log_path="/var/lib/marzban-node/access.log",
                log_level="INVALID"
            )
    
    def test_log_level_normalization(self):
        """Test log level case normalization."""
        config = NodeConfig(
            node_id="test-001",
            node_name="Test Node",
            central_redis_url="redis://localhost:6379/0",
            access_log_path="/var/lib/marzban-node/access.log",
            log_level="debug"
        )
        
        assert config.log_level == "DEBUG"


class TestConfigService:
    """Test cases for ConfigService class."""
    
    def test_load_from_env_with_all_vars(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            'NODE_ID': 'env-test-001',
            'NODE_NAME': 'Environment Test Node',
            'CENTRAL_REDIS_URL': 'redis://test:6379/1',
            'ACCESS_LOG_PATH': '/tmp/test.log',
            'BATCH_SIZE': '25',
            'FLUSH_INTERVAL': '2.5',
            'MAX_RETRIES': '3',
            'RETRY_DELAY': '1.5',
            'LOG_LEVEL': 'WARNING'
        }
        
        # Set environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
        
        try:
            config = ConfigService.load_from_env()
            
            assert config.node_id == 'env-test-001'
            assert config.node_name == 'Environment Test Node'
            assert config.central_redis_url == 'redis://test:6379/1'
            assert config.access_log_path == '/tmp/test.log'
            assert config.batch_size == 25
            assert config.flush_interval == 2.5
            assert config.max_retries == 3
            assert config.retry_delay == 1.5
            assert config.log_level == 'WARNING'
        
        finally:
            # Clean up environment variables
            for key in env_vars:
                os.environ.pop(key, None)
    
    def test_load_from_env_with_defaults(self):
        """Test loading configuration with default values."""
        env_vars = {
            'NODE_ID': 'minimal-test',
            'NODE_NAME': 'Minimal Test Node',
            'CENTRAL_REDIS_URL': 'redis://localhost:6379/0'
        }
        
        # Set minimal environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
        
        try:
            config = ConfigService.load_from_env()
            
            assert config.node_id == 'minimal-test'
            assert config.access_log_path == '/var/lib/marzban-node/access.log'  # default
            assert config.batch_size == 50  # default
            assert config.flush_interval == 3.0  # default
            assert config.log_level == 'INFO'  # default
        
        finally:
            # Clean up environment variables
            for key in env_vars:
                os.environ.pop(key, None)
    
    def test_load_from_env_file(self):
        """Test loading configuration from .env file."""
        env_content = """
NODE_ID=file-test-001
NODE_NAME=File Test Node
CENTRAL_REDIS_URL=redis://file-test:6379/0
ACCESS_LOG_PATH=/tmp/file-test.log
BATCH_SIZE=100
LOG_LEVEL=DEBUG
        """.strip()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            env_file_path = f.name
        
        try:
            config = ConfigService.load_from_env(env_file_path)
            
            assert config.node_id == 'file-test-001'
            assert config.node_name == 'File Test Node'
            assert config.batch_size == 100
            assert config.log_level == 'DEBUG'
        
        finally:
            os.unlink(env_file_path)
    
    def test_missing_required_env_vars(self):
        """Test handling of missing required environment variables."""
        # Clear any existing environment variables
        env_vars_to_clear = ['NODE_ID', 'NODE_NAME', 'CENTRAL_REDIS_URL']
        original_values = {}
        
        for var in env_vars_to_clear:
            original_values[var] = os.environ.pop(var, None)
        
        try:
            with pytest.raises(ValueError, match="NODE_ID is required"):
                ConfigService.load_from_env()
        
        finally:
            # Restore original values
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
    
    def test_redis_keys_generation(self):
        """Test Redis key generation methods."""
        position_key = ConfigService.get_redis_position_key("test-node-123")
        queue_key = ConfigService.get_redis_queue_key()
        
        assert position_key == "node_agent:test-node-123:position"
        assert queue_key == "node_logs_queue"
    
    def test_whitespace_handling(self):
        """Test proper handling of whitespace in environment variables."""
        env_vars = {
            'NODE_ID': '  spaced-node  ',
            'NODE_NAME': '  Spaced Node Name  ',
            'CENTRAL_REDIS_URL': '  redis://localhost:6379/0  ',
            'ACCESS_LOG_PATH': '  /tmp/spaced.log  '
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
        
        try:
            config = ConfigService.load_from_env()
            
            assert config.node_id == 'spaced-node'
            assert config.node_name == 'Spaced Node Name'
            assert config.central_redis_url == 'redis://localhost:6379/0'
            assert config.access_log_path == '/tmp/spaced.log'
        
        finally:
            for key in env_vars:
                os.environ.pop(key, None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
