# DND_DC_BOT - 龙与地下城Discord机器人

![Status](https://img.shields.io/badge/状态-稳定运行-green) ![Version](https://img.shields.io/badge/版本-v1.4.0-blue) ![Commands](https://img.shields.io/badge/斜杠命令-22个-orange) ![AI](https://img.shields.io/badge/AI-Gemini%20API-purple) ![Docker](https://img.shields.io/badge/Docker-支持-blue)

一个专为龙与地下城(D&D)游戏设计的Discord机器人，集成了AI场景生成、完整的游戏辅助功能和智能查询系统。

## 🆕 最新功能亮点

### 🎭 AI场景生成器 (NEW!)
- **Gemini AI驱动**: 使用Google Gemini API生成高质量场景描述
- **自定义风格**: 支持任意风格词汇（恐怖、浪漫、幽默、史诗、诗意等）
- **灵活长度**: 50-500字可调节
- **DM专用**: 为地下城主提供丰富的场景描述工具

### 🎲 完整游戏系统
- **22个斜杠命令**: 覆盖骰子、查询、战斗、场景生成等全套功能
- **智能缓存**: 优化的API响应速度
- **数据持久化**: SQLite数据库存储所有游戏数据
- **网络兼容**: 支持代理环境，解决连接问题

## 🚀 快速开始

### 🐳 Docker部署（推荐）
**Docker部署可以完美解决SSL连接问题，是推荐的部署方式**

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/DND_DC_BOT.git
cd DND_DC_BOT

# 2. 配置环境变量
cp docker.env.example .env
# 编辑.env文件，添加以下内容：
# DISCORD_TOKEN=your_discord_bot_token
# GEMINI_API_KEY=your_gemini_api_key
# PROXY_URL=http://127.0.0.1:7890  # 如果需要代理

# 3. 一键部署
chmod +x deploy-docker.sh
./deploy-docker.sh

# 4. 管理服务
./deploy-docker.sh --status   # 查看状态
./deploy-docker.sh --logs     # 查看日志
./deploy-docker.sh --restart  # 重启服务
./deploy-docker.sh --down     # 停止服务
```

### 🐍 传统部署

#### 前置要求
- Python 3.8+
- pip

#### 详细步骤
1. **克隆项目**
```bash
git clone https://github.com/yourusername/DND_DC_BOT.git
cd DND_DC_BOT
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
创建 `.env` 文件：
```env
DISCORD_TOKEN=your_discord_bot_token
PROXY_URL=http://127.0.0.1:7890  # 如果需要代理
```

4. **启动机器人**
```bash
# 直接启动（推荐）
python3 main.py

# 后台启动
nohup python3 main.py > bot.log 2>&1 &
```

#### 网络连接配置
如果你的网络环境需要代理访问Discord：

1. **确保代理服务运行**（如ClashX, V2Ray等）
2. **配置代理URL**：在`.env`文件中设置正确的代理地址
3. **测试连接**：
```bash
python3 check_connection.py
```

## 🎲 核心功能

### 🎭 AI场景生成器 ✨
使用Google Gemini API为DM提供智能场景描述生成

**命令**: `/scene`

**参数**:
- `description`: 英文场景描述
- `length`: 描述长度（50-500字，默认100）
- `style`: 风格词汇（支持任意自定义）

**支持的风格**:
- **预设风格**: 描述性、神秘、紧张、戏剧性、恐怖、浪漫、幽默、史诗、温馨、冒险
- **自定义风格**: 诗意、诡异、悲伤、威严、俏皮、古典、现代等任意词汇

**使用示例**:
```
/scene description:"A mysterious forest" length:120 style:"恐怖"
/scene description:"A romantic garden" length:100 style:"浪漫"
/scene description:"A funny tavern" length:150 style:"幽默"
/scene description:"A dark castle" length:80 style:"诡异"
```

### 🎲 骰子系统 ✅
完整的D&D骰子投掷系统

| 命令 | 描述 | 示例 |
|------|------|------|
| `/r` | 投掷骰子 | `/r dice:d20 modifier:5 advantage:优势` |
| `/check` | 技能检定 | `/check modifier:3 advantage:优势` |
| `/save` | 豁免检定 | `/save save_type:敏捷 modifier:2` |
| `/att` | 攻击检定 | `/att attack_bonus:5 damage_dice:1d8+3` |
| `/stats` | 角色属性生成 | `/stats method:4d6去最低` |
| `/rh` | 骰子帮助 | `/rh` |

**高级功能**:
- 优势/劣势投掷
- 多骰子投掷
- 保留/丢弃规则
- 复杂修正值计算
- 私密投掷模式

### 🔍 查询系统 ✅
完整的D&D 5e资源查询

| 命令 | 描述 | 示例 |
|------|------|------|
| `/sp` | 法术查询 | `/sp fireball` |
| `/mon` | 怪物查询 | `/mon goblin` |
| `/sk` | 技能查询 | `/sk perception` |

**特色功能**:
- 智能搜索匹配
- 详细信息展示
- 超长内容自动Thread展开
- 1小时智能缓存
- 友好的错误提示

### ⚔️ 战斗管理系统 ✅
完整的D&D战斗辅助工具

| 命令 | 描述 | 示例 |
|------|------|------|
| `/cs` | 开始战斗 | `/cs name:哥布林袭击` |
| `/ce` | 结束战斗 | `/ce` |
| `/st` | 战斗状态 | `/st` |
| `/add` | 添加参与者 | `/add name:哥布林 max_hp:7 initiative:12` |
| `/rm` | 移除参与者 | `/rm name:哥布林` |
| `/next` | 下一回合 | `/next` |
| `/dmg` | 造成伤害 | `/dmg target:哥布林 expression:1d6+2` |
| `/heal` | 治疗角色 | `/heal target:法师 expression:1d8+3` |

**战斗系统特色**:
- 先攻自动排序
- 回合制管理
- 生命值实时追踪
- 支持骰子表达式
- 多频道独立会话
- DM权限控制

### 🛠️ 基础工具
| 命令 | 描述 | 示例 |
|------|------|------|
| `/ping` | 测试响应 | `/ping` |
| `/help` | 帮助信息 | `/help` |
| `/dbstats` | 数据库统计 | `/dbstats` |
| `/echo` | 消息重复 | `/echo message:"测试"` |

## 🎯 `/r` 命令完整指南

### 基础用法
```
/r dice:d20                          # 投掷1个d20
/r dice:d6                           # 投掷1个d6
/r dice:d100                         # 投掷1个d100
```

### 带修正值
```
/r dice:d20 modifier:5               # 投掷d20+5
/r dice:d8 modifier:-2               # 投掷d8-2
```

### 优势/劣势投掷
```
/r dice:d20 advantage:优势           # 优势骰 (2d20取高)
/r dice:d20 advantage:劣势           # 劣势骰 (2d20取低)
/r dice:d20 advantage:优势 modifier:3 # 优势骰+3
```

### 多个骰子
```
/r dice:d6 count:3                   # 投掷3d6
/r dice:d8 count:2 modifier:4        # 投掷2d8+4
```

### 保留/丢弃规则
```
/r dice:d6 count:4 drop_lowest:1     # 4d6去最低 (D&D属性生成)
/r dice:d20 count:2 keep_highest:1   # 2d20保留最高
/r dice:d12 count:5 keep_highest:3 modifier:-1  # 5d12保留最高3个-1
```

### 复杂组合示例
```
/r dice:d8 count:3 modifier:2 private:true      # 3d8+2 (私密显示)
/r dice:d6 advantage:优势 modifier:4             # d6优势骰+4
```

## 🎭 场景生成器详细指南

### 基本使用
```
/scene description:"A dark forest path" style:"神秘"
```

### 风格选择
**预设风格**:
- `描述性`: 丰富的形容词和感官描述
- `神秘`: 营造神秘氛围和暗示
- `紧张`: 紧迫的语言和短句
- `戏剧性`: 戏剧化语言，增强情感冲击
- `恐怖`: 令人不安的描述和恐惧感
- `浪漫`: 优美诗意的语言
- `幽默`: 轻松幽默的描述
- `史诗`: 宏伟壮阔的语言
- `温馨`: 温暖亲切的氛围
- `冒险`: 充满活力的探索感

**自定义风格**:
- 可以使用任意风格词汇
- 如：`诗意`、`诡异`、`悲伤`、`威严`、`俏皮`等
- AI会根据词汇特征自动调整生成策略

### 长度控制
- **最小长度**: 50字
- **最大长度**: 500字
- **默认长度**: 100字
- **推荐长度**: 80-150字（适合朗读）

### 高级示例
```
/scene description:"An ancient library with floating books" length:150 style:"史诗"
/scene description:"A crowded marketplace" length:100 style:"幽默"
/scene description:"A haunted mansion" length:120 style:"恐怖"
/scene description:"A peaceful meadow" length:80 style:"诗意"
```

## 🛠️ 技术栈

- **Python 3.11**: 主要开发语言
- **discord.py**: Discord API库
- **Google Gemini API**: AI场景生成
- **SQLite**: 本地数据存储
- **python-dotenv**: 环境变量管理
- **Docker**: 容器化部署
- **Docker Compose**: 服务编排

## 🚀 部署详细指南

### 🐳 Docker部署（推荐）

#### 为什么选择Docker？
- **解决SSL问题**: 使用现代OpenSSL，完美兼容Discord API
- **环境一致性**: 避免Python版本和依赖冲突
- **简化部署**: 一键部署，无需手动配置
- **易于管理**: 统一的服务管理命令

#### 前置要求
- Docker 20.10+
- Docker Compose 1.29+

#### 详细步骤

1. **环境准备**
```bash
# 检查Docker版本
docker --version
docker-compose --version

# 如果未安装，请先安装Docker
# macOS: brew install docker docker-compose
# Ubuntu: sudo apt-get install docker.io docker-compose
```

2. **项目部署**
```bash
# 克隆项目
git clone https://github.com/yourusername/DND_DC_BOT.git
cd DND_DC_BOT

# 配置环境变量
cp docker.env.example .env

# 编辑.env文件，添加必要配置
nano .env
```

3. **环境变量配置**
在`.env`文件中配置：
```env
# 必须配置
DISCORD_TOKEN=your_discord_bot_token

# 可选配置（如果需要代理）
PROXY_URL=http://127.0.0.1:7890

# 可选配置（Docker相关）
COMPOSE_PROJECT_NAME=dnd_dc_bot
```

4. **一键部署**
```bash
# 给脚本执行权限
chmod +x deploy-docker.sh

# 启动服务
./deploy-docker.sh

# 查看启动状态
./deploy-docker.sh --status
```

5. **服务管理**
```bash
# 查看日志
./deploy-docker.sh --logs

# 重启服务
./deploy-docker.sh --restart

# 停止服务
./deploy-docker.sh --down

# 更新服务
./deploy-docker.sh --update
```

#### Docker部署优势
- **稳定性**: 容器化运行，避免系统依赖问题
- **安全性**: 隔离运行环境，不影响主机系统
- **可维护性**: 统一的管理接口，便于维护
- **可扩展性**: 支持多实例部署

### 🐍 传统部署

#### 前置要求
- Python 3.8+
- pip
- 稳定的网络连接

#### 详细步骤

1. **系统准备**
```bash
# 检查Python版本
python3 --version

# 检查pip版本
pip --version

# 如果需要，升级pip
pip install --upgrade pip
```

2. **项目配置**
```bash
# 克隆项目
git clone https://github.com/yourusername/DND_DC_BOT.git
cd DND_DC_BOT

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

3. **环境变量配置**
```bash
# 复制配置文件
cp config_example.env .env

# 编辑配置文件
nano .env
```

配置内容：
```env
# Discord机器人令牌
DISCORD_TOKEN=your_discord_bot_token

# 代理配置（如果需要）
PROXY_URL=http://127.0.0.1:7890

# 日志级别
LOG_LEVEL=INFO

# 数据库文件路径
DATABASE_PATH=dnd_bot.db
```

4. **网络连接测试**
```bash
# 测试网络连接
python3 check_connection.py

# 如果显示连接失败，检查代理配置
```

5. **启动机器人**
```bash
# 前台启动（开发调试）
python3 main.py

# 后台启动（生产环境）
nohup python3 main.py > bot.log 2>&1 &

# 查看运行状态
ps aux | grep python3 | grep main.py

# 查看日志
tail -f bot.log
```

#### 常见问题解决

**SSL连接问题**:
```bash
# 检查OpenSSL版本
openssl version

# 如果版本过旧，考虑使用Docker部署
# 或者升级系统OpenSSL
```

**代理连接问题**:
```bash
# 测试代理连接
curl --proxy http://127.0.0.1:7890 https://discord.com/api/v10/gateway

# 检查代理端口
lsof -i :7890

# 确认代理软件运行状态
```

**依赖安装问题**:
```bash
# 清理pip缓存
pip cache purge

# 重新安装依赖
pip install -r requirements.txt --no-cache-dir

# 如果某个包安装失败，单独安装
pip install package_name
```

## 🔧 开发和调试

### 本地开发环境

1. **开发环境配置**
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 启用开发模式
export DEVELOPMENT=true
python3 main.py
```

2. **调试命令**
```bash
# 查看详细日志
tail -f logs/bot.log

# 查看错误日志
tail -f logs/error.log

# 实时监控
python3 -u main.py | tee console.log
```

### 数据库管理

```bash
# 查看数据库状态
python3 -c "from database.database import DatabaseManager; print(DatabaseManager().get_database_stats())"

# 重置数据库
python3 setup_database.py

# 备份数据库
cp dnd_bot.db dnd_bot_backup.db
```

### API测试

```bash
# 测试Gemini API
python3 -c "from scene_generator import scene_generator; import asyncio; print(asyncio.run(scene_generator.generate_scene_description('A dark forest', 100, '神秘')))"

# 测试Discord连接
python3 check_connection.py
```

## 📊 项目统计

### 当前状态
- **版本**: v1.4.0
- **斜杠命令**: 22个
- **核心模块**: 6个
- **API集成**: 2个（D&D 5e SRD, Google Gemini）
- **数据库表**: 15个
- **支持功能**: 骰子、查询、战斗、场景生成

### 功能完成度
- **骰子系统**: 100% ✅
- **查询系统**: 100% ✅
- **战斗系统**: 100% ✅
- **场景生成**: 100% ✅
- **角色管理**: 0% ⏳
- **DM工具**: 20% ⏳

### 技术指标
- **响应时间**: <2秒
- **API缓存**: 1小时
- **数据库**: SQLite稳定运行
- **内存使用**: <200MB
- **容器大小**: ~100MB

## 🤝 贡献指南

### 如何贡献

1. **Fork项目**
2. **创建功能分支**
```bash
git checkout -b feature/new-feature
```

3. **提交更改**
```bash
git commit -m "Add new feature"
```

4. **推送到分支**
```bash
git push origin feature/new-feature
```

5. **创建Pull Request**

### 开发规范

- **代码风格**: 遵循PEP 8
- **注释**: 关键函数必须有docstring
- **测试**: 新功能需要添加测试
- **文档**: 更新相关文档

### 错误报告

如果发现Bug，请创建Issue并包含：
- 错误描述
- 复现步骤
- 环境信息
- 日志文件

## 🌐 网络连接故障排除

### 常见错误

1. **Connection timeout**
```
Cannot connect to host discord.com:443
```

2. **SSL握手失败**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

3. **代理连接失败**
```
Cannot connect to proxy
```

### 解决方案

1. **检查代理设置**
```bash
# 确认代理运行
curl --proxy http://127.0.0.1:7890 https://google.com

# 检查端口占用
lsof -i :7890
```

2. **使用连接诊断工具**
```bash
python3 check_connection.py
```

3. **Docker部署（推荐）**
```bash
# Docker能解决大部分SSL问题
./deploy-docker.sh
```

## 📖 文档和资源

### 用户文档
- **快速开始**: 本README
- **命令指南**: [START_GUIDE.md](START_GUIDE.md)
- **查询使用**: [docs/query_usage_guide.md](docs/query_usage_guide.md)
- **战斗系统**: [docs/combat_system_guide.md](docs/combat_system_guide.md)

### 技术文档
- **API参考**: [docs/dnd_api_reference.md](docs/dnd_api_reference.md)
- **数据库设计**: [docs/database_schema.md](docs/database_schema.md)
- **Docker部署**: [docs/docker-deployment-guide.md](docs/docker-deployment-guide.md)

### 故障排除
- **连接问题**: [docs/troubleshooting.md](docs/troubleshooting.md)
- **安全配置**: [docs/security_guide.md](docs/security_guide.md)

## 📄 许可证

本项目采用MIT许可证，详情请查看[LICENSE](LICENSE)文件。

## 🎮 更新日志

### v1.4.0 (2025-07-10) 🎭
- **AI场景生成器**: 集成Google Gemini API
  - 支持自定义风格词汇（恐怖、浪漫、幽默、史诗等）
  - 灵活的长度控制（50-500字）
  - 智能演示模式回退
  - 完美的中文场景描述生成
- **自定义风格系统**: 突破预设限制
  - 10个预设风格
  - 支持任意自定义风格词汇
  - AI自动风格适应
  - 丰富的风格示例库
- **功能增强**: 新增场景生成命令
  - `/scene` 命令完整实现
  - 参数验证和错误处理
  - 美观的Discord嵌入消息
  - 详细的使用指南
- **依赖更新**: 
  - 新增 `google-genai>=1.25.0`
  - 更新 requirements.txt
- **文档全面更新**: 
  - 更新README反映所有新功能
  - 新增场景生成器使用指南
  - 改进部署说明

### v1.3.0 (2025-07-07) 🐳
- **Docker部署支持**: 完美解决SSL连接问题
  - 创建完整的Docker部署方案
  - 使用Python 3.11 + 现代OpenSSL
  - 提供一键部署脚本
  - 支持容器化服务管理
- **Docker配置文件**: 完整的容器化配置
- **版本升级**: 标志着容器化部署的完成

### v1.2.9 (2025-07-09) ⚡
- **命令简化**: `/roll` → `/r`，减少87.5%输入
- **启动问题修复**: 解决多个启动相关错误
- **SSL连接修复**: 多层SSL兼容性处理
- **稳定性提升**: 机器人稳定运行

### v1.2.8 (2025-07-07) ⚡
- **命令简化**: 所有命令改为简写形式
- **用户体验**: 更方便的命令操作
- **文档更新**: 同步更新所有文档

### v1.2.7 (2025-07-07) 🔧
- **战斗系统修复**: 彻底解决数据库问题
- **完全可用**: 所有8个战斗命令正常工作
- **性能优化**: 数据库访问优化

## 🎯 项目愿景

打造最全面、最易用的D&D Discord机器人，让线上跑团体验更加流畅有趣。通过AI技术增强游戏体验，为DM和玩家提供强大的辅助工具。

---

**开始您的冒险吧！** 🎲✨

如有问题或建议，欢迎创建Issue或联系开发者。