import os
import aiohttp
import asyncio
import hashlib
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

# Embedding API configuration
EMBEDDING_API_URL = os.getenv("OPENAI_EMBEDDING_URL", "https://api.openai.com/v1/embeddings")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Retry and timeout configuration
MAX_RETRIES = 3
CLIENT_TIMEOUT = aiohttp.ClientTimeout(total=60)

# In-memory cache for embeddings
EMBEDDING_CACHE = {}

def _cache_key(text: str, model: str) -> str:
    """Generate a cache key for a given text and model."""
    digest = hashlib.sha256(text.encode()).hexdigest()
    return f"{model}:{digest}"

async def _embed_request(inputs: list, model: str) -> list:
    """
    Internal helper to send batch embedding request and return list of embeddings.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not set in environment variable OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"model": model, "input": inputs}

    async def _do_request():
        async with aiohttp.ClientSession(timeout=CLIENT_TIMEOUT) as session:
            async with session.post(EMBEDDING_API_URL, json=payload, headers=headers) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Embedding API error {response.status}: {text}")
                    response.raise_for_status()
                return await response.json()

    try:
        data = await _retry_async_operation(_do_request, max_retries=MAX_RETRIES)
    except Exception as e:
        logger.error(f"Embedding API retries exhausted: {str(e)}", exc_info=True)
        raise

    # Extract embeddings in the order returned
    embeddings = [item.get("embedding") for item in data.get("data", [])]
    return embeddings

async def async_embed(text: str, model: str = "text-embedding-3-small") -> list:
    """
    Asynchronously embed a single text string, with caching.
    """
    key = _cache_key(text, model)
    if key in EMBEDDING_CACHE:
        return EMBEDDING_CACHE[key]

    embeddings = await _embed_request([text], model)
    if embeddings:
        EMBEDDING_CACHE[key] = embeddings[0]
        return embeddings[0]
    return None

async def async_embed_batch(
    texts: list,
    model: str = "text-embedding-3-small",
    batch_size: int = 16,
    concurrency: int = 4
) -> list:
    """
    Asynchronously embed a batch of texts, using batching and caching.
    Maintains input order and uses a semaphore for concurrency control.
    """
    results = [None] * len(texts)
    to_request = {}

    # First, fill in cached embeddings
    for idx, text in enumerate(texts):
        key = _cache_key(text, model)
        if key in EMBEDDING_CACHE:
            results[idx] = EMBEDDING_CACHE[key]
        else:
            to_request[idx] = text

    semaphore = asyncio.Semaphore(concurrency)

    async def fetch_chunk(indices, batch_texts):
        async with semaphore:
            try:
                embeddings = await _embed_request(batch_texts, model)
                for sub_i, emb in enumerate(embeddings):
                    global_i = indices[sub_i]
                    text_val = batch_texts[sub_i]
                    results[global_i] = emb
                    EMBEDDING_CACHE[_cache_key(text_val, model)] = emb
            except Exception as e:
                logger.error(f"Error embedding chunk {indices}: {str(e)}", exc_info=True)
                for global_i in indices:
                    results[global_i] = None

    # Break uncached texts into chunks
    items = list(to_request.items())
    tasks = []
    for i in range(0, len(items), batch_size):
        slice_items = items[i : i + batch_size]
        idxs, batch_texts = zip(*slice_items)
        tasks.append(asyncio.create_task(fetch_chunk(idxs, list(batch_texts))))

    if tasks:
        await asyncio.gather(*tasks)

    return results 