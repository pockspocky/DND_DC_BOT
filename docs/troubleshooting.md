# 故障排除指南

## 🛠️ 常见问题解决方案

### 查询命令错误

#### 问题1: 代理连接错误
**错误信息**: `ClientConnectorError: Cannot connect to host discord.com:443 ssl:default [None]`

**原因**: 代理设置影响了Discord API连接

**解决方案**:
1. **立即修复**: 禁用.env文件中的代理设置
   ```bash
   # 备份原始配置
   cp .env .env.backup
   
   # 注释掉代理设置
   sed -i 's/PROXY_URL=/#PROXY_URL=/' .env
   
   # 重新启动机器人
   python3 main.py
   ```

2. **手动修复**: 编辑 `.env` 文件
   ```env
   # 将这行：
   PROXY_URL=http://127.0.0.1:7890
   
   # 修改为：
   #PROXY_URL=http://127.0.0.1:7890
   ```

3. **恢复代理设置** (如果需要):
   ```bash
   # 恢复原始配置
   cp .env.backup .env
   ```

4. **最佳实践**: 使用选择性代理
   - 只为特定服务设置代理
   - 不要设置全局代理环境变量
   - 考虑使用不同的配置文件

#### 问题2: Discord连接超时
**错误信息**: `Connection timeout to host https://discord.com/api/v10/users/@me`

**原因**: 网络环境限制，无法直接访问Discord API

**解决方案**:
1. **使用代理**: 确保.env文件中有正确的代理设置
   ```env
   PROXY_URL=http://127.0.0.1:7890
   ```

2. **验证连接**: 运行诊断脚本
   ```bash
   python3 -c "
   import asyncio, aiohttp, os
   from dotenv import load_dotenv
   
   load_dotenv()
   async def test():
       proxy = os.getenv('PROXY_URL')
       async with aiohttp.ClientSession() as session:
           async with session.get('https://discord.com/api/v10/gateway', proxy=proxy) as r:
               print('✅ Discord连接成功' if r.status == 200 else '❌ 连接失败')
   asyncio.run(test())
   "
   ```

3. **网络环境方案**:
   - 检查代理服务是否正常运行
   - 尝试使用其他网络环境（如移动热点）
   - 确认防火墙没有阻止Discord连接

#### 问题3: API查询超时
**错误信息**: API查询命令无响应或超时

**解决方案**:
1. 检查网络连接
2. 验证D&D 5e API服务状态
3. 清除查询缓存: `/clearquerycache` (仅管理员)

#### 问题4: 法术/怪物未找到
**错误信息**: "未找到法术/怪物"

**解决方案**:
1. **检查拼写**: 确保使用正确的英文名称
2. **使用连字符**: 多单词名称用连字符连接
   - 正确: `animal-friendship`
   - 错误: `animal friendship`
3. **常见名称参考**:
   - 法术: `fireball`, `magic-missile`, `cure-wounds`
   - 怪物: `goblin`, `adult-black-dragon`, `owlbear`
   - 技能: `perception`, `stealth`, `investigation`

### 机器人启动问题

#### 问题1: Discord Token错误
**解决方案**:
1. 检查 `.env` 文件中的 `DISCORD_TOKEN`
2. 确保token有效且未过期
3. 重新生成token（如果需要）

#### 问题2: 数据库连接失败
**解决方案**:
1. 检查数据库文件权限
2. 确保SQLite可用
3. 删除损坏的数据库文件，重新启动

#### 问题3: 模块加载失败
**解决方案**:
1. 检查Python依赖: `pip install -r requirements.txt`
2. 验证文件结构完整性
3. 检查Python版本兼容性

## 🔍 调试技巧

### 1. 启用详细日志
修改 `main.py` 中的日志级别：
```python
logging.basicConfig(level=logging.DEBUG)
```

### 2. 测试单独功能
使用独立测试脚本验证功能：
```python
# 测试API连接
python3 docs/api_test_example.py

# 测试数据库
python3 setup_database.py
```

### 3. 检查网络连接
```bash
# 测试D&D API连接
curl "https://www.dnd5eapi.co/api/2014/spells/fireball"

# 测试Discord连接
ping discord.com
```

## 📋 问题报告清单

如果问题持续存在，请提供以下信息：

### 基本信息
- [ ] 操作系统版本
- [ ] Python版本
- [ ] 错误的完整堆栈跟踪
- [ ] 导致错误的具体命令

### 环境信息
- [ ] 是否使用代理
- [ ] 网络连接状态
- [ ] Discord机器人权限设置

### 复现步骤
- [ ] 详细的操作步骤
- [ ] 预期结果 vs 实际结果
- [ ] 是否能稳定复现

## 🚀 性能优化建议

### 1. 缓存管理
- 定期清理查询缓存（1小时自动过期）
- 避免频繁查询相同内容

### 2. 网络优化
- 使用稳定的网络连接
- 考虑使用CDN或代理加速

### 3. 资源管理
- 定期重启机器人释放内存
- 监控数据库大小和性能

## 📞 获取帮助

1. **查看日志**: 检查 `bot.log` 文件的详细错误信息
2. **查阅文档**: 
   - [使用指南](query_usage_guide.md)
   - [API参考](dnd_api_reference.md)
3. **社区支持**: 联系服务器管理员
4. **问题反馈**: 提交详细的问题报告

---
*最后更新: 2025年7月3日* 