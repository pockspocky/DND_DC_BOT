#!/bin/bash

# Quick Docker Setup Verification Script
# This is a simplified version for quick checks

set -e

echo "🐳 Docker Setup Quick Verification"
echo "=================================="
echo ""

# Check Docker
if command -v docker &> /dev/null; then
    echo "✓ Docker installed: $(docker --version)"
else
    echo "✗ Docker not installed"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo "✓ Docker Compose installed"
else
    echo "✗ Docker Compose not installed"
    exit 1
fi

# Check required files
echo ""
echo "Checking required files..."
for file in Dockerfile docker-compose.yml deploy-docker.sh .dockerignore docker.env.example; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
        exit 1
    fi
done

# Check .env file
if [ -f ".env" ]; then
    echo "✓ .env file exists"
else
    echo "⚠ .env file missing (copy from docker.env.example)"
fi

echo ""
echo "=================================="
echo "✓ Docker setup verified!"
echo ""
echo "To run comprehensive tests, use:"
echo "  ./test_docker_setup.sh"
echo ""
echo "To deploy the bot, use:"
echo "  ./deploy-docker.sh"
