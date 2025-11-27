# DND_DC_BOT - Dungeons & Dragons Discord Bot

![Status](https://img.shields.io/badge/status-stable-green) ![Version](https://img.shields.io/badge/version-v1.4.0-blue) ![Commands](https://img.shields.io/badge/slash%20commands-22-orange) ![AI](https://img.shields.io/badge/AI-Gemini%20API-purple)

A Discord bot designed specifically for Dungeons & Dragons (D&D) gameplay, featuring AI scene generation, comprehensive game assistance, and intelligent query systems.

## 🆕 Latest Features

### 🎭 AI Scene Generator (NEW!)
- **Gemini AI Powered**: Generate high-quality scene descriptions using Google Gemini API
- **Custom Styles**: Support for any style keywords (horror, romantic, humorous, epic, poetic, etc.)
- **Flexible Length**: Adjustable from 50-500 words
- **DM Exclusive**: Rich scene description tools for Dungeon Masters

### 🎲 Complete Game System
- **22 Slash Commands**: Full coverage of dice, queries, combat, scene generation, and more
- **Intelligent Caching**: Optimized API response speed
- **Data Persistence**: SQLite database stores all game data

## 🚀 Quick Start

### Prerequisites

**Docker Deployment (Recommended)** 🐳:
- Docker 20.10+
- Docker Compose 1.28+

**Direct Python Deployment**:
- Python 3.8+
- pip

### Installation Steps

#### Option 1: Docker Deployment (Recommended for SSL Issues) 🐳

Docker deployment is **recommended** if you encounter SSL certificate errors or network connectivity issues. It provides a consistent environment with modern SSL support.

1. **Clone the project**
```bash
git clone https://github.com/yourusername/DND_DC_BOT.git
cd DND_DC_BOT
```

2. **Configure environment variables**
```bash
cp docker.env.example .env
nano .env  # Edit with your tokens
```

Required configuration:
```env
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key  # Optional, for AI scene generation
```

3. **Deploy the bot**
```bash
# Make deployment script executable
chmod +x deploy-docker.sh

# Deploy (builds image and starts container)
./deploy-docker.sh

# View logs
./deploy-docker.sh --logs

# Check status
./deploy-docker.sh --status
```

**Docker Management Commands**:
```bash
./deploy-docker.sh          # Deploy/update bot
./deploy-docker.sh --status # Show container status
./deploy-docker.sh --logs   # View logs (follow mode)
./deploy-docker.sh --restart # Restart container
./deploy-docker.sh --down   # Stop and remove container
```

📖 **Full Docker Guide**: See [Docker Deployment Guide](docs/docker-deployment-guide.md) for detailed instructions, troubleshooting, and advanced configuration.

#### Option 2: Direct Python Deployment

1. **Clone the project**
```bash
git clone https://github.com/yourusername/DND_DC_BOT.git
cd DND_DC_BOT
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
Create `.env` file:
```env
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key  # Optional, for AI scene generation
```

4. **Start the bot**
```bash
# Direct start (recommended)
python3 main.py

# Background start
nohup python3 main.py > bot.log 2>&1 &
```

## 🎲 Core Features

### 🎭 AI Scene Generator ✨
Intelligent scene description generation for DMs using Google Gemini API

**Command**: `/scene`

**Parameters**:
- `description`: English scene description
- `length`: Description length (50-500 words, default 100)
- `style`: Style keyword (supports any custom style)

**Supported Styles**:
- **Preset Styles**: Descriptive, mysterious, tense, dramatic, horror, romantic, humorous, epic, cozy, adventure
- **Custom Styles**: Poetic, eerie, melancholic, majestic, playful, classical, modern, and any other keywords

**Usage Examples**:
```
/scene description:"A mysterious forest" length:120 style:"horror"
/scene description:"A romantic garden" length:100 style:"romantic"
/scene description:"A funny tavern" length:150 style:"humorous"
/scene description:"A dark castle" length:80 style:"eerie"
```

### 🎲 Dice System ✅
Complete D&D dice rolling system

| Command | Description | Example |
|---------|-------------|---------|
| `/r` | Roll dice | `/r dice:d20 modifier:5 advantage:advantage` |
| `/check` | Skill check | `/check modifier:3 advantage:advantage` |
| `/save` | Saving throw | `/save save_type:dexterity modifier:2` |
| `/att` | Attack roll | `/att attack_bonus:5 damage_dice:1d8+3` |
| `/stats` | Generate character stats | `/stats method:4d6 drop lowest` |
| `/rh` | Dice help | `/rh` |

**Advanced Features**:
- Advantage/disadvantage rolls
- Multiple dice rolls
- Keep/drop rules
- Complex modifier calculations
- Private roll mode

### 🔍 Query System ✅
Complete D&D 5e resource queries

| Command | Description | Example |
|---------|-------------|---------|
| `/sp` | Spell query | `/sp fireball` |
| `/mon` | Monster query | `/mon goblin` |
| `/sk` | Skill query | `/sk perception` |

**Key Features**:
- Intelligent search matching
- Detailed information display
- Auto-thread expansion for long content
- 1-hour intelligent caching
- User-friendly error messages

### ⚔️ Combat Management System ✅
Complete D&D combat assistance tools

| Command | Description | Example |
|---------|-------------|---------|
| `/cs` | Start combat | `/cs name:Goblin Ambush` |
| `/ce` | End combat | `/ce` |
| `/st` | Combat status | `/st` |
| `/add` | Add participant | `/add name:Goblin max_hp:7 initiative:12` |
| `/rm` | Remove participant | `/rm name:Goblin` |
| `/next` | Next turn | `/next` |
| `/dmg` | Deal damage | `/dmg target:Goblin expression:1d6+2` |
| `/heal` | Heal character | `/heal target:Wizard expression:1d8+3` |

**Combat System Features**:
- Automatic initiative sorting
- Turn-based management
- Real-time HP tracking
- Dice expression support
- Multi-channel independent sessions
- DM permission control

### 🛠️ Basic Tools
| Command | Description | Example |
|---------|-------------|---------|
| `/ping` | Test response | `/ping` |
| `/help` | Help information | `/help` |
| `/dbstats` | Database statistics | `/dbstats` |
| `/echo` | Echo message | `/echo message:"test"` |

## 🎯 Complete `/r` Command Guide

### Basic Usage
```
/r dice:d20                          # Roll 1d20
/r dice:d6                           # Roll 1d6
/r dice:d100                         # Roll 1d100
```

### With Modifiers
```
/r dice:d20 modifier:5               # Roll d20+5
/r dice:d8 modifier:-2               # Roll d8-2
```

### Advantage/Disadvantage Rolls
```
/r dice:d20 advantage:advantage      # Advantage roll (2d20 keep highest)
/r dice:d20 advantage:disadvantage   # Disadvantage roll (2d20 keep lowest)
/r dice:d20 advantage:advantage modifier:3  # Advantage roll +3
```

### Multiple Dice
```
/r dice:d6 count:3                   # Roll 3d6
/r dice:d8 count:2 modifier:4        # Roll 2d8+4
```

### Keep/Drop Rules
```
/r dice:d6 count:4 drop_lowest:1     # 4d6 drop lowest (D&D stat generation)
/r dice:d20 count:2 keep_highest:1   # 2d20 keep highest
/r dice:d12 count:5 keep_highest:3 modifier:-1  # 5d12 keep highest 3, -1
```

### Complex Combination Examples
```
/r dice:d8 count:3 modifier:2 private:true      # 3d8+2 (private display)
/r dice:d6 advantage:advantage modifier:4       # d6 advantage roll +4
```

## 🎭 Scene Generator Detailed Guide

### Basic Usage
```
/scene description:"A dark forest path" style:"mysterious"
```

### Style Selection
**Preset Styles**:
- `descriptive`: Rich adjectives and sensory descriptions
- `mysterious`: Creates mysterious atmosphere and hints
- `tense`: Urgent language and short sentences
- `dramatic`: Dramatic language, enhanced emotional impact
- `horror`: Unsettling descriptions and sense of fear
- `romantic`: Beautiful poetic language
- `humorous`: Light and funny descriptions
- `epic`: Grand and magnificent language
- `cozy`: Warm and intimate atmosphere
- `adventure`: Energetic sense of exploration

**Custom Styles**:
- Can use any style keywords
- Examples: `poetic`, `eerie`, `melancholic`, `majestic`, `playful`, etc.
- AI automatically adjusts generation strategy based on keyword characteristics

### Length Control
- **Minimum length**: 50 words
- **Maximum length**: 500 words
- **Default length**: 100 words
- **Recommended length**: 80-150 words (suitable for reading aloud)

### Advanced Examples
```
/scene description:"An ancient library with floating books" length:150 style:"epic"
/scene description:"A crowded marketplace" length:100 style:"humorous"
/scene description:"A haunted mansion" length:120 style:"horror"
/scene description:"A peaceful meadow" length:80 style:"poetic"
```

## 🛠️ Technology Stack

- **Python 3.8+**: Primary development language (Python 3.11 in Docker)
- **discord.py**: Discord API library
- **Google Gemini API**: AI scene generation
- **SQLite**: Local data storage
- **python-dotenv**: Environment variable management
- **aiosqlite**: Async SQLite database operations
- **aiohttp**: Async HTTP client for API requests
- **Docker**: Containerized deployment (recommended for SSL issues)
- **Docker Compose**: Service orchestration

## 🚀 Deployment Guide

### Deployment Method Comparison

| Feature | Docker Deployment 🐳 | Direct Python Deployment |
|---------|---------------------|-------------------------|
| **SSL Issues** | ✅ Resolved automatically | ⚠️ May require manual fixes |
| **Setup Complexity** | ⭐⭐ Simple | ⭐⭐⭐ Moderate |
| **Dependency Management** | ✅ Automatic | ⚠️ Manual |
| **Environment Isolation** | ✅ Complete isolation | ❌ System-wide |
| **Updates** | ✅ One command | ⚠️ Manual steps |
| **Recommended For** | Production, SSL issues | Development, testing |

### Docker Deployment (Recommended) 🐳

**Why Docker?**
- ✅ Resolves SSL certificate issues automatically
- ✅ Consistent environment across all systems
- ✅ No dependency conflicts
- ✅ Easy updates and rollbacks
- ✅ Automatic restart on crashes

#### Prerequisites
- Docker 20.10+
- Docker Compose 1.28+
- Stable network connection

#### Detailed Steps

1. **Install Docker** (if not already installed)
```bash
# Check Docker installation
docker --version
docker-compose --version

# If not installed, visit: https://docs.docker.com/get-docker/
```

2. **Project Setup**
```bash
# Clone the project
git clone https://github.com/yourusername/DND_DC_BOT.git
cd DND_DC_BOT

# Copy and configure environment file
cp docker.env.example .env
nano .env  # Edit with your tokens
```

3. **Configure Environment Variables**
```env
# Discord bot token (required)
DISCORD_TOKEN=your_discord_bot_token

# Gemini API key (optional, for AI scene generation)
GEMINI_API_KEY=your_gemini_api_key

# Log level (optional)
LOG_LEVEL=INFO

# Database file path (optional)
DATABASE_PATH=dnd_bot.db
```

4. **Deploy the Bot**
```bash
# Make deployment script executable
chmod +x deploy-docker.sh

# Deploy (builds image and starts container)
./deploy-docker.sh

# The bot will start in detached mode
# Database and logs are persisted on your host system
```

5. **Manage the Bot**
```bash
# View logs (real-time)
./deploy-docker.sh --logs

# Check container status
./deploy-docker.sh --status

# Restart the bot
./deploy-docker.sh --restart

# Stop the bot
./deploy-docker.sh --down

# Update the bot (after pulling new code)
./deploy-docker.sh  # Rebuilds and restarts
```

📖 **Complete Docker Documentation**: [Docker Deployment Guide](docs/docker-deployment-guide.md)

### Direct Python Deployment

**Best for**: Development, testing, or when Docker is not available

#### Prerequisites
- Python 3.8+
- pip
- Stable network connection

#### Detailed Steps

1. **System Preparation**
```bash
# Check Python version
python3 --version

# Check pip version
pip --version

# If needed, upgrade pip
pip install --upgrade pip
```

2. **Project Configuration**
```bash
# Clone the project
git clone https://github.com/yourusername/DND_DC_BOT.git
cd DND_DC_BOT

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

3. **Environment Variable Configuration**
```bash
# Copy configuration file
cp config_example.env .env

# Edit configuration file
nano .env
```

Configuration content:
```env
# Discord bot token (required)
DISCORD_TOKEN=your_discord_bot_token

# Gemini API key (optional, for AI scene generation)
GEMINI_API_KEY=your_gemini_api_key

# Log level (optional)
LOG_LEVEL=INFO

# Database file path (optional)
DATABASE_PATH=dnd_bot.db
```

4. **Start the Bot**
```bash
# Foreground start (development/debugging)
python3 main.py

# Background start (production environment)
nohup python3 main.py > bot.log 2>&1 &

# Check running status
ps aux | grep python3 | grep main.py

# View logs
tail -f bot.log
```

### Common Issue Resolution

**SSL Certificate Errors** 🔒:
```bash
# Recommended solution: Use Docker deployment
./deploy-docker.sh

# Alternative: Update system certificates (Linux)
sudo apt-get update
sudo apt-get install --reinstall ca-certificates

# Alternative: Update system certificates (macOS)
brew install openssl
```

**Dependency Installation Issues**:
```bash
# Clear pip cache
pip cache purge

# Reinstall dependencies
pip install -r requirements.txt --no-cache-dir

# If a specific package fails to install, install separately
pip install package_name
```

**Docker Issues**:
```bash
# Check Docker service status
sudo systemctl status docker

# Restart Docker service
sudo systemctl restart docker

# View detailed container logs
docker logs dnd-bot

# Rebuild from scratch
./deploy-docker.sh --down
docker system prune -a
./deploy-docker.sh
```

## 🔧 Development and Debugging

### Local Development Environment

1. **Development Environment Configuration**
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Enable development mode
export DEVELOPMENT=true
python3 main.py
```

2. **Debugging Commands**
```bash
# View detailed logs
tail -f logs/bot.log

# View error logs
tail -f logs/error.log

# Real-time monitoring
python3 -u main.py | tee console.log
```

### Database Management

```bash
# View database status
python3 -c "from database.database import DatabaseManager; print(DatabaseManager().get_database_stats())"

# Reset database
python3 setup_database.py

# Backup database
cp dnd_bot.db dnd_bot_backup.db
```

### API Testing

```bash
# Test Gemini API
python3 -c "from scene_generator import scene_generator; import asyncio; print(asyncio.run(scene_generator.generate_scene_description('A dark forest', 100, 'mysterious')))"
```

## 📊 Project Statistics

### Current Status
- **Version**: v1.4.0
- **Slash Commands**: 22
- **Core Modules**: 6
- **API Integrations**: 2 (D&D 5e SRD, Google Gemini)
- **Database Tables**: 15
- **Supported Features**: Dice, queries, combat, scene generation

### Feature Completion
- **Dice System**: 100% ✅
- **Query System**: 100% ✅
- **Combat System**: 100% ✅
- **Scene Generation**: 100% ✅
- **Character Management**: 0% ⏳
- **DM Tools**: 20% ⏳

### Technical Metrics
- **Response Time**: <2 seconds
- **API Cache**: 1 hour
- **Database**: SQLite running stably
- **Memory Usage**: <200MB (direct) / <250MB (Docker)
- **Docker Image Size**: ~450MB
- **Deployment Methods**: 2 (Docker + Direct Python)

## 🤝 Contributing Guide

### How to Contribute

1. **Fork the project**
2. **Create a feature branch**
```bash
git checkout -b feature/new-feature
```

3. **Commit your changes**
```bash
git commit -m "Add new feature"
```

4. **Push to the branch**
```bash
git push origin feature/new-feature
```

5. **Create a Pull Request**

### Development Standards

- **Code Style**: Follow PEP 8
- **Comments**: Key functions must have docstrings
- **Testing**: New features require tests
- **Documentation**: Update relevant documentation

### Bug Reports

If you find a bug, please create an Issue including:
- Error description
- Steps to reproduce
- Environment information
- Log files

## 📖 Documentation

### User Documentation
- **Quick Start**: This README
- **Command Reference**: See command tables above for complete usage

### Technical Information
- **Database**: SQLite with 15+ tables for game data
- **API Integration**: D&D 5e SRD API and Google Gemini API
- **Architecture**: Modular command system with async operations

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🎮 Changelog

### v1.5.0 (2025-11-24) 🐳
- **Docker Support**: Complete containerization implementation
  - Dockerfile with Python 3.11 and optimized SSL support
  - Docker Compose orchestration with volume persistence
  - Deployment management script with easy commands
  - Comprehensive Docker deployment documentation
  - Automatic SSL certificate handling
  - Resolves network connectivity issues
- **Deployment Options**: Both Docker and direct Python methods supported
- **Documentation Updates**: Enhanced README with deployment comparison
- **Production Ready**: Automatic restart, log persistence, database backup

### v1.4.0 (2025-07-10) 🎭
- **AI Scene Generator**: Integrated Google Gemini API
  - Support for custom style keywords (horror, romantic, humorous, epic, etc.)
  - Flexible length control (50-500 words)
  - Intelligent demo mode fallback
  - Perfect Chinese scene description generation
- **Custom Style System**: Breaking through preset limitations
  - 10 preset styles
  - Support for any custom style keywords
  - AI automatic style adaptation
  - Rich style example library
- **Feature Enhancement**: New scene generation command
  - Complete `/scene` command implementation
  - Parameter validation and error handling
  - Beautiful Discord embed messages
  - Detailed usage guide
- **Dependency Updates**: 
  - Added `google-genai>=1.25.0`
  - Updated requirements.txt

### v1.2.9 (2025-07-09) ⚡
- **Command Simplification**: `/roll` → `/r`, 87.5% less typing
- **Startup Issue Fixes**: Resolved multiple startup-related errors
- **SSL Connection Fixes**: Multi-layer SSL compatibility handling
- **Stability Improvements**: Bot running stably

### v1.2.8 (2025-07-07) ⚡
- **Command Simplification**: All commands changed to abbreviated forms
- **User Experience**: More convenient command operations
- **Documentation Updates**: Synchronized updates to all documentation

### v1.2.7 (2025-07-07) 🔧
- **Combat System Fixes**: Completely resolved database issues
- **Fully Functional**: All 8 combat commands working properly
- **Performance Optimization**: Database access optimization

## 🎯 Project Vision

Create the most comprehensive and user-friendly D&D Discord bot, making online tabletop gaming experiences smoother and more enjoyable. Enhance gameplay through AI technology, providing powerful assistance tools for DMs and players.

---

**Start your adventure!** 🎲✨

If you have questions or suggestions, feel free to create an Issue or contact the developer.