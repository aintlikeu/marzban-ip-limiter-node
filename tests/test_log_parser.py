"""
Tests for log parser functionality.

This module contains unit tests for the MarzbanLogParser class
and log parsing functionality.
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from node_agent.log_parser import MarzbanLogParser, create_log_entry


class TestMarzbanLogParser:
    """Test cases for MarzbanLogParser class."""
    
    def test_is_accepted_connection_positive(self):
        """Test detection of accepted connections."""
        accepted_lines = [
            "2024/01/15 10:30:45 [info] accepted connection from 192.168.1.100",
            "INFO: Connection accepted from client",
            "ACCEPTED connection established"
        ]
        
        for line in accepted_lines:
            assert MarzbanLogParser.is_accepted_connection(line)
    
    def test_is_accepted_connection_negative(self):
        """Test rejection of non-accepted connections."""
        rejected_lines = [
            "2024/01/15 10:30:45 [info] rejected connection from 192.168.1.100",
            "2024/01/15 10:30:45 [error] connection failed",
            "Starting server on port 8080"
        ]
        
        for line in rejected_lines:
            assert not MarzbanLogParser.is_accepted_connection(line)
    
    def test_extract_email_success(self):
        """Test successful email extraction."""
        test_cases = [
            ("email: user@example.com rest of log", "user@example.com"),
            ("some text email:test.user@domain.org more text", "test.user@domain.org"),
            ("prefix email: admin@test.co.uk suffix", "admin@test.co.uk"),
            ("email:simple@test.com,other_data", "simple@test.com")
        ]
        
        for line, expected_email in test_cases:
            result = MarzbanLogParser.extract_email(line)
            assert result == expected_email, f"Failed for line: {line}"
    
    def test_extract_email_failure(self):
        """Test email extraction failure cases."""
        no_email_lines = [
            "no email in this line",
            "email: ",  # empty email
            "text without email pattern",
            ""
        ]
        
        for line in no_email_lines:
            result = MarzbanLogParser.extract_email(line)
            assert result is None, f"Should not extract email from: {line}"
    
    def test_extract_client_ip_success(self):
        """Test successful client IP extraction."""
        test_cases = [
            ("connection from 192.168.1.100 established", "192.168.1.100"),
            ("accepted from 10.0.0.1 with auth", "10.0.0.1"),
            ("client from 172.16.255.254 connected", "172.16.255.254"),
            ("from 8.8.8.8 request received", "8.8.8.8")
        ]
        
        for line, expected_ip in test_cases:
            result = MarzbanLogParser.extract_client_ip(line)
            assert result == expected_ip, f"Failed for line: {line}"
    
    def test_extract_client_ip_failure(self):
        """Test client IP extraction failure cases."""
        no_ip_lines = [
            "no IP address in this line",
            "from invalid.ip.address",
            "from 999.999.999.999",  # invalid IP
            "connection established"
        ]
        
        for line in no_ip_lines:
            result = MarzbanLogParser.extract_client_ip(line)
            assert result is None, f"Should not extract IP from: {line}"
    
    def test_extract_timestamp_success(self):
        """Test successful timestamp extraction."""
        test_cases = [
            "2024/01/15 10:30:45 [info] log message",
            "2023/12/31 23:59:59 connection established",
            "2024/06/01 00:00:00 another message"
        ]
        
        for line in test_cases:
            result = MarzbanLogParser.extract_timestamp(line)
            assert result is not None, f"Should extract timestamp from: {line}"
            assert isinstance(result, float), "Timestamp should be a float"
            assert result > 0, "Timestamp should be positive"
    
    def test_extract_timestamp_failure(self):
        """Test timestamp extraction failure cases."""
        no_timestamp_lines = [
            "no timestamp in this line",
            "2024-01-15 10:30:45 wrong format",
            "invalid date format",
            ""
        ]
        
        for line in no_timestamp_lines:
            result = MarzbanLogParser.extract_timestamp(line)
            assert result is None, f"Should not extract timestamp from: {line}"
    
    def test_parse_log_line_complete(self):
        """Test complete log line parsing with all fields."""
        log_line = "2024/01/15 10:30:45 [info] accepted connection from 192.168.1.100 email: user@example.com auth successful"
        node_id = "test-node"
        node_name = "Test Node"
        
        result = MarzbanLogParser.parse_log_line(log_line, node_id, node_name)
        
        assert result is not None
        assert result['email'] == 'user@example.com'
        assert result['client_ip'] == '192.168.1.100'
        assert result['node_id'] == 'test-node'
        assert result['node_name'] == 'Test Node'
        assert result['raw_line'] == log_line
        assert 'timestamp' in result
        assert 'processed_at' in result
    
    def test_parse_log_line_missing_accepted(self):
        """Test parsing line without 'accepted' keyword."""
        log_line = "2024/01/15 10:30:45 [info] rejected connection from 192.168.1.100 email: user@example.com"
        
        result = MarzbanLogParser.parse_log_line(log_line, "node", "name")
        assert result is None
    
    def test_parse_log_line_missing_email(self):
        """Test parsing line without email."""
        log_line = "2024/01/15 10:30:45 [info] accepted connection from 192.168.1.100"
        
        result = MarzbanLogParser.parse_log_line(log_line, "node", "name")
        assert result is None
    
    def test_parse_log_line_missing_ip(self):
        """Test parsing line without IP address."""
        log_line = "2024/01/15 10:30:45 [info] accepted connection email: user@example.com"
        
        result = MarzbanLogParser.parse_log_line(log_line, "node", "name")
        assert result is None
    
    def test_parse_log_line_empty(self):
        """Test parsing empty or whitespace-only lines."""
        empty_lines = ["", "   ", "\n", "\t"]
        
        for line in empty_lines:
            result = MarzbanLogParser.parse_log_line(line, "node", "name")
            assert result is None
    
    def test_validate_log_entry_valid(self):
        """Test validation of valid log entry."""
        valid_entry = {
            'timestamp': 1234567890.0,
            'node_id': 'test-node',
            'node_name': 'Test Node',
            'email': 'user@example.com',
            'client_ip': '192.168.1.100',
            'raw_line': 'test log line',
            'processed_at': 1234567900.0
        }
        
        assert MarzbanLogParser.validate_log_entry(valid_entry)
    
    def test_validate_log_entry_missing_fields(self):
        """Test validation of log entry with missing fields."""
        incomplete_entries = [
            {},  # empty
            {'timestamp': 123},  # missing other fields
            {  # missing client_ip
                'timestamp': 123,
                'node_id': 'test',
                'node_name': 'test',
                'email': 'test@test.com',
                'raw_line': 'test',
                'processed_at': 123
            }
        ]
        
        for entry in incomplete_entries:
            assert not MarzbanLogParser.validate_log_entry(entry)
    
    def test_validate_log_entry_none_values(self):
        """Test validation of log entry with None values."""
        entry_with_none = {
            'timestamp': 123,
            'node_id': None,  # None value
            'node_name': 'test',
            'email': 'test@test.com',
            'client_ip': '192.168.1.1',
            'raw_line': 'test',
            'processed_at': 123
        }
        
        assert not MarzbanLogParser.validate_log_entry(entry_with_none)


class TestCreateLogEntry:
    """Test cases for create_log_entry convenience function."""
    
    def test_create_log_entry_success(self):
        """Test successful log entry creation."""
        log_line = "2024/01/15 10:30:45 [info] accepted connection from 192.168.1.100 email: user@example.com"
        
        result = create_log_entry(log_line, "test-node", "Test Node")
        
        assert result is not None
        assert result['email'] == 'user@example.com'
        assert result['client_ip'] == '192.168.1.100'
        assert result['node_id'] == 'test-node'
    
    def test_create_log_entry_failure(self):
        """Test failed log entry creation."""
        invalid_line = "invalid log line without required fields"
        
        result = create_log_entry(invalid_line, "test-node", "Test Node")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
