#!/bin/bash

# =============================================================================
# Marzban Node Agent Health Check Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_DIR="/opt/marzban-node-agent"
SERVICE_NAME="marzban-node-agent"
CONTAINER_NAME="marzban-node-agent"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check Docker service
check_docker() {
    print_status "Checking Docker service..."
    
    if ! systemctl is-active --quiet docker; then
        print_error "Docker service is not running"
        return 1
    fi
    
    print_success "Docker service is running"
    return 0
}

# Function to check container status
check_container() {
    print_status "Checking container status..."
    
    cd "$AGENT_DIR" 2>/dev/null || {
        print_error "Agent directory not found: $AGENT_DIR"
        return 1
    }
    
    # Check if container exists and is running
    if docker-compose -f docker/docker-compose.yml ps | grep -q "Up"; then
        print_success "Container is running"
        
        # Get container stats
        local container_id=$(docker ps -qf "name=$CONTAINER_NAME")
        if [ -n "$container_id" ]; then
            local stats=$(docker stats --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}" "$container_id" | tail -1)
            print_status "Resource usage: $stats"
        fi
        return 0
    else
        print_error "Container is not running"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis() {
    print_status "Checking Redis connectivity..."
    
    local result=$(docker-compose -f "$AGENT_DIR/docker/docker-compose.yml" exec -T node-agent python -c "
import sys
sys.path.append('/app/src')
try:
    from node_agent.config import ConfigService
    import redis.asyncio as redis
    import asyncio
    
    async def test():
        config = ConfigService.load_from_env()
        client = redis.from_url(config.central_redis_url)
        try:
            await client.ping()
            return True
        except Exception as e:
            print(f'Error: {e}', file=sys.stderr)
            return False
        finally:
            await client.close()
    
    result = asyncio.run(test())
    print('OK' if result else 'FAIL')
except Exception as e:
    print(f'FAIL: {e}', file=sys.stderr)
" 2>/dev/null)
    
    if echo "$result" | grep -q "OK"; then
        print_success "Redis connection is healthy"
        return 0
    else
        print_error "Redis connection failed"
        echo "$result" | grep -v "OK" | sed 's/^/  /'
        return 1
    fi
}

# Function to check log file access
check_log_file() {
    print_status "Checking access log file..."
    
    local log_result=$(docker-compose -f "$AGENT_DIR/docker/docker-compose.yml" exec -T node-agent python -c "
import sys
sys.path.append('/app/src')
import os
from node_agent.config import ConfigService

try:
    config = ConfigService.load_from_env()
    log_path = config.access_log_path
    
    if os.path.exists(log_path):
        if os.access(log_path, os.R_OK):
            stat = os.stat(log_path)
            print(f'OK:{stat.st_size}')
        else:
            print('FAIL:Not readable')
    else:
        print('FAIL:File not found')
except Exception as e:
    print(f'FAIL:{e}')
" 2>/dev/null)
    
    if echo "$log_result" | grep -q "OK:"; then
        local file_size=$(echo "$log_result" | cut -d: -f2)
        print_success "Access log file is readable (size: $file_size bytes)"
        return 0
    else
        local error=$(echo "$log_result" | cut -d: -f2)
        print_error "Access log file issue: $error"
        return 1
    fi
}

# Function to get agent metrics
get_metrics() {
    print_status "Getting agent metrics..."
    
    local metrics=$(docker-compose -f "$AGENT_DIR/docker/docker-compose.yml" exec -T node-agent python -c "
import sys
sys.path.append('/app/src')
import json
try:
    from node_agent.config import ConfigService
    config = ConfigService.load_from_env()
    
    print(json.dumps({
        'node_id': config.node_id,
        'node_name': config.node_name,
        'batch_size': config.batch_size,
        'flush_interval': config.flush_interval,
        'log_level': config.log_level
    }))
except Exception as e:
    print(f'{{\"error\": \"{e}\"}}')
" 2>/dev/null)
    
    if echo "$metrics" | python3 -m json.tool >/dev/null 2>&1; then
        print_success "Agent configuration:"
        echo "$metrics" | python3 -m json.tool | sed 's/^/  /'
    else
        print_warning "Could not retrieve agent metrics"
    fi
}

# Function to check recent logs
check_recent_logs() {
    print_status "Checking recent logs (last 10 lines)..."
    
    echo "--- Container Logs ---"
    docker-compose -f "$AGENT_DIR/docker/docker-compose.yml" logs --tail=10 node-agent 2>/dev/null | sed 's/^/  /'
    echo
}

# Function to check systemd service
check_systemd() {
    print_status "Checking systemd service..."
    
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            print_success "Systemd service is enabled and active"
        else
            print_warning "Systemd service is enabled but not active"
        fi
    else
        print_warning "Systemd service is not enabled"
    fi
}

# Function to check disk space
check_disk_space() {
    print_status "Checking disk space..."
    
    local disk_usage=$(df -h "$AGENT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -lt 80 ]; then
        print_success "Disk usage: ${disk_usage}%"
    elif [ "$disk_usage" -lt 90 ]; then
        print_warning "Disk usage: ${disk_usage}% (getting high)"
    else
        print_error "Disk usage: ${disk_usage}% (critically high)"
    fi
}

# Main health check function
main() {
    echo "=============================================="
    echo "Marzban Node Agent Health Check"
    echo "=============================================="
    echo
    
    local overall_status=0
    
    # Run all checks
    check_docker || overall_status=1
    echo
    
    check_container || overall_status=1
    echo
    
    check_redis || overall_status=1
    echo
    
    check_log_file || overall_status=1
    echo
    
    get_metrics
    echo
    
    check_systemd
    echo
    
    check_disk_space
    echo
    
    check_recent_logs
    
    echo "=============================================="
    if [ $overall_status -eq 0 ]; then
        print_success "Overall health check: PASSED"
    else
        print_error "Overall health check: FAILED"
        echo
        echo "Troubleshooting steps:"
        echo "1. Check logs: docker-compose -f $AGENT_DIR/docker/docker-compose.yml logs"
        echo "2. Restart service: systemctl restart $SERVICE_NAME"
        echo "3. Check configuration: $AGENT_DIR/config/.env"
        echo "4. Verify Redis connectivity manually"
    fi
    echo "=============================================="
    
    exit $overall_status
}

# Handle command line arguments
case "${1:-}" in
    --quiet|-q)
        # Quiet mode - only show errors
        exec 1>/dev/null
        main
        ;;
    --json)
        # JSON output mode (for monitoring systems)
        exec > >(python3 -c "
import sys, json
lines = sys.stdin.read().strip().split('\n')
result = {'status': 'unknown', 'checks': []}
for line in lines:
    if '[OK]' in line:
        result['checks'].append({'name': line.split('[OK]')[1].strip(), 'status': 'ok'})
    elif '[ERROR]' in line:
        result['checks'].append({'name': line.split('[ERROR]')[1].strip(), 'status': 'error'})
    elif '[WARNING]' in line:
        result['checks'].append({'name': line.split('[WARNING]')[1].strip(), 'status': 'warning'})

if any(c['status'] == 'error' for c in result['checks']):
    result['status'] = 'error'
elif any(c['status'] == 'warning' for c in result['checks']):
    result['status'] = 'warning' 
else:
    result['status'] = 'ok'
    
print(json.dumps(result, indent=2))
")
        main
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo "Options:"
        echo "  --quiet, -q    Quiet mode (only show errors)"
        echo "  --json         JSON output mode"
        echo "  --help, -h     Show this help message"
        ;;
    *)
        main
        ;;
esac
