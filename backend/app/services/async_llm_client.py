import os
import aiohttp
import asyncio
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

# API configuration
DEFAULT_LLM_API = "OpenAI"  # Force OpenAI regardless of env var
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

# Retry configuration
MAX_RETRIES = 3
CLIENT_TIMEOUT = aiohttp.ClientTimeout(total=60)

async def _retry_async_operation(operation, max_retries=MAX_RETRIES):
    """Retry an async operation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                raise  # Re-raise the last exception
            wait_time = (2 ** attempt) + (asyncio.get_event_loop().time() % 1)
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time:.1f}s")
            await asyncio.sleep(wait_time)

async def async_llm_call(
    messages,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = None
):
    """
    Execute an async chat completion request to the configured LLM API.

    Args:
        messages (list): List of message dicts with 'role' and 'content'.
        model (str): Model name to use (optional, API-specific).
        temperature (float): Sampling temperature.
        max_tokens (int, optional): Maximum tokens to generate.

    Returns:
        dict: Parsed JSON response from the API.
    """
    logger.info("Starting LLM API call")
    logger.debug(f"Using model: {model or 'default'}, temperature: {temperature}")
    
    if DEFAULT_LLM_API == "GoogleAI":
        if not GOOGLE_API_KEY:
            logger.error("Google API key not found in environment")
            raise ValueError("Google API key not set in environment variable GOOGLE_API_KEY")
            
        # Convert messages to Google's format
        prompt = "\n".join([m["content"] for m in messages])
        logger.debug("Using Google AI API")
        
        headers = {
            "x-goog-api-key": GOOGLE_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": temperature,
                "topK": 40,
                "topP": 0.95
            }
        }
        
        url = GOOGLE_API_URL
        
    else:  # Default to OpenAI
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not found in environment")
            raise ValueError("OpenAI API key not set in environment variable OPENAI_API_KEY")
            
        logger.debug("Using OpenAI API")
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or "gpt-3.5-turbo",
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
            
        url = OPENAI_API_URL

    async def _do_request():
        logger.info(f"Making request to {url}")
        async with aiohttp.ClientSession(timeout=CLIENT_TIMEOUT) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"LLM API error {response.status}: {text}")
                    response.raise_for_status()
                    
                data = await response.json()
                logger.info("Successfully received response from LLM API")
                
                # Format response consistently regardless of API
                if DEFAULT_LLM_API == "GoogleAI":
                    return {
                        "content": data["candidates"][0]["content"]["parts"][0]["text"]
                    }
                else:
                    return {
                        "content": data["choices"][0]["message"]["content"]
                    }

    try:
        logger.info("Starting LLM request with retries")
        result = await _retry_async_operation(_do_request, max_retries=MAX_RETRIES)
        logger.info("LLM request completed successfully")
        return result
    except Exception as e:
        logger.error(f"LLM API retries exhausted: {str(e)}", exc_info=True)
        raise

async def async_llm_batch(
    batch_of_messages,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = None,
    concurrency: int = None
):
    """
    Run multiple LLM calls in parallel and return list of responses.

    Args:
        batch_of_messages (List[list]): A list where each element is a list of message dicts.
        model (str): Model name to use for each call.
        temperature (float): Sampling temperature.
        max_tokens (int, optional): Maximum tokens to generate for each call.
        concurrency (int, optional): Maximum number of concurrent tasks.

    Returns:
        List[dict]: List of JSON responses for each call.
    """
    # Determine concurrency limit (default from env or 5)
    if concurrency is None:
        concurrency = int(os.getenv("LLM_CONCURRENCY", 5))

    # Prepare coroutines for each batch element
    coros = [
        async_llm_call(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        for messages in batch_of_messages
    ]
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(concurrency)
    
    async def _bounded_llm_call(coro):
        async with semaphore:
            return await coro
    
    # Run with concurrency control
    return await asyncio.gather(*[_bounded_llm_call(coro) for coro in coros]) 