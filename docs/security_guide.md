# 安全配置指南

## 🔒 重要安全提醒

### ⚠️ 敏感信息保护

**绝对不要将以下文件提交到Git仓库：**
- `.env` - 环境变量配置文件
- `.env.*` - 任何环境变量相关文件
- `config.json` - 可能包含敏感配置
- 任何包含API密钥、Token、密码的文件

### 📋 安全检查清单

#### 1. 环境变量配置
```bash
# ✅ 正确：使用.env文件（已在.gitignore中）
DISCORD_TOKEN=your_token_here
PROXY_URL=http://127.0.0.1:7890

# ❌ 错误：直接在代码中硬编码
bot = discord.Client(token="MTM4OTg4NDkyMjYxMjY3ODY4Nw...")
```

#### 2. .gitignore 配置检查
确保以下文件类型被忽略：
```gitignore
# 环境变量文件
.env
.env.*
.env.local
.env.backup
config.json

# 数据库文件（可能包含敏感数据）
*.db
*.sqlite
*.sqlite3

# 日志文件（可能包含敏感信息）
*.log
logs/
```

## 🚨 意外泄露的应急处理

### 如果敏感信息被误提交：

#### 步骤1：立即从Git历史中移除
```bash
# 从所有提交历史中移除敏感文件
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch <sensitive_file>' \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（警告：这会重写Git历史）
git push --force origin <branch>
```

#### 步骤2：更换所有泄露的凭据
- 重新生成Discord Bot Token
- 更换所有API密钥
- 修改所有相关密码

## 🛡️ 预防措施

### 1. 使用环境变量
```python
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ 安全的方式
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN未设置")
```

### 2. 配置文件模板
提供配置文件示例，但不包含真实数据：
```bash
# config_example.env
DISCORD_TOKEN=your_discord_token_here
PROXY_URL=http://127.0.0.1:7890
PREFIX=/
```

---

**记住：安全是开发的首要任务！**
