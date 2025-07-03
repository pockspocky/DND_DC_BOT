"""
D&D 5e API客户端
处理与D&D 5e SRD API的通信
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from .proxy_config import get_dnd_api_session

class DnDAPIClient:
    """D&D 5e API客户端"""
    
    BASE_URL = "https://www.dnd5eapi.co/api/2014"
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_timeout = 3600  # 1小时缓存
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """启动API客户端"""
        if not self.session:
            # 使用专用的代理配置创建会话
            self.session = get_dnd_api_session()
            self.logger.info("D&D API客户端已启动")
    
    async def close(self):
        """关闭API客户端"""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("D&D API客户端已关闭")
    
    def _get_cache_key(self, endpoint: str) -> str:
        """生成缓存键"""
        return f"dnd_api:{endpoint}"
    
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """检查缓存是否有效"""
        if not cached_data or 'timestamp' not in cached_data:
            return False
        
        cache_time = datetime.fromisoformat(cached_data['timestamp'])
        return datetime.now() - cache_time < timedelta(seconds=self.cache_timeout)
    
    async def _get(self, endpoint: str, max_retries: int = 3) -> Optional[Dict]:
        """通用GET请求方法"""
        if not self.session:
            await self.start()
        
        # 检查缓存
        cache_key = self._get_cache_key(endpoint)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            self.logger.debug(f"从缓存返回数据: {endpoint}")
            return self.cache[cache_key]['data']
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                if not self.session:
                    await self.start()
                
                async with self.session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 缓存数据
                        self.cache[cache_key] = {
                            'data': data,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.logger.debug(f"API请求成功: {endpoint}")
                        return data
                    
                    elif response.status == 404:
                        self.logger.warning(f"资源不存在: {endpoint}")
                        return None
                    
                    else:
                        self.logger.error(f"API错误: {response.status} - {endpoint}")
                        if response.status >= 500 and attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        return None
                        
            except aiohttp.ClientError as e:
                self.logger.error(f"请求错误: {e} - {endpoint}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            
            except asyncio.TimeoutError:
                self.logger.error(f"请求超时: {endpoint}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    async def get_spell(self, spell_name: str) -> Optional[Dict]:
        """获取法术信息"""
        spell_index = spell_name.lower().replace(' ', '-').replace("'", "")
        return await self._get(f"spells/{spell_index}")
    
    async def get_monster(self, monster_name: str) -> Optional[Dict]:
        """获取怪物信息"""
        monster_index = monster_name.lower().replace(' ', '-').replace("'", "")
        return await self._get(f"monsters/{monster_index}")
    
    async def get_skill(self, skill_name: str) -> Optional[Dict]:
        """获取技能信息"""
        skill_index = skill_name.lower().replace(' ', '-')
        return await self._get(f"skills/{skill_index}")
    
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
    
    async def get_magic_item(self, item_name: str) -> Optional[Dict]:
        """获取魔法物品信息"""
        item_index = item_name.lower().replace(' ', '-')
        return await self._get(f"magic-items/{item_index}")
    
    async def search_spells(self, query: str, limit: int = 5) -> Optional[Dict]:
        """搜索法术 - 获取法术列表"""
        return await self._get("spells")
    
    async def search_monsters(self, query: str, limit: int = 5) -> Optional[Dict]:
        """搜索怪物 - 获取怪物列表"""
        return await self._get("monsters")
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        self.logger.info("API缓存已清除") 