"""
D&D 5e API Client
Handles communication with D&D 5e SRD API
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

class DnDAPIClient:
    """D&D 5e API Client"""
    
    BASE_URL = "https://www.dnd5eapi.co/api/2014"
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_timeout = 3600  # 1 hour cache
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start API client"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=30,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30, connect=10),
                headers={
                    'User-Agent': 'DND-Discord-Bot/1.2',
                    'Accept': 'application/json'
                }
            )
            self.logger.info("D&D API client started")
    
    async def close(self):
        """Close API client"""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("D&D API client closed")
    
    def _get_cache_key(self, endpoint: str) -> str:
        """Generate cache key"""
        return f"dnd_api:{endpoint}"
    
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """Check if cache is valid"""
        if not cached_data or 'timestamp' not in cached_data:
            return False
        
        cache_time = datetime.fromisoformat(cached_data['timestamp'])
        return datetime.now() - cache_time < timedelta(seconds=self.cache_timeout)
    
    async def _get(self, endpoint: str, max_retries: int = 3) -> Optional[Dict]:
        """Generic GET request method"""
        if not self.session:
            await self.start()
        
        # Check cache
        cache_key = self._get_cache_key(endpoint)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            self.logger.debug(f"Returning data from cache: {endpoint}")
            return self.cache[cache_key]['data']
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                if not self.session:
                    await self.start()
                
                async with self.session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Cache data
                        self.cache[cache_key] = {
                            'data': data,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.logger.debug(f"API request successful: {endpoint}")
                        return data
                    
                    elif response.status == 404:
                        self.logger.warning(f"Resource not found: {endpoint}")
                        return None
                    
                    else:
                        self.logger.error(f"API error: {response.status} - {endpoint}")
                        if response.status >= 500 and attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        return None
                        
            except aiohttp.ClientError as e:
                self.logger.error(f"Request error: {e} - {endpoint}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            
            except asyncio.TimeoutError:
                self.logger.error(f"Request timeout: {endpoint}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    async def get_spell(self, spell_name: str) -> Optional[Dict]:
        """Get spell information"""
        spell_index = spell_name.lower().replace(' ', '-').replace("'", "")
        return await self._get(f"spells/{spell_index}")
    
    async def get_monster(self, monster_name: str) -> Optional[Dict]:
        """Get monster information"""
        monster_index = monster_name.lower().replace(' ', '-').replace("'", "")
        return await self._get(f"monsters/{monster_index}")
    
    async def get_skill(self, skill_name: str) -> Optional[Dict]:
        """Get skill information"""
        skill_index = skill_name.lower().replace(' ', '-')
        return await self._get(f"skills/{skill_index}")
    
    async def get_class(self, class_name: str) -> Optional[Dict]:
        """Get class information"""
        class_index = class_name.lower()
        return await self._get(f"classes/{class_index}")
    
    async def get_race(self, race_name: str) -> Optional[Dict]:
        """Get race information"""
        race_index = race_name.lower()
        return await self._get(f"races/{race_index}")
    
    async def get_equipment(self, item_name: str) -> Optional[Dict]:
        """Get equipment information"""
        item_index = item_name.lower().replace(' ', '-')
        return await self._get(f"equipment/{item_index}")
    
    async def get_magic_item(self, item_name: str) -> Optional[Dict]:
        """Get magic item information"""
        item_index = item_name.lower().replace(' ', '-')
        return await self._get(f"magic-items/{item_index}")
    
    async def search_spells(self, query: str, limit: int = 5) -> Optional[Dict]:
        """Search spells - get spell list"""
        return await self._get("spells")
    
    async def search_monsters(self, query: str, limit: int = 5) -> Optional[Dict]:
        """Search monsters - get monster list"""
        return await self._get("monsters")
    
    def clear_cache(self):
        """Clear cache"""
        self.cache.clear()
        self.logger.info("API cache cleared") 