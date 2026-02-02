import aiohttp
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

async def search_component(mpn: str, api_key: str) -> Optional[Dict]:
    """Search for component on Octopart"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://octopart.com/api/v4/rest/parts/search"
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "queries": [{"mpn": mpn, "limit": 5}]
            }
            
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                else:
                    logger.error(f"Octopart API error: {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"Component search error: {e}")
        return None
