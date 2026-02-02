from fastapi import HTTPException, Request
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            'generate': (10, 3600),  # 10 requests per hour
            'status': (100, 60),     # 100 requests per minute
            'default': (1000, 3600)  # 1000 requests per hour
        }
    
    async def check_rate_limit(self, request: Request, endpoint: str = 'default'):
        client_ip = request.client.host
        key = f"{client_ip}:{endpoint}"
        
        max_requests, window_seconds = self.limits.get(endpoint, self.limits['default'])
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
        
        # Check limit
        if len(self.requests[key]) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s"
            )
        
        # Add current request
        self.requests[key].append(now)

rate_limiter = RateLimiter()
