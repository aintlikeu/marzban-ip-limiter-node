# Use Python 3.12 slim image for smaller footprint
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Create non-privileged user for security
RUN groupadd -r nodeagent && useradd -r -g nodeagent nodeagent

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY config/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create directory for logs and ensure proper permissions
RUN mkdir -p /var/log/nodeagent && \
    chown -R nodeagent:nodeagent /app /var/log/nodeagent

# Switch to non-privileged user
USER nodeagent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.append('/app/src'); \
    from node_agent.config import ConfigService; \
    import redis.asyncio as redis; \
    import asyncio; \
    config = ConfigService.load_from_env(); \
    loop = asyncio.new_event_loop(); \
    asyncio.set_event_loop(loop); \
    client = redis.from_url(config.central_redis_url); \
    loop.run_until_complete(client.ping()); \
    loop.run_until_complete(client.close())" || exit 1

# Set Python path
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose port for health checks (if needed)
EXPOSE 8080

# Run the application
CMD ["python", "-m", "node_agent.main"]
