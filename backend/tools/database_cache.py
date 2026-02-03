"""
Advanced Caching Layer for Tool Results

Supports JSON storage with TTL, built on SQLAlchemy.
Can be extended to use Scylla DB for distributed caching.
"""

import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import asyncio
from enum import Enum

from sqlalchemy import Column, String, JSON, DateTime, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, event
import sqlalchemy

logger = logging.getLogger(__name__)

Base = declarative_base()


class CacheEntry(Base):
    """Database model for cached tool results."""
    __tablename__ = "tool_cache"
    
    key = Column(String(256), primary_key=True, index=True)
    value = Column(JSON)  # Stores any JSON-serializable data
    result_type = Column(String(50))  # 'product_price', 'material_price', etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, index=True)
    hit_count = Column(Integer, default=0)
    source = Column(String(100))  # Where the data came from
    confidence = Column(String(20), default='medium')  # high, medium, low
    
    __table_args__ = (
        Index('idx_result_type_expires', 'result_type', 'expires_at'),
    )


class CacheStoreBackend(ABC):
    """Abstract base for cache storage backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict]:
        """Retrieve cached value."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Dict, ttl: int = 3600) -> bool:
        """Store value with TTL (in seconds)."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cached value."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    async def clear_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        pass


class SQLAlchemyCacheStore(CacheStoreBackend):
    """SQLAlchemy-based cache store (supports SQLite, PostgreSQL, etc.)."""
    
    def __init__(self, database_url: str = "sqlite:///./tool_cache.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
        # Enable JSON support for SQLite
        if 'sqlite' in database_url:
            @event.listens_for(self.engine, "connect")
            def load_spatialite(dbapi_conn, connection_record):
                dbapi_conn.enable_load_extension(True)
        
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    async def get(self, key: str) -> Optional[Dict]:
        """Retrieve cached value if not expired."""
        try:
            session: Session = self.SessionLocal()
            entry = session.query(CacheEntry).filter(
                CacheEntry.key == key,
                CacheEntry.expires_at > datetime.utcnow()
            ).first()
            
            if entry:
                # Update hit count
                entry.hit_count += 1
                session.commit()
                
                result = entry.value.copy() if entry.value else {}
                result['_cache_metadata'] = {
                    'cached_at': entry.created_at.isoformat(),
                    'hits': entry.hit_count,
                    'source': entry.source,
                    'confidence': entry.confidence
                }
                
                return result
            
            return None
        
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None
        
        finally:
            session.close()
    
    async def set(
        self,
        key: str,
        value: Dict,
        ttl: int = 3600,
        result_type: str = 'general',
        source: str = 'unknown',
        confidence: str = 'medium'
    ) -> bool:
        """Store value with TTL."""
        try:
            session: Session = self.SessionLocal()
            
            # Remove metadata before storing
            store_value = value.copy()
            store_value.pop('_cache_metadata', None)
            
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            # Try to update existing entry
            entry = session.query(CacheEntry).filter(CacheEntry.key == key).first()
            
            if entry:
                entry.value = store_value
                entry.expires_at = expires_at
                entry.result_type = result_type
                entry.source = source
                entry.confidence = confidence
                entry.hit_count = 0
            else:
                entry = CacheEntry(
                    key=key,
                    value=store_value,
                    result_type=result_type,
                    created_at=datetime.utcnow(),
                    expires_at=expires_at,
                    source=source,
                    confidence=confidence
                )
                session.add(entry)
            
            session.commit()
            logger.debug(f"Cached {result_type} for key: {key[:50]}...")
            return True
        
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
        
        finally:
            session.close()
    
    async def delete(self, key: str) -> bool:
        """Delete cached value."""
        try:
            session: Session = self.SessionLocal()
            session.query(CacheEntry).filter(CacheEntry.key == key).delete()
            session.commit()
            return True
        
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
        
        finally:
            session.close()
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        try:
            session: Session = self.SessionLocal()
            exists = session.query(CacheEntry).filter(
                CacheEntry.key == key,
                CacheEntry.expires_at > datetime.utcnow()
            ).first() is not None
            return exists
        
        except Exception as e:
            logger.error(f"Cache exists check error: {e}")
            return False
        
        finally:
            session.close()
    
    async def clear_expired(self) -> int:
        """Remove expired entries."""
        try:
            session: Session = self.SessionLocal()
            count = session.query(CacheEntry).filter(
                CacheEntry.expires_at <= datetime.utcnow()
            ).delete()
            session.commit()
            logger.info(f"Cleared {count} expired cache entries")
            return count
        
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
        
        finally:
            session.close()
    
    async def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        try:
            session: Session = self.SessionLocal()
            
            total = session.query(CacheEntry).count()
            by_type = {}
            total_hits = 0
            
            for result_type, in session.query(CacheEntry.result_type).distinct():
                count = session.query(CacheEntry).filter(
                    CacheEntry.result_type == result_type
                ).count()
                hits = session.query(CacheEntry).filter(
                    CacheEntry.result_type == result_type
                ).with_entities(sqlalchemy.func.sum(CacheEntry.hit_count)).scalar() or 0
                
                by_type[result_type] = {
                    'entries': count,
                    'hits': hits
                }
                total_hits += hits
            
            return {
                'total_entries': total,
                'total_hits': total_hits,
                'by_type': by_type,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}
        
        finally:
            session.close()


class RedisCacheStore(CacheStoreBackend):
    """Redis-based cache store (optional, for high-performance caching)."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            import redis
            self.redis = redis.from_url(redis_url)
            self.redis.ping()
            logger.info("✓ Redis cache initialized")
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self.redis = None
    
    async def get(self, key: str) -> Optional[Dict]:
        """Retrieve from Redis."""
        if not self.redis:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Dict,
        ttl: int = 3600,
        **kwargs
    ) -> bool:
        """Store in Redis with TTL."""
        if not self.redis:
            return False
        
        try:
            self.redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete from Redis."""
        if not self.redis:
            return False
        
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self.redis:
            return False
        
        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists check error: {e}")
            return False
    
    async def clear_expired(self) -> int:
        """Redis automatically expires keys, so just return 0."""
        return 0


class CacheStore:
    """
    High-level cache store interface.
    
    Automatically selects best backend and implements fallback.
    """
    
    def __init__(
        self,
        primary_backend: CacheStoreBackend = None,
        fallback_backend: CacheStoreBackend = None,
        database_url: str = "sqlite:///./tool_cache.db"
    ):
        # Try to use Redis as primary if available
        if primary_backend is None:
            try:
                primary_backend = RedisCacheStore()
            except:
                primary_backend = SQLAlchemyCacheStore(database_url)
        
        # Fallback to SQLAlchemy
        if fallback_backend is None:
            fallback_backend = SQLAlchemyCacheStore(database_url)
        
        self.primary = primary_backend
        self.fallback = fallback_backend
    
    async def get(self, key: str) -> Optional[Dict]:
        """Retrieve from primary, fallback to secondary."""
        result = await self.primary.get(key)
        if result is None and self.fallback:
            result = await self.fallback.get(key)
        return result
    
    async def set(
        self,
        key: str,
        value: Dict,
        ttl: int = 3600,
        **kwargs
    ) -> bool:
        """Store in both caches."""
        primary_success = await self.primary.set(key, value, ttl, **kwargs)
        if self.fallback:
            await self.fallback.set(key, value, ttl, **kwargs)
        return primary_success
    
    async def delete(self, key: str) -> bool:
        """Delete from both caches."""
        primary_result = await self.primary.delete(key)
        if self.fallback:
            await self.fallback.delete(key)
        return primary_result
    
    async def exists(self, key: str) -> bool:
        """Check if exists in either cache."""
        return (
            await self.primary.exists(key) or
            (await self.fallback.exists(key) if self.fallback else False)
        )
    
    async def clear_expired(self) -> int:
        """Clear expired entries."""
        count = await self.primary.clear_expired()
        if self.fallback:
            count += await self.fallback.clear_expired()
        return count


# Global cache store instance
_cache_store = None


def get_cache_store(
    database_url: str = "sqlite:///./tool_cache.db"
) -> CacheStore:
    """Get or create the global cache store."""
    global _cache_store
    if _cache_store is None:
        _cache_store = CacheStore(database_url=database_url)
    return _cache_store
