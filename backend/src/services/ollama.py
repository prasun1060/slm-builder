import httpx
from typing import Any, Dict, List
from httpx.exceptions import ConnectionError

class OllamaUnavailableError(RuntimeError):
    pass

class OllamaService:
    def __init__(self, model_config: Dict[str, Any]):
        self.base_url = model_config.get('base_url')
        self.model_id = model_config.get('model_id')
        if not self.base_url or not self.model_id:
            raise ValueError("model_config must contain 'base_url' and 'model_id'")

    async def generate(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/generate", json={"prompt": prompt, "model": self.model_id})
                response.raise_for_status()
                return response.json().get('text')
        except ConnectionError:
            raise OllamaUnavailableError("Failed to connect to Ollama API")
        except httpx.exceptions.RequestException as e:
            raise RuntimeError(f"Error generating text: {e}")

    async def get_embedding(self, text: str) -> List[float]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/embed", json={"text": text, "model": self.model_id})
                response.raise_for_status()
                return response.json().get('embedding')
        except ConnectionError:
            raise OllamaUnavailableError("Failed to connect to Ollama API")
        except httpx.exceptions.RequestException as e:
            raise RuntimeError(f"Error getting embedding: {e}")

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json().get('status') == 'ok'
        except ConnectionError:
            raise OllamaUnavailableError("Failed to connect to Ollama API")
        except httpx.exceptions.RequestException as e:
            raise RuntimeError(f"Health check failed: {e}")
