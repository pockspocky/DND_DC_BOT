"""
代理配置管理
为D&D API和Discord API提供独立的代理配置
"""

import os
import aiohttp
import logging

logger = logging.getLogger(__name__)

def get_dnd_api_session():
    """为D&D API创建专用会话（不使用代理）"""
    connector = aiohttp.TCPConnector(
        limit=30,
        limit_per_host=10,
        ttl_dns_cache=300,
        use_dns_cache=True,
    )
    
    return aiohttp.ClientSession(
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=30, connect=10),
        headers={
            'User-Agent': 'DND-Discord-Bot/1.2',
            'Accept': 'application/json'
        }
    ) 