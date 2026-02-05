import aiohttp
import json
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with local Ollama instance."""

    def __init__(self, base_url: Optional[str] = None, model: str = "aurora"):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model

    async def chat(self, messages: List[Dict[str, str]], format: Optional[str] = None) -> Dict[str, Any]:
        """Send chat messages to Ollama."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        if format == "json":
            payload["format"] = "json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama error: {error_text}")
                        return {"error": error_text}

                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return {"error": str(e)}

    async def generate(self, prompt: str, system: Optional[str] = None, format: Optional[str] = None) -> Dict[str, Any]:
        """Generate a completion from a prompt."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system
        if format == "json":
            payload["format"] = "json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama error: {error_text}")
                        return {"error": error_text}

                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return {"error": str(e)}
