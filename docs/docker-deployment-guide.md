# Docker Deployment Guide

This guide provides comprehensive instructions for deploying DND_DC_BOT using Docker, including setup, configuration, operations, and troubleshooting.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Operations](#operations)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## Prerequisites

### Required Software

Before deploying DND_DC_BOT with Docker, ensure you have the following installed:

#### Docker

**Minimum Version**: Docker 20.10.0 or higher

**Installation Instructions**:

- **Ubuntu/Debian**:
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  ```
  Log out and back in for group changes to take effect.

- **macOS**:
  Download and install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

- **Windows**:
  Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

**Verify Installation**:
```bash
docker --version
# Expected output: Docker version 20.10.0 or higher
```

#### Docker Compose

**Minimum Version**: Docker Compose 1.28.0 or higher

**Installation Instructions**:

- **Linux**:
  ```bash
  sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  ```

- **macOS/Windows**:
  Docker Compose is included with Docker Desktop

**Verify Installation**:
```bash
docker-compose --version
# Expected output: docker-compose version 1.28.0 or higher
```

### System Requirements

- **CPU**: 1 core minimum, 2+ cores recommended
- **RAM**: 512 MB minimum, 1 GB+ recommended
- **Disk Space**: 500 MB for Docker image and data
- **Network**: Internet connection for Discord API and external services

### Required Credentials

Before deployment, obtain the following:

1. **Discord Bot Token**:
   - Visit [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application or select existing one
   - Navigate to "Bot" section
   - Click "Reset Token" to generate a new token
   - Copy and save the token securely

2. **Google Gemini API Key** (Optional, for AI scene generation):
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy and save the key securely

## Quick Start

Follow these steps to deploy DND_DC_BOT with Docker in minutes:

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/DND_DC_BOT.git
cd DND_DC_BOT
```

### Step 2: Configure Environment Variables

Copy the example environment file and edit it with your credentials:

```bash
cp docker.env.example .env
```

Edit `.env` file with your preferred text editor:

```bash
nano .env
# or
vim .env
```

**Required Configuration**:
```env
DISCORD_TOKEN=your_discord_bot_token_here
```

**Optional Configuration**:
```env
GEMINI_API_KEY=your_gemini_api_key_here
LOG_LEVEL=INFO
DATABASE_PATH=dnd_bot.db
```

Save and close the file.

### Step 3: Deploy the Bot

Make the deployment script executable (first time only):

```bash
chmod +x deploy-docker.sh
```

Deploy the bot:

```bash
./deploy-docker.sh
```

**Expected Output**:
```
🚀 Building and starting DND_DC_BOT...
Building dnd-bot
[+] Building 45.2s (10/10) FINISHED
Creating dnd-bot ... done
✅ DND_DC_BOT is now running!
📊 Check status: ./deploy-docker.sh --status
📋 View logs: ./deploy-docker.sh --logs
```

### Step 4: Verify Deployment

Check that the bot is running:

```bash
./deploy-docker.sh --status
```

**Expected Output**:
```
Name       Command          State   Ports
dnd-bot    python main.py   Up
```

View the logs to confirm successful connection:

```bash
./deploy-docker.sh --logs
```

**Expected Log Output**:
```
INFO: Bot is starting...
INFO: Logged in as DND_DC_BOT#1234
INFO: Connected to Discord successfully
```

### Step 5: Test the Bot

In your Discord server, try a test command:

```
/r 1d20
```

If the bot responds with a dice roll result, deployment is successful! 🎉

## Configuration

### Environment Variables

The bot is configured through environment variables in the `.env` file. Here's a complete reference:

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Discord bot authentication token | `your_discord_bot_token_here` |

#### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `GEMINI_API_KEY` | Gem Key | None | `**********************` |
| `LOG_LEVEL` | Logging verbosity level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `DATABASE_PATH` | SQLite database file path | `dnd_bot.db` | `dnd_bot.db` |
| `PREFIX` | Command prefix (legacy, slash commands don't use this) | `!` | `!` |

#### Obtaining API Keys

**Discord Bot Token**:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Navigate to "Bot" section
4. Click "Reset Token" and copy the new token
5. **Important**: Never share your token publicly

**Google Gemini API Key**:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Note: Free tier has usage limits

### Volume Mounts

Docker Compose automatically mounts two directories for data persistence:

#### Database Volume

```yaml
./dnd_bot.db:/app/dnd_bot.db
```

- **Purpose**: Persists all game data (users, characters, combat sessions, roll history)
- **Location**: `./dnd_bot.db` on host system
- **Backup**: Copy this file to backup all bot data

#### Logs Volume

```yaml
./logs:/app/logs
```

- **Purpose**: Persists log files for debugging and monitoring
- **Location**: `./logs/` directory on host system
- **Files**:
  - `bot.log`: General bot activity logs
  - `error.log`: Error and exception logs

### Network Configuration

By default, the bot uses Docker's default bridge network, which is sufficient for most deployments. The bot only needs outbound internet access to:

- Discord API (`discord.com`)
- Google Gemini API (`generativelanguage.googleapis.com`)
- D&D 5e SRD API (`www.dnd5eapi.co`)

No inbound ports need to be exposed.

## Operations

### Starting the Bot

Deploy or start the bot:

```bash
./deploy-docker.sh
```

This command:
1. Builds the Docker image (if needed)
2. Starts the container in detached mode
3. Applies the restart policy

**Options**:
- Rebuilds image even if no changes: `docker-compose up -d --build`
- View startup logs: Add `--logs` flag after starting

### Viewing Logs

Display real-time logs:

```bash
./deploy-docker.sh --logs
```

**Behavior**:
- Shows all historical logs
- Follows new log entries in real-time
- Press `Ctrl+C` to exit (container keeps running)

**Alternative**: View logs without the script:
```bash
docker-compose logs -f dnd-bot
```

**View specific number of lines**:
```bash
docker-compose logs --tail=100 dnd-bot
```

### Checking Status

Check if the container is running:

```bash
./deploy-docker.sh --status
```

**Output Interpretation**:

- `State: Up`: Container is running normally
- `State: Restarting`: Container is restarting after a crash
- `State: Exit`: Container has stopped (check logs for errors)

**Detailed status**:
```bash
docker ps -a | grep dnd-bot
```

### Restarting the Bot

Restart the container:

```bash
./deploy-docker.sh --restart
```

**Use Cases**:
- Apply configuration changes in `.env`
- Recover from unexpected state
- Clear memory/cache

**Note**: Database and logs are preserved during restart.

### Stopping the Bot

Stop and remove the container:

```bash
./deploy-docker.sh --down
```

**Behavior**:
- Gracefully stops the container
- Removes the container (but not the image)
- Preserves database and logs

**To start again**: Run `./deploy-docker.sh`

### Updating the Bot

When new code is available:

#### Step 1: Pull Latest Code

```bash
git pull origin main
```

#### Step 2: Rebuild and Deploy

```bash
./deploy-docker.sh
```

The `--build` flag is included automatically, so the image will be rebuilt with the new code.

#### Step 3: Verify Update

```bash
./deploy-docker.sh --logs
```

Check logs for successful startup with new version.

### Backing Up Data

#### Backup Database

```bash
cp dnd_bot.db dnd_bot.db.backup.$(date +%Y%m%d)
```

#### Backup Logs

```bash
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

#### Restore Database

```bash
cp dnd_bot.db.backup.20241124 dnd_bot.db
./deploy-docker.sh --restart
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Container Won't Start

**Symptoms**:
- `./deploy-docker.sh` completes but container is not running
- `--status` shows `State: Exit`

**Diagnosis**:
```bash
./deploy-docker.sh --logs
```

**Common Causes**:

1. **Missing or Invalid Discord Token**:
   ```
   ERROR: discord.errors.LoginFailure: Improper token has been passed
   ```
   **Solution**: Verify `DISCORD_TOKEN` in `.env` file is correct

2. **Missing .env File**:
   ```
   ERROR: .env file not found
   ```
   **Solution**: Copy `docker.env.example` to `.env` and configure

3. **Python Dependency Error**:
   ```
   ERROR: Could not find a version that satisfies the requirement
   ```
   **Solution**: Rebuild image with `docker-compose build --no-cache`

#### Issue: SSL Certificate Errors

**Symptoms**:
```
ERROR: SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution**:

Docker deployment should resolve SSL issues automatically. If you still encounter SSL errors:

1. **Verify base image**:
   ```bash
   docker-compose build --no-cache
   ```

2. **Check Docker version**:
   ```bash
   docker --version
   # Ensure version 20.10.0+
   ```

3. **Test SSL from container**:
   ```bash
   docker-compose exec dnd-bot python -c "import ssl; print(ssl.OPENSSL_VERSION)"
   ```

#### Issue: Permission Denied Errors

**Symptoms**:
```
ERROR: PermissionError: [Errno 13] Permission denied: '/app/dnd_bot.db'
```

**Solution**:

1. **Check file permissions**:
   ```bash
   ls -la dnd_bot.db logs/
   ```

2. **Fix permissions**:
   ```bash
   chmod 666 dnd_bot.db
   chmod -R 777 logs/
   ```

3. **Restart container**:
   ```bash
   ./deploy-docker.sh --restart
   ```

#### Issue: Database Locked

**Symptoms**:
```
ERROR: database is locked
```

**Solution**:

1. **Check for multiple instances**:
   ```bash
   docker ps -a | grep dnd-bot
   ```

2. **Stop all instances**:
   ```bash
   docker stop $(docker ps -aq --filter name=dnd-bot)
   ```

3. **Remove stale containers**:
   ```bash
   docker rm $(docker ps -aq --filter name=dnd-bot)
   ```

4. **Restart**:
   ```bash
   ./deploy-docker.sh
   ```

#### Issue: Bot Not Responding to Commands

**Symptoms**:
- Bot appears online in Discord
- Commands don't trigger any response

**Diagnosis**:

1. **Check logs for errors**:
   ```bash
   ./deploy-docker.sh --logs
   ```

2. **Verify bot permissions**:
   - Bot needs "applications.commands" scope
   - Bot needs "Send Messages" permission in channels

3. **Check command registration**:
   ```
   INFO: Successfully synced X application commands
   ```

**Solution**:

1. **Re-invite bot with correct permissions**:
   - Use Discord Developer Portal to generate new invite URL
   - Include "applications.commands" scope
   - Include necessary bot permissions

2. **Restart bot**:
   ```bash
   ./deploy-docker.sh --restart
   ```

#### Issue: High Memory Usage

**Symptoms**:
- Container using excessive memory
- System becomes slow

**Diagnosis**:
```bash
docker stats dnd-bot
```

**Solution**:

1. **Restart container** (clears memory):
   ```bash
   ./deploy-docker.sh --restart
   ```

2. **Add memory limits** (see Advanced Topics)

#### Issue: Cannot Connect to Discord

**Symptoms**:
```
ERROR: Cannot connect to host discord.com:443
```

**Solution**:

1. **Check internet connectivity**:
   ```bash
   ping discord.com
   ```

2. **Check firewall rules**:
   - Ensure outbound HTTPS (443) is allowed
   - Check Docker network settings

3. **Test from container**:
   ```bash
   docker-compose exec dnd-bot ping discord.com
   ```

4. **If behind proxy**: See Advanced Topics for proxy configuration

### Getting Help

If you encounter issues not covered here:

1. **Check logs thoroughly**:
   ```bash
   ./deploy-docker.sh --logs > debug.log
   ```

2. **Verify environment**:
   ```bash
   docker --version
   docker-compose --version
   cat .env
   ```

3. **Check GitHub Issues**: Search for similar problems

4. **Create detailed bug report** with:
   - Error messages from logs
   - Docker and Docker Compose versions
   - Operating system
   - Steps to reproduce

## Advanced Topics

### Production Considerations

#### Resource Limits

Limit container resource usage in `docker-compose.yml`:

```yaml
services:
  dnd-bot:
    # ... existing configuration ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

Apply changes:
```bash
./deploy-docker.sh
```

#### Health Checks

Add health check to `docker-compose.yml`:

```yaml
services:
  dnd-bot:
    # ... existing configuration ...
    healthcheck:
      test: ["CMD", "python", "-c", "import discord; print('healthy')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

#### Logging Configuration

Configure log rotation in `docker-compose.yml`:

```yaml
services:
  dnd-bot:
    # ... existing configuration ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Custom Network Configuration

#### Create Custom Network

```bash
docker network create dnd-bot-network
```

Update `docker-compose.yml`:

```yaml
services:
  dnd-bot:
    # ... existing configuration ...
    networks:
      - dnd-bot-network

networks:
  dnd-bot-network:
    external: true
```

#### Proxy Configuration

If deploying behind a corporate proxy, add to `.env`:

```env
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
NO_PROXY=localhost,127.0.0.1
```

Update `docker-compose.yml`:

```yaml
services:
  dnd-bot:
    # ... existing configuration ...
    environment:
      - HTTP_PROXY=${HTTP_PROXY}
      - HTTPS_PROXY=${HTTPS_PROXY}
      - NO_PROXY=${NO_PROXY}
```

### Multi-Container Setup

If running multiple bots or services:

#### Separate Databases

```yaml
services:
  dnd-bot-1:
    build: .
    container_name: dnd-bot-1
    env_file: .env.bot1
    volumes:
      - ./dnd_bot_1.db:/app/dnd_bot.db
      - ./logs/bot1:/app/logs

  dnd-bot-2:
    build: .
    container_name: dnd-bot-2
    env_file: .env.bot2
    volumes:
      - ./dnd_bot_2.db:/app/dnd_bot.db
      - ./logs/bot2:/app/logs
```

### Monitoring and Alerting

#### Container Monitoring

Use Docker stats for real-time monitoring:

```bash
docker stats dnd-bot
```

#### Log Monitoring

Monitor for errors:

```bash
docker-compose logs -f dnd-bot | grep ERROR
```

#### Automated Restart Monitoring

Check restart count:

```bash
docker inspect dnd-bot --format='{{.RestartCount}}'
```

### Performance Optimization

#### Image Size Optimization

Current Dockerfile uses `python:3.11-slim` for optimal size. Further optimization:

1. **Multi-stage builds** (if needed):
   ```dockerfile
   FROM python:3.11-slim as builder
   # Build dependencies
   
   FROM python:3.11-slim
   COPY --from=builder /app /app
   ```

2. **Remove unnecessary files**:
   Update `.dockerignore` to exclude more files

#### Startup Time Optimization

- Use image caching effectively
- Pre-build images: `docker-compose build`
- Use Docker layer caching in CI/CD

### Security Best Practices

#### Environment Variable Security

1. **Never commit `.env` file**:
   ```bash
   # Verify .env is in .gitignore
   git check-ignore .env
   ```

2. **Use secrets management** (production):
   - Docker Secrets
   - HashiCorp Vault
   - AWS Secrets Manager

#### Container Security

1. **Run as non-root user** (add to Dockerfile):
   ```dockerfile
   RUN useradd -m -u 1000 botuser
   USER botuser
   ```

2. **Read-only root filesystem**:
   ```yaml
   services:
     dnd-bot:
       read_only: true
       tmpfs:
         - /tmp
   ```

3. **Scan images for vulnerabilities**:
   ```bash
   docker scan dnd-bot
   ```

### Backup Automation

#### Automated Database Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp dnd_bot.db "$BACKUP_DIR/dnd_bot_$DATE.db"

# Keep only last 7 days
find $BACKUP_DIR -name "dnd_bot_*.db" -mtime +7 -delete

echo "Backup completed: dnd_bot_$DATE.db"
```

#### Cron Job Setup

```bash
chmod +x backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line:
0 2 * * * /path/to/DND_DC_BOT/backup.sh
```

### Migration from Non-Docker Deployment

If migrating from a non-Docker deployment:

#### Step 1: Backup Existing Data

```bash
cp dnd_bot.db dnd_bot.db.backup
cp -r logs logs.backup
```

#### Step 2: Stop Non-Docker Bot

```bash
# Find process
ps aux | grep "python.*main.py"

# Kill process
kill <PID>
```

#### Step 3: Deploy with Docker

```bash
cp .env.example .env
# Edit .env with existing configuration
./deploy-docker.sh
```

#### Step 4: Verify Migration

```bash
./deploy-docker.sh --logs
```

Existing database and logs will be used automatically.

### CI/CD Integration

#### GitHub Actions Example

```yaml
name: Deploy Bot

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker-compose build
      
      - name: Deploy to server
        run: |
          ssh user@server 'cd /path/to/bot && git pull && ./deploy-docker.sh'
```

### Troubleshooting Advanced Issues

#### Container Keeps Restarting

Check restart loop:

```bash
docker logs dnd-bot --tail=50
docker inspect dnd-bot --format='{{.State.Status}}'
```

Disable auto-restart temporarily:

```yaml
restart: "no"
```

#### Network Connectivity Issues

Test DNS resolution:

```bash
docker-compose exec dnd-bot nslookup discord.com
```

Test HTTPS connectivity:

```bash
docker-compose exec dnd-bot curl -I https://discord.com
```

#### Database Corruption

If database is corrupted:

```bash
# Restore from backup
cp dnd_bot.db.backup dnd_bot.db

# Or reinitialize (loses data)
rm dnd_bot.db
docker-compose exec dnd-bot python database/init_db.py
```

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Project GitHub Repository](https://github.com/yourusername/DND_DC_BOT)

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in `docs/`
- Review troubleshooting section above

---

**Last Updated**: 2024-11-24
**Version**: 1.0.0
