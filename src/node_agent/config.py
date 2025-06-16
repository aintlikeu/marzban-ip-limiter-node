"""
Configuration module for Marzban Node Agent.

This module provides configuration management for the log forwarding agent,
including environment variable loading and validation.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class NodeConfig:
    """Configuration class for Node Agent."""
    
    node_id: str
    node_name: str
    central_redis_url: str
    access_log_path: str
    batch_size: int = 50
    flush_interval: float = 3.0
    max_retries: int = 5
    retry_delay: float = 2.0
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.node_id:
            raise ValueError("NODE_ID is required")
        if not self.node_name:
            raise ValueError("NODE_NAME is required")
        if not self.central_redis_url:
            raise ValueError("CENTRAL_REDIS_URL is required")
        if not self.access_log_path:
            raise ValueError("ACCESS_LOG_PATH is required")
        
        if self.batch_size <= 0:
            raise ValueError("BATCH_SIZE must be positive")
        if self.flush_interval <= 0:
            raise ValueError("FLUSH_INTERVAL must be positive")
        if self.max_retries < 0:
            raise ValueError("MAX_RETRIES must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("RETRY_DELAY must be non-negative")
        
        # Normalize log level
        self.log_level = self.log_level.upper()
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid LOG_LEVEL: {self.log_level}")


class ConfigService:
    """Service for loading configuration from environment variables."""
    
    @staticmethod
    def load_from_env(env_file: Optional[str] = None) -> NodeConfig:
        """
        Load configuration from environment variables.
        
        Args:
            env_file: Optional path to .env file
            
        Returns:
            NodeConfig instance with loaded configuration
            
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        return NodeConfig(
            node_id=os.getenv("NODE_ID", "").strip(),
            node_name=os.getenv("NODE_NAME", "").strip(),
            central_redis_url=os.getenv("CENTRAL_REDIS_URL", "").strip(),
            access_log_path=os.getenv("ACCESS_LOG_PATH", "/var/lib/marzban-node/access.log").strip(),
            batch_size=int(os.getenv("BATCH_SIZE", "50")),
            flush_interval=float(os.getenv("FLUSH_INTERVAL", "3.0")),
            max_retries=int(os.getenv("MAX_RETRIES", "5")),
            retry_delay=float(os.getenv("RETRY_DELAY", "2.0")),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip(),
        )
    
    @staticmethod
    def get_redis_position_key(node_id: str) -> str:
        """
        Get Redis key for storing log file position.
        
        Args:
            node_id: Unique identifier for the node
            
        Returns:
            Redis key for position storage
        """
        return f"node_agent:{node_id}:position"
    
    @staticmethod
    def get_redis_queue_key() -> str:
        """
        Get Redis key for the log queue.
        
        Returns:
            Redis key for log queue
        """
        return "node_logs_queue"
