import json
import os
import unittest.mock

import pytest
import pytest_asyncio
from bittensor.keyfiles import Keypair
from bittensor.wallet import Wallet

from tests.mock.transport import MockedTransport


@pytest.fixture(scope="session")
def alice_wallet(tmp_path_factory):
    """Use native v11 keyfiles for the well-known Alice identity throughout the suite."""
    path = str(tmp_path_factory.mktemp("wallets"))
    wallet = Wallet(name="alice", path=path)
    keypair = Keypair.create_from_uri("//Alice")
    wallet.coldkey_file.set_keypair(keypair, encrypt=False)
    wallet.hotkey_file.set_keypair(keypair, encrypt=False)
    wallet.regenerate_coldkeypub(ss58_address=keypair.ss58_address)
    wallet.regenerate_hotkeypub(ss58_address=keypair.ss58_address)
    # Return a fresh instance so tests exercise loading the generated files.
    return Wallet(name="alice", path=path)


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
