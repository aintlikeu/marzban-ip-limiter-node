#!/bin/bash

# =============================================================================
# Marzban Node Agent Uninstall Script
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
CONTAINER_NAME="marzban-node-agent"

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

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run this script as root or with sudo"
        exit 1
    fi
}

# Function to confirm uninstallation
confirm_uninstall() {
    echo "=============================================="
    echo "Marzban Node Agent Uninstall Script"
    echo "=============================================="
    echo
    print_warning "This will completely remove Marzban Node Agent from your system:"
    echo "  - Stop and remove the service"
    echo "  - Remove Docker containers and images"
    echo "  - Delete all files and configuration"
    echo "  - Remove systemd service"
    echo
    
    read -p "Are you sure you want to continue? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_status "Uninstallation cancelled"
        exit 0
    fi
    echo
}

# Function to stop service
stop_service() {
    print_status "Stopping Marzban Node Agent service..."
    
    # Stop systemd service if exists
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        systemctl stop "$SERVICE_NAME"
        print_success "Systemd service stopped"
    else
        print_warning "Systemd service was not running"
    fi
    
    # Stop Docker containers if running
    if [ -d "$AGENT_DIR" ]; then
        cd "$AGENT_DIR" 2>/dev/null || true
        
        # Try both compose files
        if [ -f "docker/docker-compose.standalone.yml" ]; then
            docker-compose -f docker/docker-compose.standalone.yml down 2>/dev/null || true
            print_success "Standalone Docker containers stopped"
        fi
        
        if [ -f "docker/docker-compose.yml" ]; then
            docker-compose -f docker/docker-compose.yml down 2>/dev/null || true
            print_success "Main Docker containers stopped"
        fi
    fi
    
    # Force stop container if still running
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
        print_success "Force stopped and removed container"
    fi
}

# Function to remove systemd service
remove_systemd_service() {
    print_status "Removing systemd service..."
    
    # Disable service
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        systemctl disable "$SERVICE_NAME"
        print_success "Service disabled"
    fi
    
    # Remove service file
    if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        print_success "Service file removed"
    fi
    
    # Remove environment file if exists
    if [ -f "/etc/systemd/system/$SERVICE_NAME.service.d/environment.conf" ]; then
        rm -rf "/etc/systemd/system/$SERVICE_NAME.service.d"
        print_success "Environment file removed"
    fi
    
    # Reload systemd
    systemctl daemon-reload
    systemctl reset-failed 2>/dev/null || true
    print_success "Systemd configuration reloaded"
}

# Function to remove Docker images
remove_docker_images() {
    print_status "Removing Docker images..."
    
    # Remove custom built images
    if docker images -q marzban-node-agent 2>/dev/null | grep -q .; then
        docker rmi $(docker images -q marzban-node-agent) 2>/dev/null || true
        print_success "Custom Docker images removed"
    fi
    
    # Clean up unused images (optional)
    read -p "Remove unused Docker images and volumes? (y/N): " cleanup
    if [[ $cleanup =~ ^[Yy]$ ]]; then
        docker system prune -af --volumes 2>/dev/null || true
        print_success "Docker cleanup completed"
    fi
}

# Function to remove files
remove_files() {
    print_status "Removing application files..."
    
    # Backup configuration if requested
    if [ -f "$CONFIG_DIR/.env" ]; then
        read -p "Backup configuration files? (Y/n): " backup
        if [[ ! $backup =~ ^[Nn]$ ]]; then
            backup_dir="/tmp/marzban-node-agent-backup-$(date +%Y%m%d_%H%M%S)"
            mkdir -p "$backup_dir"
            cp -r "$CONFIG_DIR" "$backup_dir/" 2>/dev/null || true
            print_success "Configuration backed up to: $backup_dir"
        fi
    fi
    
    # Remove main directory
    if [ -d "$AGENT_DIR" ]; then
        rm -rf "$AGENT_DIR"
        print_success "Application directory removed: $AGENT_DIR"
    fi
    
    # Remove log directory
    if [ -d "/var/log/$SERVICE_NAME" ]; then
        rm -rf "/var/log/$SERVICE_NAME"
        print_success "Log directory removed"
    fi
    
    # Remove symbolic links
    if [ -L "/usr/local/bin/marzban-health" ]; then
        rm -f "/usr/local/bin/marzban-health"
        print_success "Health check symlink removed"
    fi
    
    if [ -L "/usr/local/bin/marzban-install" ]; then
        rm -f "/usr/local/bin/marzban-install"
        print_success "Install script symlink removed"
    fi
}

# Function to remove cron jobs
remove_cron_jobs() {
    print_status "Removing cron jobs..."
    
    # Remove health check cron jobs
    if crontab -l 2>/dev/null | grep -q "marzban-node-agent"; then
        # Create temporary crontab without marzban-node-agent entries
        crontab -l 2>/dev/null | grep -v "marzban-node-agent" | crontab -
        print_success "Cron jobs removed"
    else
        print_warning "No cron jobs found"
    fi
    
    # Remove system-wide cron entries
    if [ -f "/etc/crontab" ] && grep -q "marzban-node-agent" "/etc/crontab"; then
        sed -i '/marzban-node-agent/d' /etc/crontab
        print_success "System cron entries removed"
    fi
}

# Function to remove logrotate configuration
remove_logrotate() {
    print_status "Removing logrotate configuration..."
    
    if [ -f "/etc/logrotate.d/marzban-node-agent" ]; then
        rm -f "/etc/logrotate.d/marzban-node-agent"
        print_success "Logrotate configuration removed"
    else
        print_warning "No logrotate configuration found"
    fi
}

# Function to remove Docker networks
remove_docker_networks() {
    print_status "Cleaning up Docker networks..."
    
    # Remove marzban-network if not used by other containers
    if docker network ls --format "{{.Name}}" | grep -q "^marzban-network$"; then
        # Check if network is in use
        if [ "$(docker network inspect marzban-network --format='{{len .Containers}}')" = "0" ]; then
            docker network rm marzban-network 2>/dev/null || true
            print_success "Docker network removed"
        else
            print_warning "Docker network in use by other containers, keeping it"
        fi
    fi
}

# Function to clean up user and groups
cleanup_user() {
    print_status "Cleaning up user accounts..."
    
    # Remove marzban-agent user if exists
    if id "marzban-agent" >/dev/null 2>&1; then
        userdel marzban-agent 2>/dev/null || true
        print_success "User 'marzban-agent' removed"
    fi
    
    # Remove group if exists and empty
    if getent group marzban-agent >/dev/null 2>&1; then
        groupdel marzban-agent 2>/dev/null || true
        print_success "Group 'marzban-agent' removed"
    fi
}

# Function to show final status
show_final_status() {
    echo
    echo "=============================================="
    print_success "Uninstallation completed successfully!"
    echo "=============================================="
    echo
    print_status "What was removed:"
    echo "  ✅ Systemd service and configuration"
    echo "  ✅ Docker containers and images"
    echo "  ✅ Application files and directories"
    echo "  ✅ Log files and configuration"
    echo "  ✅ Cron jobs and logrotate rules"
    echo "  ✅ Symbolic links and user accounts"
    echo
    
    # Check for any remaining traces
    print_status "Checking for remaining traces..."
    
    remaining_found=false
    
    # Check for running containers
    if docker ps -a --format "{{.Names}}" | grep -q "marzban-node-agent"; then
        print_warning "Some containers may still exist"
        remaining_found=true
    fi
    
    # Check for images
    if docker images --format "{{.Repository}}" | grep -q "marzban-node-agent"; then
        print_warning "Some Docker images may still exist"
        remaining_found=true
    fi
    
    # Check for processes
    if pgrep -f "marzban-node-agent" >/dev/null 2>&1; then
        print_warning "Some processes may still be running"
        remaining_found=true
    fi
    
    if [ "$remaining_found" = false ]; then
        print_success "No remaining traces found"
    else
        echo
        print_status "To manually clean up any remaining traces:"
        echo "  docker system prune -af --volumes"
        echo "  pkill -f marzban-node-agent"
    fi
    
    echo
    print_status "Thank you for using Marzban Node Agent!"
}

# Function to handle errors
handle_error() {
    local exit_code=$?
    echo
    print_error "An error occurred during uninstallation (exit code: $exit_code)"
    print_status "You may need to manually clean up some components"
    exit $exit_code
}

# Main uninstallation function
main() {
    # Set error handler
    trap handle_error ERR
    
    check_root
    confirm_uninstall
    
    print_status "Starting uninstallation process..."
    echo
    
    # Perform uninstallation steps
    stop_service
    echo
    
    remove_systemd_service
    echo
    
    remove_docker_images
    echo
    
    remove_files
    echo
    
    remove_cron_jobs
    echo
    
    remove_logrotate
    echo
    
    remove_docker_networks
    echo
    
    cleanup_user
    echo
    
    show_final_status
}

# Handle command line arguments
case "${1:-}" in
    --force|-f)
        # Force uninstall without confirmation
        print_warning "Force uninstall mode enabled"
        confirm_uninstall() { echo "Force mode: skipping confirmation"; }
        main
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo "Options:"
        echo "  --force, -f    Force uninstall without confirmation"
        echo "  --help, -h     Show this help message"
        echo ""
        echo "This script will completely remove Marzban Node Agent from your system."
        ;;
    *)
        main "$@"
        ;;
esac
