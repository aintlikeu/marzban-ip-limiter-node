# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-06-16

### Added
- Initial release of Marzban Node Agent
- Real-time log monitoring and forwarding
- Redis-based centralized log collection
- Docker containerization support
- Comprehensive configuration system
- Built-in health checks and monitoring
- Automatic retry and recovery mechanisms
- Position tracking for log file recovery
- Batch processing for optimal performance
- Detailed documentation and installation guides
- Systemd service integration
- Security features and non-privileged execution

### Features
- **Log Parsing**: Intelligent parsing of Marzban access logs
- **Buffering**: Configurable batching for efficient data transfer
- **Retry Logic**: Exponential backoff for failed Redis operations
- **Position Recovery**: Automatic recovery from last processed position
- **Health Monitoring**: Built-in health checks and diagnostics
- **Docker Support**: Ready-to-use Docker images and compose files
- **Installation Scripts**: Automated installation and setup scripts

### Documentation
- Complete installation guide
- Configuration reference
- Troubleshooting documentation
- API reference for developers
- Example configurations for different scenarios

### Testing
- Comprehensive unit test suite
- Integration tests for Redis connectivity
- Log parsing validation tests
- Configuration validation tests

### Security
- Non-privileged container execution
- Secure configuration file handling
- Redis authentication support
- SSL/TLS connection support
