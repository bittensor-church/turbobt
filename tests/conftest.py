import json
import os
import tempfile
import unittest.mock

import bittensor_wallet
import pytest_asyncio

from tests.mock.transport import MockedTransport


@pytest_asyncio.fixture(autouse=True, scope="session")
def monkeypatch_keypair(alice_wallet):
    assert alice_wallet.hotkey != alice_wallet.hotkey, "Keypair.__eq__ fixed!"

    with unittest.mock.patch.object(
        bittensor_wallet.Keypair, "__eq__", lambda self, other: str(self) == str(other)
    ):
        yield


@pytest_asyncio.fixture(scope="session")
def alice_wallet():
    keypair = bittensor_wallet.Keypair.create_from_uri("//Alice")

    wallet = bittensor_wallet.Wallet(
        path=tempfile.mkdtemp(),
    )
    wallet.set_coldkey(keypair=keypair, encrypt=False, overwrite=True)
    wallet.set_coldkeypub(keypair=keypair, encrypt=False, overwrite=True)
    wallet.set_hotkey(keypair=keypair, encrypt=False, overwrite=True)

    return wallet


@pytest_asyncio.fixture(scope="session")
async def metadata():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "test_substrate/data/metadata_version_15.json")
    with open(path) as data:
        return json.load(data)


@pytest_asyncio.fixture(scope="session")
async def runtime():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "test_substrate/data/runtime_version_318.json")
    with open(path) as data:
        return json.load(data)


@pytest_asyncio.fixture
async def mocked_transport(metadata, runtime):
    transport = MockedTransport()
    transport.responses["state_call"] = {
        "Metadata_metadata_at_version": {
            "result": metadata,
        },
    }
    transport.responses["state_getRuntimeVersion"] = {
        "result": runtime,
    }

    with unittest.mock.patch.object(transport, "send", wraps=transport.send):
        yield transport
