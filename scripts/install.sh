#!/bin/bash

# =============================================================================
# Marzban Node Agent Installation Script
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_DIR="/opt/marzban-node-agent"
CONFIG_DIR="$AGENT_DIR/config"
SERVICE_NAME="marzban-node-agent"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check for Docker
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check for docker-compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker service."
        exit 1
    fi
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run this script as root or with sudo"
        exit 1
    fi
    
    print_success "System requirements check passed"
}

# Function to create directories
create_directories() {
    print_status "Creating directories..."
    
    mkdir -p "$AGENT_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "/var/log/$SERVICE_NAME"
    
    print_success "Directories created"
}

# Function to copy files
copy_files() {
    print_status "Copying application files..."
    
    # Copy source code
    cp -r src/ "$AGENT_DIR/"
    cp -r docker/ "$AGENT_DIR/"
    cp -r scripts/ "$AGENT_DIR/"
    
    # Copy configuration files
    cp config/requirements.txt "$CONFIG_DIR/"
    cp config/.env.example "$CONFIG_DIR/"
    
    # Create default .env if it doesn't exist
    if [ ! -f "$CONFIG_DIR/.env" ]; then
        cp "$CONFIG_DIR/.env.example" "$CONFIG_DIR/.env"
        print_warning "Created default .env file. Please edit $CONFIG_DIR/.env with your configuration."
    fi
    
    print_success "Files copied successfully"
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image..."
    
    cd "$AGENT_DIR"
    docker build -t marzban-node-agent:latest -f docker/Dockerfile .
    
    print_success "Docker image built successfully"
}

# Function to configure systemd service
configure_service() {
    print_status "Configuring systemd service..."
    
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Marzban Node Agent
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$AGENT_DIR
ExecStart=/usr/bin/docker-compose -f docker/docker-compose.yml up -d
ExecStop=/usr/bin/docker-compose -f docker/docker-compose.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    print_success "Systemd service configured"
}

# Function to start service
start_service() {
    print_status "Starting Marzban Node Agent..."
    
    cd "$AGENT_DIR"
    
    # Start with docker-compose
    docker-compose -f docker/docker-compose.yml up -d
    
    # Wait for container to start
    sleep 5
    
    # Check status
    if docker-compose -f docker/docker-compose.yml ps | grep -q "Up"; then
        print_success "Marzban Node Agent started successfully"
    else
        print_error "Failed to start Marzban Node Agent"
        print_status "Checking logs..."
        docker-compose -f docker/docker-compose.yml logs
        exit 1
    fi
}

# Function to run installation health check
health_check() {
    print_status "Running health check..."
    
    cd "$AGENT_DIR"
    
    # Check container status
    if ! docker-compose -f docker/docker-compose.yml ps | grep -q "Up"; then
        print_error "Container is not running"
        return 1
    fi
    
    # Check Redis connectivity (if possible)
    if docker-compose -f docker/docker-compose.yml exec -T node-agent python -c "
import sys
sys.path.append('/app/src')
from node_agent.config import ConfigService
import redis.asyncio as redis
import asyncio

async def test():
    config = ConfigService.load_from_env()
    client = redis.from_url(config.central_redis_url)
    try:
        await client.ping()
        print('Redis connection successful')
        return True
    except Exception as e:
        print(f'Redis connection failed: {e}')
        return False
    finally:
        await client.close()

print('OK' if asyncio.run(test()) else 'FAIL')
" 2>/dev/null | grep -q "OK"; then
        print_success "Redis connectivity check passed"
    else
        print_warning "Redis connectivity check failed - please verify Redis configuration"
    fi
    
    print_success "Health check completed"
}

# Main installation function
main() {
    echo "=============================================="
    echo "Marzban Node Agent Installation Script"
    echo "=============================================="
    echo
    
    check_requirements
    create_directories
    copy_files
    build_image
    configure_service
    start_service
    health_check
    
    echo
    echo "=============================================="
    print_success "Installation completed successfully!"
    echo "=============================================="
    echo
    echo "Next steps:"
    echo "1. Edit configuration: $CONFIG_DIR/.env"
    echo "2. Restart service: systemctl restart $SERVICE_NAME"
    echo "3. Check status: systemctl status $SERVICE_NAME"
    echo "4. View logs: docker-compose -f $AGENT_DIR/docker/docker-compose.yml logs -f"
    echo
    echo "For more information, see the documentation in docs/"
}

# Run main function
main "$@"
