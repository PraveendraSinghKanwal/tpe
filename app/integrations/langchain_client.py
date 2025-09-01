from typing import Dict, Any, List, Optional
import asyncio
import time
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks import get_openai_callback
from langchain.callbacks.base import BaseCallbackHandler

from app.config import settings
from app.core.logging import get_logger
from app.core.monitoring import record_llm_metrics

logger = get_logger(__name__)


class MetricsCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for collecting LLM metrics."""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.start_time = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """Called when LLM starts."""
        self.start_time = time.time()
    
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when LLM ends."""
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Record metrics
            record_llm_metrics(
                model=settings.openai_model,
                endpoint=self.endpoint,
                duration=duration,
                status="success",
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                total_tokens=self.total_tokens
            )
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM encounters an error."""
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Record error metrics
            record_llm_metrics(
                model=settings.openai_model,
                endpoint=self.endpoint,
                duration=duration,
                status="error"
            )
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when LLM generates a new token."""
        pass


class LangChainClient:
    """LangChain client for LLM interactions."""
    
    def __init__(self):
        self.model = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            openai_api_key=settings.openai_api_key
        )
    
    async def get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        endpoint: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Get completion from LLM using LangChain.
        
        Args:
            system_prompt: System message to set context
            user_prompt: User message/query
            endpoint: Endpoint identifier for metrics
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Create callback handler for metrics
            callback_handler = MetricsCallbackHandler(endpoint)
            
            # Prepare messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Get completion with metrics tracking
            with get_openai_callback() as cb:
                response = await asyncio.to_thread(
                    self.model.agenerate,
                    [messages],
                    callbacks=[callback_handler]
                )
                
                # Extract response content
                if response.generations and response.generations[0]:
                    content = response.generations[0][0].text
                else:
                    content = ""
                
                # Update callback handler with token counts
                callback_handler.prompt_tokens = cb.prompt_tokens or 0
                callback_handler.completion_tokens = cb.completion_tokens or 0
                callback_handler.total_tokens = cb.total_tokens or 0
                
                logger.info(
                    "LLM completion successful",
                    endpoint=endpoint,
                    model=settings.openai_model,
                    prompt_tokens=callback_handler.prompt_tokens,
                    completion_tokens=callback_handler.completion_tokens,
                    total_tokens=callback_handler.total_tokens
                )
                
                return {
                    "content": content,
                    "model": settings.openai_model,
                    "prompt_tokens": callback_handler.prompt_tokens,
                    "completion_tokens": callback_handler.completion_tokens,
                    "total_tokens": callback_handler.total_tokens
                }
                
        except Exception as e:
            logger.error(
                "LLM completion failed",
                endpoint=endpoint,
                error=str(e),
                model=settings.openai_model
            )
            raise
    
    async def get_completion_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        endpoint: str = "unknown",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Get completion with retry logic for resilience.
        
        Args:
            system_prompt: System message to set context
            user_prompt: User message/query
            endpoint: Endpoint identifier for metrics
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Dictionary containing response and metadata
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await self.get_completion(system_prompt, user_prompt, endpoint)
                
            except Exception as e:
                last_exception = e
                logger.warning(
                    "LLM completion attempt failed",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                    endpoint=endpoint
                )
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
        
        # All retries failed
        logger.error(
            "LLM completion failed after all retries",
            endpoint=endpoint,
            max_retries=max_retries,
            final_error=str(last_exception)
        )
        raise last_exception


# Global LangChain client instance
langchain_client = LangChainClient()
