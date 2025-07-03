#!/usr/bin/env python3
"""
D&D 5e API 测试示例
演示如何使用D&D 5e SRD API进行数据查询
"""

import aiohttp
import asyncio
import json
from typing import Dict, Optional, List

class DnDAPI:
    """D&D 5e API 客户端"""
    
    BASE_URL = "https://www.dnd5eapi.co/api/2014"
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _get(self, endpoint: str) -> Optional[Dict]:
        """通用GET请求方法"""
        if not self.session:
            raise RuntimeError("请使用 async with 语法")
        
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    print(f"❌ 资源不存在: {endpoint}")
                    return None
                else:
                    print(f"❌ API错误: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None
    
    async def get_spell(self, spell_name: str) -> Optional[Dict]:
        """获取法术信息"""
        spell_index = spell_name.lower().replace(' ', '-')
        return await self._get(f"spells/{spell_index}")
    
    async def get_monster(self, monster_name: str) -> Optional[Dict]:
        """获取怪物信息"""
        monster_index = monster_name.lower().replace(' ', '-')
        return await self._get(f"monsters/{monster_index}")
    
    async def get_class(self, class_name: str) -> Optional[Dict]:
        """获取职业信息"""
        class_index = class_name.lower()
        return await self._get(f"classes/{class_index}")
    
    async def get_race(self, race_name: str) -> Optional[Dict]:
        """获取种族信息"""
        race_index = race_name.lower()
        return await self._get(f"races/{race_index}")
    
    async def get_equipment(self, item_name: str) -> Optional[Dict]:
        """获取装备信息"""
        item_index = item_name.lower().replace(' ', '-')
        return await self._get(f"equipment/{item_index}")
    
    async def get_skill(self, skill_name: str) -> Optional[Dict]:
        """获取技能信息"""
        skill_index = skill_name.lower()
        return await self._get(f"skills/{skill_index}")
    
    async def get_magic_item(self, item_name: str) -> Optional[Dict]:
        """获取魔法物品信息"""
        item_index = item_name.lower().replace(' ', '-')
        return await self._get(f"magic-items/{item_index}")

def print_spell_info(spell_data: Dict):
    """打印法术信息"""
    print(f"📜 {spell_data['name']} (等级 {spell_data['level']})")
    print(f"   学派: {spell_data['school']['name']}")
    print(f"   施法时间: {spell_data['casting_time']}")
    print(f"   射程: {spell_data['range']}")
    print(f"   持续时间: {spell_data['duration']}")
    print(f"   成分: {', '.join(spell_data['components'])}")
    
    if spell_data.get('damage'):
        damage = spell_data['damage']
        if 'damage_at_slot_level' in damage:
            print(f"   伤害: {damage['damage_at_slot_level']['3']} {damage['damage_type']['name']}")
    
    print(f"   描述: {spell_data['desc'][0][:100]}...")

def print_monster_info(monster_data: Dict):
    """打印怪物信息"""
    print(f"🐉 {monster_data['name']} (CR {monster_data['challenge_rating']})")
    print(f"   体型: {monster_data['size']} {monster_data['type']}")
    print(f"   阵营: {monster_data['alignment']}")
    print(f"   AC: {monster_data['armor_class'][0]['value']}")
    print(f"   HP: {monster_data['hit_points']} ({monster_data['hit_points_roll']})")
    print(f"   速度: {monster_data['speed'].get('walk', 'N/A')}")
    print(f"   属性: STR {monster_data['strength']} DEX {monster_data['dexterity']} CON {monster_data['constitution']}")
    print(f"   经验值: {monster_data['xp']} XP")

def print_class_info(class_data: Dict):
    """打印职业信息"""
    print(f"⚔️ {class_data['name']}")
    print(f"   生命骰: d{class_data['hit_die']}")
    
    if class_data.get('proficiencies'):
        prof_names = [prof['name'] for prof in class_data['proficiencies'][:3]]
        print(f"   专精: {', '.join(prof_names)}...")

def print_equipment_info(equipment_data: Dict):
    """打印装备信息"""
    print(f"⚔️ {equipment_data['name']}")
    print(f"   类型: {equipment_data['equipment_category']['name']}")
    
    if equipment_data.get('cost'):
        cost = equipment_data['cost']
        print(f"   价格: {cost['quantity']} {cost['unit']}")
    
    if equipment_data.get('damage'):
        damage = equipment_data['damage']
        print(f"   伤害: {damage['damage_dice']} {damage['damage_type']['name']}")
    
    if equipment_data.get('weight'):
        print(f"   重量: {equipment_data['weight']} 磅")

async def main():
    """主测试函数"""
    print("🎲 D&D 5e API 测试开始\n")
    
    async with DnDAPI() as api:
        
        # 测试法术查询
        print("=== 法术查询测试 ===")
        spell_data = await api.get_spell("fireball")
        if spell_data:
            print_spell_info(spell_data)
        print()
        
        # 测试怪物查询
        print("=== 怪物查询测试 ===")
        monster_data = await api.get_monster("adult-black-dragon")
        if monster_data:
            print_monster_info(monster_data)
        print()
        
        # 测试职业查询
        print("=== 职业查询测试 ===")
        class_data = await api.get_class("wizard")
        if class_data:
            print_class_info(class_data)
        print()
        
        # 测试装备查询
        print("=== 装备查询测试 ===")
        equipment_data = await api.get_equipment("longsword")
        if equipment_data:
            print_equipment_info(equipment_data)
        print()
        
        # 测试技能查询
        print("=== 技能查询测试 ===")
        skill_data = await api.get_skill("perception")
        if skill_data:
            print(f"🎯 {skill_data['name']} ({skill_data['ability_score']['name']})")
            print(f"   描述: {skill_data['desc'][0][:100]}...")
        print()
        
        # 测试魔法物品查询
        print("=== 魔法物品查询测试 ===")
        magic_item_data = await api.get_magic_item("adamantine-armor")
        if magic_item_data:
            print(f"✨ {magic_item_data['name']} ({magic_item_data['rarity']['name']})")
            print(f"   类型: {magic_item_data['equipment_category']['name']}")
            print(f"   描述: {magic_item_data['desc'][0][:100]}...")
        print()
        
        print("✅ 测试完成！")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main()) 