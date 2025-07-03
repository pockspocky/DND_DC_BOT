# D&D 5e SRD API 参考文档

本文档记录了D&D 5e SRD API的测试结果和使用指南，为Discord机器人项目提供API集成参考。

## 🌟 推荐API

**D&D 5e SRD API (5e-bits)**
- **基础URL**: `https://www.dnd5eapi.co/api/2014/`
- **文档**: https://5e-bits.github.io/docs/
- **GitHub**: https://github.com/5e-bits/5e-srd-api
- **特点**: 最活跃维护，完整文档，支持REST和GraphQL

## 📊 API端点测试结果

### 🎯 基础API端点

**获取所有可用端点**
```bash
GET https://www.dnd5eapi.co/api/2014/
```

**响应示例**:
```json
{
  "ability-scores": "/api/2014/ability-scores",
  "alignments": "/api/2014/alignments",
  "backgrounds": "/api/2014/backgrounds",
  "classes": "/api/2014/classes",
  "conditions": "/api/2014/conditions",
  "damage-types": "/api/2014/damage-types",
  "equipment": "/api/2014/equipment",
  "equipment-categories": "/api/2014/equipment-categories",
  "feats": "/api/2014/feats",
  "features": "/api/2014/features",
  "languages": "/api/2014/languages",
  "magic-items": "/api/2014/magic-items",
  "magic-schools": "/api/2014/magic-schools",
  "monsters": "/api/2014/monsters",
  "proficiencies": "/api/2014/proficiencies",
  "races": "/api/2014/races",
  "rule-sections": "/api/2014/rule-sections",
  "rules": "/api/2014/rules",
  "skills": "/api/2014/skills",
  "spells": "/api/2014/spells",
  "subclasses": "/api/2014/subclasses",
  "subraces": "/api/2014/subraces",
  "traits": "/api/2014/traits",
  "weapon-properties": "/api/2014/weapon-properties"
}
```

### ✨ 法术API (Spells)

**端点**: `GET /api/2014/spells/{spell-index}`

**测试用例**: 火球术 (Fireball)
```bash
GET https://www.dnd5eapi.co/api/2014/spells/fireball
```

**响应结构**:
```json
{
  "index": "fireball",
  "name": "Fireball",
  "desc": [
    "A bright streak flashes from your pointing finger to a point you choose within range..."
  ],
  "higher_level": [
    "When you cast this spell using a spell slot of 4th level or higher..."
  ],
  "range": "150 feet",
  "components": ["V", "S", "M"],
  "material": "A tiny ball of bat guano and sulfur.",
  "ritual": false,
  "duration": "Instantaneous",
  "concentration": false,
  "casting_time": "1 action",
  "level": 3,
  "damage": {
    "damage_type": {
      "index": "fire",
      "name": "Fire",
      "url": "/api/2014/damage-types/fire"
    },
    "damage_at_slot_level": {
      "3": "8d6",
      "4": "9d6",
      "5": "10d6",
      "6": "11d6",
      "7": "12d6",
      "8": "13d6",
      "9": "14d6"
    }
  },
  "dc": {
    "dc_type": {
      "index": "dex",
      "name": "DEX",
      "url": "/api/2014/ability-scores/dex"
    },
    "dc_success": "half"
  },
  "area_of_effect": {
    "type": "sphere",
    "size": 20
  },
  "school": {
    "index": "evocation",
    "name": "Evocation",
    "url": "/api/2014/magic-schools/evocation"
  },
  "classes": [
    {
      "index": "sorcerer",
      "name": "Sorcerer",
      "url": "/api/2014/classes/sorcerer"
    },
    {
      "index": "wizard",
      "name": "Wizard",
      "url": "/api/2014/classes/wizard"
    }
  ],
  "subclasses": [
    {
      "index": "lore",
      "name": "Lore",
      "url": "/api/2014/subclasses/lore"
    },
    {
      "index": "fiend",
      "name": "Fiend",
      "url": "/api/2014/subclasses/fiend"
    }
  ],
  "url": "/api/2014/spells/fireball",
  "updated_at": "2025-04-08T21:14:16.147Z"
}
```

**关键字段说明**:
- `damage_at_slot_level`: 不同法术位等级的伤害
- `dc`: 豁免检定信息
- `area_of_effect`: 影响区域
- `components`: 施法成分 (V=语言, S=姿势, M=材料)

### 🐉 怪物API (Monsters)

**端点**: `GET /api/2014/monsters/{monster-index}`

**测试用例**: 成年黑龙 (Adult Black Dragon)
```bash
GET https://www.dnd5eapi.co/api/2014/monsters/adult-black-dragon
```

**响应结构** (部分):
```json
{
  "index": "adult-black-dragon",
  "name": "Adult Black Dragon",
  "size": "Huge",
  "type": "dragon",
  "alignment": "chaotic evil",
  "armor_class": [
    {
      "type": "natural",
      "value": 19
    }
  ],
  "hit_points": 195,
  "hit_dice": "17d12",
  "hit_points_roll": "17d12+85",
  "speed": {
    "walk": "40 ft.",
    "fly": "80 ft.",
    "swim": "40 ft."
  },
  "strength": 23,
  "dexterity": 14,
  "constitution": 21,
  "intelligence": 14,
  "wisdom": 13,
  "charisma": 17,
  "proficiencies": [
    {
      "value": 7,
      "proficiency": {
        "index": "saving-throw-dex",
        "name": "Saving Throw: DEX",
        "url": "/api/2014/proficiencies/saving-throw-dex"
      }
    }
  ],
  "damage_immunities": ["acid"],
  "senses": {
    "blindsight": "60 ft.",
    "darkvision": "120 ft.",
    "passive_perception": 21
  },
  "languages": "Common, Draconic",
  "challenge_rating": 14,
  "proficiency_bonus": 5,
  "xp": 11500,
  "special_abilities": [
    {
      "name": "Amphibious",
      "desc": "The dragon can breathe air and water.",
      "damage": []
    }
  ]
}
```

**关键字段说明**:
- `hit_points_roll`: 生命值骰子表达式
- `proficiencies`: 豁免检定和技能加值
- `challenge_rating`: 挑战等级
- `special_abilities`: 特殊能力

### 🎭 职业API (Classes)

**端点**: `GET /api/2014/classes/{class-index}`

**测试用例**: 法师 (Wizard)
```bash
GET https://www.dnd5eapi.co/api/2014/classes/wizard
```

**响应结构** (部分):
```json
{
  "index": "wizard",
  "name": "Wizard",
  "hit_die": 6,
  "proficiency_choices": [
    {
      "desc": "Choose two from Arcana, History, Insight, Investigation, Medicine, and Religion",
      "choose": 2,
      "type": "proficiencies",
      "from": {
        "option_set_type": "options_array",
        "options": [
          {
            "option_type": "reference",
            "item": {
              "index": "skill-arcana",
              "name": "Skill: Arcana",
              "url": "/api/2014/proficiencies/skill-arcana"
            }
          }
        ]
      }
    }
  ],
  "proficiencies": [
    {
      "index": "daggers",
      "name": "Daggers",
      "url": "/api/2014/proficiencies/daggers"
    }
  ]
}
```

**关键字段说明**:
- `hit_die`: 生命骰类型
- `proficiency_choices`: 可选择的专精项
- `proficiencies`: 默认专精项

### ⚔️ 装备API (Equipment)

**端点**: `GET /api/2014/equipment/{equipment-index}`

**测试用例**: 长剑 (Longsword)
```bash
GET https://www.dnd5eapi.co/api/2014/equipment/longsword
```

**响应结构**:
```json
{
  "index": "longsword",
  "name": "Longsword",
  "equipment_category": {
    "index": "weapon",
    "name": "Weapon",
    "url": "/api/2014/equipment-categories/weapon"
  },
  "weapon_category": "Martial",
  "weapon_range": "Melee",
  "category_range": "Martial Melee",
  "cost": {
    "quantity": 15,
    "unit": "gp"
  },
  "damage": {
    "damage_dice": "1d8",
    "damage_type": {
      "index": "slashing",
      "name": "Slashing",
      "url": "/api/2014/damage-types/slashing"
    }
  },
  "range": {
    "normal": 5
  },
  "weight": 3,
  "properties": [
    {
      "index": "versatile",
      "name": "Versatile",
      "url": "/api/2014/weapon-properties/versatile"
    }
  ],
  "two_handed_damage": {
    "damage_dice": "1d10",
    "damage_type": {
      "index": "slashing",
      "name": "Slashing",
      "url": "/api/2014/damage-types/slashing"
    }
  },
  "url": "/api/2014/equipment/longsword",
  "updated_at": "2025-04-08T21:13:58.828Z"
}
```

**关键字段说明**:
- `damage`: 主手伤害
- `two_handed_damage`: 双手伤害 (如果有)
- `properties`: 武器属性
- `weapon_category`: 武器分类 (Simple/Martial)

### 🧝 种族API (Races)

**端点**: `GET /api/2014/races/{race-index}`

**测试用例**: 精灵 (Elf)
```bash
GET https://www.dnd5eapi.co/api/2014/races/elf
```

**响应结构** (部分):
```json
{
  "index": "elf",
  "name": "Elf",
  "speed": 30,
  "ability_bonuses": [
    {
      "ability_score": {
        "index": "dex",
        "name": "DEX",
        "url": "/api/2014/ability-scores/dex"
      },
      "bonus": 2
    }
  ],
  "age": "Although elves reach physical maturity at about the same age as humans...",
  "alignment": "Elves love freedom, variety, and self-expression...",
  "size": "Medium",
  "size_description": "Elves range from under 5 to over 6 feet tall...",
  "starting_proficiencies": [
    {
      "index": "skill-perception",
      "name": "Skill: Perception",
      "url": "/api/2014/proficiencies/skill-perception"
    }
  ],
  "languages": [
    {
      "index": "common",
      "name": "Common",
      "url": "/api/2014/languages/common"
    },
    {
      "index": "elvish",
      "name": "Elvish",
      "url": "/api/2014/languages/elvish"
    }
  ],
  "traits": [
    {
      "index": "darkvision",
      "name": "Darkvision",
      "url": "/api/2014/traits/darkvision"
    }
  ]
}
```

**关键字段说明**:
- `ability_bonuses`: 属性加值
- `starting_proficiencies`: 初始专精
- `traits`: 种族特质

### 🎯 技能API (Skills)

**端点**: `GET /api/2014/skills/{skill-index}`

**测试用例**: 察觉 (Perception)
```bash
GET https://www.dnd5eapi.co/api/2014/skills/perception
```

**响应结构**:
```json
{
  "index": "perception",
  "name": "Perception",
  "desc": [
    "Your Wisdom (Perception) check lets you spot, hear, or otherwise detect the presence of something..."
  ],
  "ability_score": {
    "index": "wis",
    "name": "WIS",
    "url": "/api/2014/ability-scores/wis"
  },
  "url": "/api/2014/skills/perception",
  "updated_at": "2025-04-08T21:14:15.880Z"
}
```

### ✨ 魔法物品API (Magic Items)

**端点**: `GET /api/2014/magic-items/{item-index}`

**测试用例**: 精金护甲 (Adamantine Armor)
```bash
GET https://www.dnd5eapi.co/api/2014/magic-items/adamantine-armor
```

**响应结构**:
```json
{
  "index": "adamantine-armor",
  "name": "Adamantine Armor",
  "equipment_category": {
    "index": "armor",
    "name": "Armor",
    "url": "/api/2014/equipment-categories/armor"
  },
  "rarity": {
    "name": "Uncommon"
  },
  "variants": [],
  "variant": false,
  "desc": [
    "Armor (medium or heavy, but not hide), uncommon",
    "This suit of armor is reinforced with adamantine..."
  ],
  "image": "/api/images/magic-items/adamantine-armor.png",
  "url": "/api/2014/magic-items/adamantine-armor",
  "updated_at": "2025-05-04T02:15:01.647Z"
}
```

## 🚀 Discord机器人集成建议

### 1. 法术查询功能
```python
async def get_spell_info(spell_name):
    url = f"https://www.dnd5eapi.co/api/2014/spells/{spell_name.lower().replace(' ', '-')}"
    # 处理API调用和响应
```

### 2. 怪物查询功能
```python
async def get_monster_info(monster_name):
    url = f"https://www.dnd5eapi.co/api/2014/monsters/{monster_name.lower().replace(' ', '-')}"
    # 包含战斗相关数据: HP, AC, 攻击, 豁免检定等
```

### 3. 角色创建助手
```python
async def get_race_info(race_name):
    url = f"https://www.dnd5eapi.co/api/2014/races/{race_name.lower()}"
    # 获取种族属性加值和特质

async def get_class_info(class_name):
    url = f"https://www.dnd5eapi.co/api/2014/classes/{class_name.lower()}"
    # 获取职业专精和生命骰信息
```

### 4. 装备查询功能
```python
async def get_equipment_info(item_name):
    url = f"https://www.dnd5eapi.co/api/2014/equipment/{item_name.lower().replace(' ', '-')}"
    # 武器伤害、护甲AC、价格等信息
```

## 📝 实现优先级

### 高优先级 (立即实现)
1. **法术查询** - 最常用功能，数据结构完整
2. **怪物查询** - DM工具，包含战斗数据
3. **技能查询** - 配合现有检定功能

### 中优先级 (后续实现)
4. **装备查询** - 角色管理相关
5. **种族/职业查询** - 角色创建助手
6. **魔法物品查询** - 进阶功能

### 低优先级 (可选实现)
7. **规则查询** - 参考功能
8. **条件查询** - 战斗辅助

## 🔧 错误处理

### 常见错误码
- `404`: 资源未找到 (拼写错误或不存在)
- `500`: 服务器错误
- `Rate Limiting`: API调用限制

### 建议处理策略
```python
import aiohttp
import asyncio

async def safe_api_call(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None  # 资源不存在
                    else:
                        raise aiohttp.ClientError(f"HTTP {response.status}")
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2 ** attempt)  # 指数退避
```

## 📊 性能优化建议

### 1. 缓存策略
- 本地缓存常用查询 (法术、怪物)
- 设置合理的过期时间 (24小时)

### 2. 批量预加载
- 预加载基础数据 (技能列表、属性列表)
- 启动时缓存高频查询项

### 3. 异步处理
- 所有API调用使用异步函数
- 避免阻塞Discord响应

## 📅 集成时间表

### Week 1-2: 基础查询功能
- [x] API测试和文档编写
- [ ] 法术查询命令实现
- [ ] 基础错误处理

### Week 3-4: 扩展功能
- [ ] 怪物查询命令
- [ ] 技能查询命令
- [ ] 缓存系统实现

### Week 5-6: 高级功能
- [ ] 装备查询命令
- [ ] 种族/职业查询
- [ ] 性能优化

---

*文档更新日期: 2025年7月3日*
*API测试完成，数据结构验证通过，可开始集成开发* 