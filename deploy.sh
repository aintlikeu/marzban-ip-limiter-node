#!/bin/bash
set -e

echo "🚀 Deploying Marzban Node Agent..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

# Check configuration
if [[ ! -f .env ]]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your settings:"
    echo "   - Set your NODE_ID and NODE_NAME"
    echo "   - Configure CENTRAL_REDIS_URL with your Redis server"
    echo "   - Verify ACCESS_LOG_PATH matches your Marzban setup"
    echo ""
    echo "After editing .env, run this script again."
    exit 1
fi

# Validate critical settings
if grep -q "your-redis-host" .env 2>/dev/null; then
    echo "❌ Please configure CENTRAL_REDIS_URL in .env file"
    exit 1
fi

# Stop existing container if running
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start
echo "🔨 Building and starting containers..."
docker-compose up -d --build

# Wait a moment for startup
sleep 3

# Check status
echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Useful commands:"
echo "   View logs:     docker-compose logs -f"
echo "   Check status:  docker-compose ps"
echo "   Stop service:  docker-compose down"
echo "   Restart:       docker-compose restart"
echo ""
echo "🔍 Check logs in a few seconds to ensure everything is working:"
echo "   docker-compose logs -f node-agent"
