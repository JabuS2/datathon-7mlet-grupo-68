import pytest

from exceptions import AppException
from services.model_client import ModelServiceClient


@pytest.mark.asyncio
async def test_rank_raises_when_service_unreachable():
    # porta fechada => falha de conexão mapeada para AppException
    client = ModelServiceClient(base_url="http://127.0.0.1:1", timeout=1.0)
    with pytest.raises(AppException) as exc:
        await client.rank("linucb", {"idade": 30}, [])
    assert exc.value.code == "MODEL_SERVICE_UNAVAILABLE"
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_update_raises_when_service_unreachable():
    client = ModelServiceClient(base_url="http://127.0.0.1:1", timeout=1.0)
    with pytest.raises(AppException) as exc:
        await client.update("linucb", "OFF-CR-001", 1.0, {"idade": 30}, [])
    assert exc.value.code == "MODEL_SERVICE_UNAVAILABLE"


def test_base_url_strips_trailing_slash():
    client = ModelServiceClient(base_url="http://model:8000/")
    assert client.base_url == "http://model:8000"
