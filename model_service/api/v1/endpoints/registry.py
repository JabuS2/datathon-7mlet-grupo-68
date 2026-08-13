import asyncio

from fastapi import APIRouter, Depends

from dependencies import get_registry, get_service
from registry import ModelRegistry
from schemas.registry import LoadRequest, RegisterRequest
from service import BanditService

router = APIRouter()


@router.get("/registry/models", tags=["registry"])
async def list_models(registry: ModelRegistry = Depends(get_registry)):
    return await asyncio.to_thread(registry.list_models)


@router.post("/registry/models", tags=["registry"])
async def register_model(
    req: RegisterRequest,
    registry: ModelRegistry = Depends(get_registry),
    service: BanditService = Depends(get_service),
):
    state = await service.snapshot_state(req.algorithm)
    return await asyncio.to_thread(registry.register_version, req.name, state)


@router.post("/registry/models/{name}/load", tags=["registry"])
async def load_model(
    name: str,
    req: LoadRequest,
    registry: ModelRegistry = Depends(get_registry),
    service: BanditService = Depends(get_service),
):
    state = await asyncio.to_thread(registry.load, name, req.version)
    await service.restore_state(req.algorithm or state.get("name"), state)
    return {"name": name, "algorithm": state.get("name"), "status": "loaded"}


@router.delete("/registry/models/{name}", tags=["registry"])
async def delete_model(name: str, registry: ModelRegistry = Depends(get_registry)):
    return await asyncio.to_thread(registry.delete_model, name)
