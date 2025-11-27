#!/bin/bash
# Complete Local Testing Script for DeceptiCloud
# This script runs all tests in sequence with validation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "DeceptiCloud Complete Local Test Suite"
echo -e "==========================================${NC}\n"

# Function to print status
print_status() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Check prerequisites
print_status "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker Desktop."
    exit 1
fi
print_success "Docker found: $(docker --version)"

if ! command -v python3 &> /dev/null; then
    print_error "Python3 not found. Please install Python 3.8+."
    exit 1
fi
print_success "Python3 found: $(python3 --version)"

# Step 2: Setup environment
print_status "Setting up environment..."
bash scripts/setup_local_test.sh

# Step 3: Start honeypots
print_status "Starting honeypots..."
docker-compose -f docker-compose.local.yml up -d

echo ""
print_status "Waiting 30 seconds for containers to initialize..."
for i in {30..1}; do
    echo -ne "\r  ${i} seconds remaining..."
    sleep 1
done
echo -e "\r  ${GREEN}✓${NC} Containers initialized"

# Step 4: Check container status
print_status "Checking container health..."

COWRIE_STATUS=$(docker inspect --format='{{.State.Status}}' cowrie_honeypot_local 2>/dev/null || echo "not found")
NGINX_STATUS=$(docker inspect --format='{{.State.Status}}' nginx_honeypot_local 2>/dev/null || echo "not found")

if [ "$COWRIE_STATUS" = "running" ]; then
    print_success "Cowrie SSH honeypot: running"
else
    print_error "Cowrie SSH honeypot: $COWRIE_STATUS"
fi

if [ "$NGINX_STATUS" = "running" ]; then
    print_success "nginx web honeypot: running"
else
    print_error "nginx web honeypot: $NGINX_STATUS"
fi

# Step 5: Test SSH honeypot manually
print_status "Testing SSH honeypot connectivity..."
if nc -z localhost 2222 2>/dev/null; then
    print_success "SSH honeypot listening on port 2222"
else
    print_warning "SSH honeypot port 2222 not accessible"
fi

# Step 6: Test web honeypot manually
print_status "Testing web honeypot connectivity..."
if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    print_success "Web honeypot responding on port 8080"

    # Test honeytoken
    if curl -s http://localhost:8080/.env | grep -q "AWS_ACCESS_KEY_ID"; then
        print_success "Honeytokens accessible (.env file)"
    else
        print_warning "Honeytokens not found"
    fi
else
    print_warning "Web honeypot port 8080 not accessible"
fi

# Step 7: Run automated tests
print_status "Running automated honeypot tests..."
python3 scripts/test_local_honeypots.py

# Step 8: Generate attack traffic
print_status "Generating attack traffic for testing..."

# SSH attacks in background
print_status "Simulating SSH attacks..."
for i in {1..5}; do
    timeout 2 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 -p 2222 root@localhost 2>/dev/null &
    sleep 1
done

# Web attacks
print_status "Simulating web attacks..."
for path in / /admin /.env /robots.txt /.git/config; do
    curl -s http://localhost:8080$path > /dev/null 2>&1 &
done

wait
sleep 3

# Step 9: Check logs
print_status "Checking honeypot logs..."

COWRIE_LOGS=$(docker logs --tail 20 cowrie_honeypot_local 2>&1)
NGINX_LOGS=$(docker logs --tail 20 nginx_honeypot_local 2>&1)

if echo "$COWRIE_LOGS" | grep -q -i "ssh\|connection\|login"; then
    print_success "Cowrie logs contain activity"
else
    print_warning "Cowrie logs appear empty"
fi

if echo "$NGINX_LOGS" | grep -q -i "GET\|POST\|404"; then
    print_success "nginx logs contain activity"
else
    print_warning "nginx logs appear empty"
fi

# Step 10: Test RL agent (short run)
print_status "Testing RL agent (2 episodes)..."
if python3 main_local.py --episodes 2 --timesteps 5; then
    print_success "RL agent completed test run"
else
    print_error "RL agent failed"
fi

# Step 11: Summary
echo -e "\n${BLUE}=========================================="
echo "Test Summary"
echo -e "==========================================${NC}\n"

echo "Honeypot Status:"
echo "  Cowrie (SSH): $COWRIE_STATUS"
echo "  nginx (web):  $NGINX_STATUS"
echo ""

echo "Access Points:"
echo "  SSH honeypot:  ssh -p 2222 root@localhost"
echo "  Web honeypot:  http://localhost:8080"
echo ""

echo "View Logs:"
echo "  docker logs -f cowrie_honeypot_local"
echo "  docker logs -f nginx_honeypot_local"
echo ""

echo "Results:"
if [ -f "results/local_timesteps.csv" ]; then
    echo "  ✓ Training results: results/local_timesteps.csv"
else
    echo "  ✗ No training results found"
fi

if [ -f "local_test_results_*.json" ]; then
    echo "  ✓ Test results: $(ls local_test_results_*.json | tail -1)"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Testing Complete!"
echo -e "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Run full training: python3 main_local.py --episodes 10"
echo "  2. View results: cat results/local_episodes.csv"
echo "  3. Stop honeypots: docker-compose -f docker-compose.local.yml down"
echo ""
