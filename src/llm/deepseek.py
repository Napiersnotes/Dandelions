"""
DeepSeek AI Provider Implementation
"""

import httpx
from typing import Optional, Dict, Any
from pydantic import BaseModel

from src.llm.base import BaseLLMProvider, LLMConfig
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class DeepSeekResponse(BaseModel):
    """DeepSeek API response format"""
    id: str
    object: str
    created: int
    model: str
    choices: list
    usage: Dict[str, int]

class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek AI provider implementation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.deepseek.com"
        self.client = None
    
    async def initialize(self):
        """Initialize DeepSeek client"""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        logger.info(f"DeepSeek provider initialized with model: {self.config.model}")
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using DeepSeek API"""
        if not self.client:
            raise RuntimeError("DeepSeek provider not initialized")
        
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.config.model or "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    **kwargs
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data["model"],
                "usage": data["usage"],
                "cost": self._calculate_cost(data["usage"])
            }
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on usage"""
        # DeepSeek pricing (example, check actual pricing)
        input_cost_per_token = 0.0000014  # $0.14 per 1M tokens
        output_cost_per_token = 0.0000028  # $0.28 per 1M tokens
        
        input_cost = usage.get("prompt_tokens", 0) * input_cost_per_token
        output_cost = usage.get("completion_tokens", 0) * output_cost_per_token
        
        return input_cost + output_cost
    
    async def test_connection(self) -> bool:
        """Test connection to DeepSeek API"""
        try:
            response = await self.client.get("/models")
            return response.status_code == 200
        except:
            return False
    
    async def close(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()
    
    def is_connected(self) -> bool:
        """Check if provider is connected"""
        return self.client is not None
