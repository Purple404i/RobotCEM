import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any
import aioredis
import os

class CacheManager:
    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = None
        self.ttl_seconds = {
            'component': 21600,     # 6 hours
            'material': 86400,      # 24 hours
            'specification': 3600,  # 1 hour
        }
    
    async def connect(self):
        self.redis = await aioredis.create_redis_pool(os.getenv('REDIS_URL', 'redis://localhost'))
    
    async def disconnect(self):
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
    
    def _make_key(self, category: str, identifier: str) -> str:
        """Create cache key with hash"""
        key_str = f"{category}:{identifier}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get(self, category: str, identifier: str) -> Optional[Any]:
        """Get cached value"""
        if not self.redis:
            return None
        
        key = self._make_key(category, identifier)
        value = await self.redis.get(key)
        
        if value:
            return json.loads(value)
        return None
    
    async def set(self, category: str, identifier: str, value: Any):
        """Set cached value with TTL"""
        if not self.redis:
            return
        
        key = self._make_key(category, identifier)
        ttl = self.ttl_seconds.get(category, 3600)
        
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )
    
    async def delete(self, category: str, identifier: str):
        """Delete cached value"""
        if not self.redis:
            return
        
        key = self._make_key(category, identifier)
        await self.redis.delete(key)

cache = CacheManager()
