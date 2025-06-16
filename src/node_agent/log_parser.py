"""
Log parser module for Marzban access logs.

This module provides functionality to parse Marzban access log entries
and extract relevant information for forwarding to the central server.
"""

import re
import time
from typing import Optional, Dict, Any
from datetime import datetime


class MarzbanLogParser:
    """Parser for Marzban access log entries."""
    
    # Regex patterns for extracting information from log lines
    EMAIL_PATTERN = re.compile(r'email:\s*([^\s,]+)')
    CLIENT_IP_PATTERN = re.compile(r'from\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')
    TIMESTAMP_PATTERN = re.compile(r'^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})')
    
    @staticmethod
    def is_accepted_connection(line: str) -> bool:
        """
        Check if log line contains an 'accepted' connection.
        
        Args:
            line: Raw log line from access.log
            
        Returns:
            True if line contains accepted connection info
        """
        return 'accepted' in line.lower()
    
    @staticmethod
    def extract_email(line: str) -> Optional[str]:
        """
        Extract email from log line using regex.
        
        Args:
            line: Raw log line from access.log
            
        Returns:
            Extracted email or None if not found
        """
        match = MarzbanLogParser.EMAIL_PATTERN.search(line)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_client_ip(line: str) -> Optional[str]:
        """
        Extract client IP from log line using regex.
        
        Args:
            line: Raw log line from access.log
            
        Returns:
            Extracted client IP or None if not found
        """
        match = MarzbanLogParser.CLIENT_IP_PATTERN.search(line)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_timestamp(line: str) -> Optional[float]:
        """
        Extract timestamp from log line and convert to Unix timestamp.
        
        Args:
            line: Raw log line from access.log
            
        Returns:
            Unix timestamp or None if not found
        """
        match = MarzbanLogParser.TIMESTAMP_PATTERN.search(line)
        if not match:
            return None
        
        try:
            # Parse timestamp format: 2024/01/15 10:30:45
            dt = datetime.strptime(match.group(1), "%Y/%m/%d %H:%M:%S")
            return dt.timestamp()
        except ValueError:
            return None
    
    @staticmethod
    def parse_log_line(
        line: str, 
        node_id: str, 
        node_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a single log line and create structured log object.
        
        Args:
            line: Raw log line from access.log
            node_id: Unique identifier for the node
            node_name: Human-readable name for the node
            
        Returns:
            Structured log object or None if line doesn't contain useful info
        """
        # Skip empty lines or lines without accepted connections
        line = line.strip()
        if not line or not MarzbanLogParser.is_accepted_connection(line):
            return None
        
        # Extract information from log line
        email = MarzbanLogParser.extract_email(line)
        client_ip = MarzbanLogParser.extract_client_ip(line)
        log_timestamp = MarzbanLogParser.extract_timestamp(line)
        
        # Skip if we couldn't extract essential information
        if not email or not client_ip:
            return None
        
        # Create structured log object
        return {
            'timestamp': log_timestamp or time.time(),
            'node_id': node_id,
            'node_name': node_name,
            'email': email,
            'client_ip': client_ip,
            'raw_line': line,
            'processed_at': time.time()
        }
    
    @staticmethod
    def validate_log_entry(log_entry: Dict[str, Any]) -> bool:
        """
        Validate that log entry contains all required fields.
        
        Args:
            log_entry: Structured log object
            
        Returns:
            True if log entry is valid
        """
        required_fields = [
            'timestamp', 'node_id', 'node_name', 
            'email', 'client_ip', 'raw_line', 'processed_at'
        ]
        
        return all(
            field in log_entry and log_entry[field] is not None 
            for field in required_fields
        )


def create_log_entry(
    line: str, 
    node_id: str, 
    node_name: str
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to create a log entry from a raw line.
    
    Args:
        line: Raw log line from access.log
        node_id: Unique identifier for the node
        node_name: Human-readable name for the node
        
    Returns:
        Structured log object or None if line doesn't contain useful info
    """
    return MarzbanLogParser.parse_log_line(line, node_id, node_name)
