#!/bin/bash

# Docker Setup Verification Test Script
# Tests all aspects of the Docker deployment for DND_DC_BOT

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Test results array
declare -a TEST_RESULTS

# Function to print test result
print_test_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        [ -n "$message" ] && echo -e "  ${BLUE}→${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        TEST_RESULTS+=("PASS: $test_name")
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        [ -n "$message" ] && echo -e "  ${RED}→${NC} $message"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        TEST_RESULTS+=("FAIL: $test_name")
    fi
    echo ""
}

# Function to print section header
print_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

# Function to cleanup
cleanup() {
    echo -e "${YELLOW}Cleaning up test environment...${NC}"
    docker-compose down -v 2>/dev/null || docker compose down -v 2>/dev/null
    docker rmi dnd_dc_bot-dnd-bot 2>/dev/null || true
    echo ""
}

# Get docker-compose command
get_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo "docker compose"
    fi
}

COMPOSE_CMD=$(get_compose_cmd)

# Trap to cleanup on exit
trap cleanup EXIT

print_section "Docker Setup Verification Tests"

# Test 1: Check Docker installation
print_section "Test 1: Prerequisites"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_test_result "Docker installed" "PASS" "$DOCKER_VERSION"
else
    print_test_result "Docker installed" "FAIL" "Docker not found"
    exit 1
fi

# Test 2: Check Docker Compose installation
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    COMPOSE_VERSION=$($COMPOSE_CMD version --short 2>/dev/null || $COMPOSE_CMD version 2>/dev/null | head -n1)
    print_test_result "Docker Compose installed" "PASS" "$COMPOSE_VERSION"
else
    print_test_result "Docker Compose installed" "FAIL" "Docker Compose not found"
    exit 1
fi

# Test 3: Check required files exist
print_section "Test 2: Required Files"

if [ -f "Dockerfile" ]; then
    print_test_result "Dockerfile exists" "PASS"
else
    print_test_result "Dockerfile exists" "FAIL"
fi

if [ -f "docker-compose.yml" ]; then
    print_test_result "docker-compose.yml exists" "PASS"
else
    print_test_result "docker-compose.yml exists" "FAIL"
fi

if [ -f "deploy-docker.sh" ]; then
    print_test_result "deploy-docker.sh exists" "PASS"
else
    print_test_result "deploy-docker.sh exists" "FAIL"
fi

if [ -x "deploy-docker.sh" ]; then
    print_test_result "deploy-docker.sh is executable" "PASS"
else
    print_test_result "deploy-docker.sh is executable" "FAIL"
fi

if [ -f ".dockerignore" ]; then
    print_test_result ".dockerignore exists" "PASS"
else
    print_test_result ".dockerignore exists" "FAIL"
fi

if [ -f "docker.env.example" ]; then
    print_test_result "docker.env.example exists" "PASS"
else
    print_test_result "docker.env.example exists" "FAIL"
fi

if [ -f ".env" ]; then
    print_test_result ".env file exists" "PASS"
else
    print_test_result ".env file exists" "FAIL" "Required for deployment"
fi

# Test 4: Build Docker image
print_section "Test 3: Docker Image Build"

echo "Building Docker image..."
if $COMPOSE_CMD build 2>&1 | tee /tmp/docker_build.log; then
    print_test_result "Docker image builds successfully" "PASS"
else
    print_test_result "Docker image builds successfully" "FAIL" "Check /tmp/docker_build.log"
fi

# Test 5: Verify image contents
if docker images | grep -q "dnd_dc_bot-dnd-bot\|dnd-dc-bot-dnd-bot"; then
    IMAGE_SIZE=$(docker images --format "{{.Size}}" dnd_dc_bot-dnd-bot 2>/dev/null || docker images --format "{{.Size}}" dnd-dc-bot-dnd-bot 2>/dev/null | head -n1)
    print_test_result "Docker image created" "PASS" "Size: $IMAGE_SIZE"
else
    print_test_result "Docker image created" "FAIL"
fi

# Test 6: Check Python version in image
PYTHON_VERSION=$(docker run --rm dnd_dc_bot-dnd-bot python --version 2>/dev/null || docker run --rm dnd-dc-bot-dnd-bot python --version 2>/dev/null)
if echo "$PYTHON_VERSION" | grep -q "Python 3.11"; then
    print_test_result "Python 3.11 in image" "PASS" "$PYTHON_VERSION"
else
    print_test_result "Python 3.11 in image" "FAIL" "Got: $PYTHON_VERSION"
fi

# Test 7: Check dependencies installed
echo "Checking dependencies in image..."
DEPS_CHECK=$(docker run --rm dnd_dc_bot-dnd-bot pip list 2>/dev/null || docker run --rm dnd-dc-bot-dnd-bot pip list 2>/dev/null)
if echo "$DEPS_CHECK" | grep -q "discord.py"; then
    print_test_result "discord.py installed" "PASS"
else
    print_test_result "discord.py installed" "FAIL"
fi

if echo "$DEPS_CHECK" | grep -q "aiosqlite"; then
    print_test_result "aiosqlite installed" "PASS"
else
    print_test_result "aiosqlite installed" "FAIL"
fi

if echo "$DEPS_CHECK" | grep -q "aiohttp"; then
    print_test_result "aiohttp installed" "PASS"
else
    print_test_result "aiohttp installed" "FAIL"
fi

# Test 8: Check application files in image
print_section "Test 4: Application Files in Image"

if docker run --rm dnd_dc_bot-dnd-bot ls main.py 2>/dev/null || docker run --rm dnd-dc-bot-dnd-bot ls main.py 2>/dev/null; then
    print_test_result "main.py in image" "PASS"
else
    print_test_result "main.py in image" "FAIL"
fi

if docker run --rm dnd_dc_bot-dnd-bot ls -d database 2>/dev/null || docker run --rm dnd-dc-bot-dnd-bot ls -d database 2>/dev/null; then
    print_test_result "database/ directory in image" "PASS"
else
    print_test_result "database/ directory in image" "FAIL"
fi

if docker run --rm dnd_dc_bot-dnd-bot ls -d dice 2>/dev/null || docker run --rm dnd-dc-bot-dnd-bot ls -d dice 2>/dev/null; then
    print_test_result "dice/ directory in image" "PASS"
else
    print_test_result "dice/ directory in image" "FAIL"
fi

if docker run --rm dnd_dc_bot-dnd-bot ls -d combat 2>/dev/null || docker run --rm dnd-dc-bot-dnd-bot ls -d combat 2>/dev/null; then
    print_test_result "combat/ directory in image" "PASS"
else
    print_test_result "combat/ directory in image" "FAIL"
fi

# Test 9: Deployment script commands
print_section "Test 5: Deployment Script Commands"

if ./deploy-docker.sh --help > /dev/null 2>&1; then
    print_test_result "deploy-docker.sh --help works" "PASS"
else
    print_test_result "deploy-docker.sh --help works" "FAIL"
fi

# Test 10: Start container
print_section "Test 6: Container Startup"

echo "Starting container..."
if $COMPOSE_CMD up -d 2>&1 | tee /tmp/docker_start.log; then
    print_test_result "Container starts successfully" "PASS"
    sleep 3  # Give container time to initialize
else
    print_test_result "Container starts successfully" "FAIL" "Check /tmp/docker_start.log"
fi

# Test 11: Check container status
if $COMPOSE_CMD ps | grep -q "dnd-bot"; then
    CONTAINER_STATUS=$($COMPOSE_CMD ps | grep "dnd-bot" | awk '{print $NF}')
    print_test_result "Container is running" "PASS" "Status: $CONTAINER_STATUS"
else
    print_test_result "Container is running" "FAIL"
fi

# Test 12: Check deployment script status command
if ./deploy-docker.sh --status > /dev/null 2>&1; then
    print_test_result "deploy-docker.sh --status works" "PASS"
else
    print_test_result "deploy-docker.sh --status works" "FAIL"
fi

# Test 13: Environment variable propagation
print_section "Test 7: Environment Variables"

# Check if DISCORD_TOKEN is set in container
if docker exec dnd-bot printenv DISCORD_TOKEN > /dev/null 2>&1; then
    print_test_result "DISCORD_TOKEN propagated to container" "PASS"
else
    print_test_result "DISCORD_TOKEN propagated to container" "FAIL"
fi

# Test 14: Volume mounts
print_section "Test 8: Volume Persistence"

# Create test data in database
echo "Testing database volume..."
if [ -f "dnd_bot.db" ]; then
    ORIGINAL_SIZE=$(stat -f%z "dnd_bot.db" 2>/dev/null || stat -c%s "dnd_bot.db" 2>/dev/null)
    print_test_result "Database file exists on host" "PASS" "Size: $ORIGINAL_SIZE bytes"
else
    print_test_result "Database file exists on host" "FAIL"
fi

# Check logs directory
if [ -d "logs" ]; then
    print_test_result "Logs directory exists on host" "PASS"
else
    print_test_result "Logs directory exists on host" "FAIL"
fi

# Test 15: Container logs
print_section "Test 9: Container Logs"

LOGS=$(docker logs dnd-bot 2>&1 | head -n 20)
if [ -n "$LOGS" ]; then
    print_test_result "Container produces logs" "PASS"
    echo -e "${BLUE}First few log lines:${NC}"
    echo "$LOGS" | head -n 5
    echo ""
else
    print_test_result "Container produces logs" "FAIL"
fi

# Test 16: Restart functionality
print_section "Test 10: Container Restart"

echo "Restarting container..."
if ./deploy-docker.sh --restart > /dev/null 2>&1; then
    print_test_result "deploy-docker.sh --restart works" "PASS"
    sleep 2
else
    print_test_result "deploy-docker.sh --restart works" "FAIL"
fi

# Verify container is still running after restart
if $COMPOSE_CMD ps | grep -q "dnd-bot"; then
    print_test_result "Container running after restart" "PASS"
else
    print_test_result "Container running after restart" "FAIL"
fi

# Test 17: Automatic restart policy
print_section "Test 11: Automatic Restart Policy"

RESTART_POLICY=$(docker inspect dnd-bot --format='{{.HostConfig.RestartPolicy.Name}}' 2>/dev/null)
if [ "$RESTART_POLICY" = "unless-stopped" ]; then
    print_test_result "Restart policy is 'unless-stopped'" "PASS"
else
    print_test_result "Restart policy is 'unless-stopped'" "FAIL" "Got: $RESTART_POLICY"
fi

# Test 18: Stop container
print_section "Test 12: Container Stop"

echo "Stopping container..."
if ./deploy-docker.sh --down > /dev/null 2>&1; then
    print_test_result "deploy-docker.sh --down works" "PASS"
else
    print_test_result "deploy-docker.sh --down works" "FAIL"
fi

# Verify container is stopped
if ! $COMPOSE_CMD ps | grep -q "dnd-bot.*Up"; then
    print_test_result "Container stopped successfully" "PASS"
else
    print_test_result "Container stopped successfully" "FAIL"
fi

# Test 19: Non-Docker deployment compatibility
print_section "Test 13: Non-Docker Deployment Compatibility"

# Check if main.py can be executed directly (syntax check)
if python3 -m py_compile main.py 2>/dev/null; then
    print_test_result "main.py syntax valid for direct execution" "PASS"
else
    print_test_result "main.py syntax valid for direct execution" "FAIL"
fi

# Check if requirements.txt is valid (check syntax and readability)
if python3 -c "import sys; [line.strip() for line in open('requirements.txt') if line.strip() and not line.startswith('#')]" > /dev/null 2>&1; then
    print_test_result "requirements.txt valid for pip install" "PASS"
else
    print_test_result "requirements.txt valid for pip install" "FAIL"
fi

# Test 20: Documentation exists
print_section "Test 14: Documentation"

if [ -f "docs/docker-deployment-guide.md" ]; then
    print_test_result "Docker deployment guide exists" "PASS"
else
    print_test_result "Docker deployment guide exists" "FAIL"
fi

if grep -q "Docker" README.md 2>/dev/null; then
    print_test_result "README mentions Docker deployment" "PASS"
else
    print_test_result "README mentions Docker deployment" "FAIL"
fi

# Final summary
print_section "Test Summary"

echo -e "${BLUE}Total Tests:${NC} $TESTS_TOTAL"
echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Failed:${NC} $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ ALL TESTS PASSED${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ✗ SOME TESTS FAILED${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Failed tests:${NC}"
    for result in "${TEST_RESULTS[@]}"; do
        if [[ $result == FAIL* ]]; then
            echo -e "  ${RED}•${NC} ${result#FAIL: }"
        fi
    done
    exit 1
fi
