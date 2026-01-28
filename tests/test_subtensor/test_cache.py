import unittest.mock

import pytest

from turbobt.substrate._models import Request, Response
from turbobt.subtensor.cache import CacheControl, CacheTransport, InMemoryStorage


@pytest.mark.asyncio
async def test_in_memory_storage():
    storage = InMemoryStorage()

    assert len(storage) == 0

    value = await storage.get("key")

    assert value is None
    assert len(storage) == 0

    await storage.set("key", "value")

    assert len(storage) == 1

    value = await storage.get("key")

    assert value == "value"


@pytest.mark.asyncio
async def test_in_memory_storage_maxsize():
    storage = InMemoryStorage(max_size=1)

    await storage.set("key1", "value1")

    value = await storage.get("key1")

    assert value == "value1"
    assert len(storage) == 1

    await storage.set("key2", "value2")

    value = await storage.get("key2")

    assert value == "value2"
    assert len(storage) == 1

    value = await storage.get("key1")

    assert value is None


@pytest.mark.parametrize(
    "rpc_request,cachable",
    [
        (
            Request(
                method="state_call",
                params={
                    "name": "state_getRuntimeVersion",
                },
            ),
            True,
        ),
        (
            Request(
                method="author_submitAndWatchExtrinsic",
                params={
                    "bytes": "0x00",
                },
            ),
            False,
        ),
    ],
)
@pytest.mark.asyncio
async def test_cache_control_is_cachable(rpc_request, cachable):
    cache_control = CacheControl()

    result = cache_control.is_cachable(rpc_request)

    assert result is cachable


@pytest.mark.asyncio
async def test_cache_transport():
    mocked_transport = unittest.mock.AsyncMock()
    mocked_transport.send.side_effect = lambda request: Response(
        request=request,
        result="SUCCESS",
    )

    storage = InMemoryStorage()
    cache_transport = CacheTransport(
        transport=mocked_transport,
        cache_control=CacheControl(),
        storage=storage,
    )

    async with cache_transport:
        response = await cache_transport.send(
            Request(
                method="state_call",
                params={
                    "name": "state_getRuntimeVersion",
                    "test": None,
                },
            ),
        )

        assert response.result == "SUCCESS"

        await cache_transport.send(
            Request(
                method="state_call",
                params={
                    "name": "state_getRuntimeVersion",
                    "test": None,
                },
            ),
        )

        assert response.result == "SUCCESS"
        assert mocked_transport.send.call_count == 1

        await cache_transport.send(
            Request(
                method="author_submitAndWatchExtrinsic",
                params={
                    "bytes": "0x00",
                },
            ),
        )

        assert mocked_transport.send.call_count == 2

    assert len(storage) == 1
