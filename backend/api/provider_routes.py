"""LLM compatibility endpoints backed by the provider failover pool."""
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from ..core.provider_router import ProviderPool, ProviderUnavailable, providers_from_environment

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])
_pool: ProviderPool | None = None


def get_pool() -> ProviderPool:
    global _pool
    if _pool is None:
        providers = providers_from_environment()
        if not providers:
            raise HTTPException(status_code=503, detail="No LLM providers are configured")
        _pool = ProviderPool(providers, client=httpx.AsyncClient())
    return _pool


async def close_provider_pool() -> None:
    """Release the shared HTTP connection pool during application shutdown."""
    if _pool is not None and _pool.client is not None:
        await _pool.client.aclose()


@router.post("/chat/completions")
async def chat_completions(payload: dict[str, Any]):
    try:
        return await get_pool().chat_completion(payload)
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="The selected inference provider rejected the request",
        ) from exc


@router.get("/providers/status")
async def provider_status():
    try:
        return get_pool().status()
    except HTTPException:
        return {}
