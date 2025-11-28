#!/bin/bash
#
# DeceptiCloud Enhanced Deception Deployment Script
#
# This script deploys the enhanced deception system either locally or on AWS.
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║   DeceptiCloud Enhanced Deception Deployment            ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    echo -e "\n${BLUE}[1/5] Checking prerequisites...${NC}"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker found: $(docker --version | cut -d' ' -f3)"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose found: $(docker-compose --version | cut -d' ' -f4)"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    print_success "Python found: $(python3 --version | cut -d' ' -f2)"
}

# Create necessary directories
create_directories() {
    echo -e "\n${BLUE}[2/5] Creating directories...${NC}"

    cd "$PROJECT_ROOT"

    mkdir -p data/deception
    mkdir -p data/cowrie/logs
    mkdir -p data/cowrie/downloads
    mkdir -p data/cowrie/etc
    mkdir -p data/nginx/logs
    mkdir -p data/nginx/content
    mkdir -p results
    mkdir -p models

    print_success "Directories created"
}

# Install Python dependencies
install_dependencies() {
    echo -e "\n${BLUE}[3/5] Installing Python dependencies...${NC}"

    cd "$PROJECT_ROOT"

    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_info "No requirements.txt found, skipping"
    fi
}

# Build and start services
deploy_local() {
    echo -e "\n${BLUE}[4/5] Deploying local services with deception...${NC}"

    cd "$PROJECT_ROOT"

    # Build deception service
    print_info "Building deception service..."
    docker-compose -f docker-compose.local.yml build deception

    # Start all services
    print_info "Starting honeypots and deception service..."
    docker-compose -f docker-compose.local.yml up -d

    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 10

    # Check service status
    if docker ps | grep -q "cowrie_honeypot_local"; then
        print_success "Cowrie honeypot is running"
    else
        print_error "Cowrie honeypot failed to start"
    fi

    if docker ps | grep -q "nginx_honeypot_local"; then
        print_success "Nginx honeypot is running"
    else
        print_error "Nginx honeypot failed to start"
    fi

    if docker ps | grep -q "deception_service_local"; then
        print_success "Deception service is running"
    else
        print_error "Deception service failed to start"
    fi
}

# Deploy to AWS
deploy_aws() {
    echo -e "\n${BLUE}[4/5] Deploying to AWS...${NC}"

    # Check AWS configuration
    if [ -z "$EC2_HOST" ] && [ -z "$SSM_INSTANCE_ID" ]; then
        print_error "AWS configuration missing!"
        print_info "Set EC2_HOST or SSM_INSTANCE_ID environment variable"
        exit 1
    fi

    print_info "AWS deployment requires manual setup"
    print_info "Please follow the AWS deployment guide in DECEPTION_GUIDE.md"
}

# Verify deployment
verify_deployment() {
    echo -e "\n${BLUE}[5/5] Verifying deployment...${NC}"

    # Test Cowrie port
    if nc -z localhost 2222 2>/dev/null; then
        print_success "Cowrie SSH port (2222) is accessible"
    else
        print_error "Cowrie SSH port (2222) is not accessible"
    fi

    # Test nginx port
    if nc -z localhost 8080 2>/dev/null; then
        print_success "Nginx web port (8080) is accessible"
    else
        print_error "Nginx web port (8080) is not accessible"
    fi

    # Check deception logs
    if [ -f "data/deception/cowrie_integration.log" ]; then
        print_success "Deception system logs found"
    else
        print_info "Deception logs not yet created (this is normal)"
    fi
}

# Print usage information
print_usage() {
    echo -e "\n${GREEN}Deployment Complete!${NC}\n"
    echo "Next steps:"
    echo "  1. Test the honeypot:"
    echo "     ssh root@localhost -p 2222"
    echo "     curl http://localhost:8080"
    echo ""
    echo "  2. View logs:"
    echo "     docker-compose -f docker-compose.local.yml logs -f deception"
    echo ""
    echo "  3. Run training:"
    echo "     python3 main_enhanced.py --mode local --episodes 10"
    echo ""
    echo "  4. View metrics:"
    echo "     ls -lh data/deception/"
    echo ""
    echo "  5. Stop services:"
    echo "     docker-compose -f docker-compose.local.yml down"
    echo ""
}

# Main deployment flow
main() {
    print_header

    MODE="${1:-local}"

    if [ "$MODE" != "local" ] && [ "$MODE" != "aws" ]; then
        echo "Usage: $0 [local|aws]"
        exit 1
    fi

    print_info "Deployment mode: $MODE"

    check_prerequisites
    create_directories
    install_dependencies

    if [ "$MODE" = "local" ]; then
        deploy_local
    else
        deploy_aws
    fi

    verify_deployment
    print_usage
}

# Run main function
main "$@"
