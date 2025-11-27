#!/bin/bash

# DND_DC_BOT Docker Deployment Script
# Manages the lifecycle of the Discord bot container

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo ""
        echo "Please install Docker first:"
        echo "  macOS: https://docs.docker.com/desktop/install/mac-install/"
        echo "  Linux: https://docs.docker.com/engine/install/"
        echo "  Windows: https://docs.docker.com/desktop/install/windows-install/"
        exit 1
    fi
}

# Function to check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        echo ""
        echo "Please install Docker Compose:"
        echo "  https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_error ".env file not found"
        echo ""
        echo "Please create a .env file with your configuration:"
        echo "  1. Copy the example file: cp docker.env.example .env"
        echo "  2. Edit .env and add your Discord token and API keys"
        echo ""
        echo "Required variables:"
        echo "  - DISCORD_TOKEN: Your Discord bot token"
        echo "  - GEMINI_API_KEY: Your Google Gemini API key (optional)"
        exit 1
    fi
}

# Function to get docker-compose command
get_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo "docker compose"
    fi
}

# Function to deploy the bot (default action)
deploy() {
    print_info "Starting deployment..."
    echo ""
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    print_info "Building Docker image..."
    if $COMPOSE_CMD build; then
        print_success "Image built successfully"
    else
        print_error "Failed to build image"
        exit 1
    fi
    
    echo ""
    print_info "Starting container..."
    if $COMPOSE_CMD up -d; then
        print_success "Container started successfully"
        echo ""
        print_info "Bot is now running in detached mode"
        print_info "Use './deploy-docker.sh --logs' to view logs"
        print_info "Use './deploy-docker.sh --status' to check status"
    else
        print_error "Failed to start container"
        exit 1
    fi
}

# Function to show container status
show_status() {
    print_info "Container status:"
    echo ""
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD ps
}

# Function to show container logs
show_logs() {
    print_info "Showing container logs (Ctrl+C to exit)..."
    echo ""
    
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD logs -f
}

# Function to restart the container
restart_container() {
    print_info "Restarting container..."
    echo ""
    
    COMPOSE_CMD=$(get_compose_cmd)
    if $COMPOSE_CMD restart; then
        print_success "Container restarted successfully"
    else
        print_error "Failed to restart container"
        exit 1
    fi
}

# Function to stop the container
stop_container() {
    print_info "Stopping container..."
    echo ""
    
    COMPOSE_CMD=$(get_compose_cmd)
    if $COMPOSE_CMD down; then
        print_success "Container stopped and removed"
    else
        print_error "Failed to stop container"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "DND_DC_BOT Docker Deployment Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  (no args)    Deploy the bot (build and start in detached mode)"
    echo "  --status     Show container status"
    echo "  --logs       Show and follow container logs"
    echo "  --restart    Restart the container"
    echo "  --down       Stop and remove the container"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy the bot"
    echo "  $0 --status           # Check if bot is running"
    echo "  $0 --logs             # View bot logs"
    echo "  $0 --restart          # Restart the bot"
    echo "  $0 --down             # Stop the bot"
}

# Main script logic
main() {
    # Check prerequisites
    check_docker
    check_docker_compose
    
    # Parse command line arguments
    case "${1:-}" in
        "")
            # Default action: deploy
            check_env_file
            deploy
            ;;
        --status)
            show_status
            ;;
        --logs)
            show_logs
            ;;
        --restart)
            restart_container
            ;;
        --down)
            stop_container
            ;;
        --help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown option: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
