#!/bin/bash

# =============================================================================
# Marzban Node Agent Configuration Setup Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to validate Redis URL format
validate_redis_url() {
    local url="$1"
    if [[ ! $url =~ ^redis(s)?://.*:[0-9]+/[0-9]+$ ]]; then
        return 1
    fi
    return 0
}

# Function to test Redis connection
test_redis_connection() {
    local redis_url="$1"
    print_status "Testing Redis connection..."
    
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli -u "$redis_url" ping >/dev/null 2>&1; then
            print_success "Redis connection test passed"
            return 0
        else
            print_warning "Redis connection test failed"
            return 1
        fi
    else
        print_warning "redis-cli not available, skipping connection test"
        return 0
    fi
}

# Main configuration function
main() {
    echo "=============================================="
    echo "Marzban Node Agent Configuration Setup"
    echo "=============================================="
    echo
    
    # Check if config directory exists
    CONFIG_DIR="${1:-./config}"
    if [ ! -d "$CONFIG_DIR" ]; then
        print_error "Config directory not found: $CONFIG_DIR"
        exit 1
    fi
    
    ENV_FILE="$CONFIG_DIR/.env"
    
    # Check if .env already exists
    if [ -f "$ENV_FILE" ]; then
        print_warning ".env file already exists"
        read -p "Do you want to overwrite it? (y/N): " confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            print_status "Configuration cancelled"
            exit 0
        fi
    fi
    
    # Get user input
    echo "Please provide the following information:"
    echo
    
    # Node ID
    while true; do
        read -p "Node ID (unique identifier, e.g., germany-01): " NODE_ID
        if [[ -n "$NODE_ID" && "$NODE_ID" =~ ^[a-zA-Z0-9-]+$ ]]; then
            break
        else
            print_error "Invalid Node ID. Use only letters, numbers, and hyphens."
        fi
    done
    
    # Node Name
    read -p "Node Name (human readable, e.g., Germany Frankfurt 01): " NODE_NAME
    if [ -z "$NODE_NAME" ]; then
        NODE_NAME="$NODE_ID"
    fi
    
    # Redis URL
    while true; do
        read -p "Central Redis URL (e.g., redis://server:6379/0): " REDIS_URL
        if validate_redis_url "$REDIS_URL"; then
            break
        else
            print_error "Invalid Redis URL format. Use: redis://host:port/db"
        fi
    done
    
    # Access log path
    read -p "Marzban access log path [/var/lib/marzban-node/access.log]: " LOG_PATH
    LOG_PATH="${LOG_PATH:-/var/lib/marzban-node/access.log}"
    
    # Advanced settings
    echo
    read -p "Configure advanced settings? (y/N): " advanced
    if [[ $advanced =~ ^[Yy]$ ]]; then
        read -p "Batch size [50]: " BATCH_SIZE
        BATCH_SIZE="${BATCH_SIZE:-50}"
        
        read -p "Flush interval in seconds [3.0]: " FLUSH_INTERVAL
        FLUSH_INTERVAL="${FLUSH_INTERVAL:-3.0}"
        
        read -p "Log level (DEBUG/INFO/WARNING/ERROR) [INFO]: " LOG_LEVEL
        LOG_LEVEL="${LOG_LEVEL:-INFO}"
    else
        BATCH_SIZE=50
        FLUSH_INTERVAL=3.0
        LOG_LEVEL=INFO
    fi
    
    # Test Redis connection if possible
    test_redis_connection "$REDIS_URL" || true
    
    # Create .env file
    print_status "Creating configuration file..."
    
    cat > "$ENV_FILE" << EOF
# =============================================================================
# Marzban Node Agent Configuration
# Generated on $(date)
# =============================================================================

# Node identification (REQUIRED)
NODE_ID=$NODE_ID
NODE_NAME=$NODE_NAME

# Central Redis server connection (REQUIRED)
CENTRAL_REDIS_URL=$REDIS_URL

# Path to Marzban access log file (REQUIRED)
ACCESS_LOG_PATH=$LOG_PATH

# Batching and performance settings
BATCH_SIZE=$BATCH_SIZE
FLUSH_INTERVAL=$FLUSH_INTERVAL

# Retry and reliability settings  
MAX_RETRIES=5
RETRY_DELAY=2.0

# Logging configuration
LOG_LEVEL=$LOG_LEVEL
EOF
    
    print_success "Configuration file created: $ENV_FILE"
    echo
    print_status "Configuration summary:"
    echo "  Node ID: $NODE_ID"
    echo "  Node Name: $NODE_NAME"
    echo "  Redis URL: $REDIS_URL"
    echo "  Log Path: $LOG_PATH"
    echo "  Batch Size: $BATCH_SIZE"
    echo "  Log Level: $LOG_LEVEL"
    echo
    print_success "You can now start the agent with:"
    echo "  sudo systemctl start marzban-node-agent"
    echo "  or"
    echo "  docker-compose -f docker/docker-compose.standalone.yml up -d"
}

# Run main function
main "$@"
