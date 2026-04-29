import json

import pytest
import pytest_asyncio

from turbobt.subnet import BITTENSOR_VERSION_INT, WeightsCommited
from turbobt.substrate._scalecodec import u16_proportion_to_float
from turbobt.subtensor.pallets.subtensor_module import ZippedWeights


@pytest_asyncio.fixture
async def mocked_encrypted_commit(monkeypatch):
    def get_encrypted_commit(
        uids,
        weights,
        version_key,
        tempo,
        current_block,
        netuid,
        subnet_reveal_period_epochs,
        block_time,
        hotkey,
    ):
        return (
            json.dumps(
                {
                    "uids": uids,
                    "weights": weights,
                }
            ).encode(),
            123,
        )

    monkeypatch.setattr(
        "bittensor_drand.get_encrypted_commit",
        get_encrypted_commit,
    )

    yield


@pytest.mark.asyncio
async def test_commit(
    mocked_subtensor, bittensor, alice_wallet, mocked_encrypted_commit
):
    subnet = bittensor.subnet(1)

    await subnet.weights.commit(
        {
            0: 0.2,
            1: 0.8,
        }
    )

    mocked_subtensor.subtensor_module.commit_timelocked_mechanism_weights.assert_awaited_once_with(
        1,
        json.dumps({"uids": [0, 1], "weights": [16384, 65535]}).encode(),
        0,
        123,
        commit_reveal_version=4,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_commit_empty(
    mocked_subtensor, bittensor, alice_wallet, mocked_encrypted_commit
):
    subnet = bittensor.subnet(1)

    await subnet.weights.commit({})

    mocked_subtensor.subtensor_module.commit_timelocked_mechanism_weights.assert_awaited_once_with(
        1,
        json.dumps({"uids": [], "weights": []}).encode(),
        0,
        123,
        commit_reveal_version=4,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_commit_zeros(
    mocked_subtensor, bittensor, alice_wallet, mocked_encrypted_commit
):
    subnet = bittensor.subnet(1)

    await subnet.weights.commit(
        {
            0: 0.0,
            1: 0.0,
        }
    )

    mocked_subtensor.subtensor_module.commit_timelocked_mechanism_weights.assert_awaited_once_with(
        1,
        json.dumps({"uids": [0, 1], "weights": [0, 0]}).encode(),
        0,
        123,
        commit_reveal_version=4,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_commit_mechanism(
    mocked_subtensor, bittensor, alice_wallet, mocked_encrypted_commit
):
    subnet = bittensor.subnet(1)

    await subnet.weights.commit_mechanism(
        1,
        {
            0: 0.2,
            1: 0.8,
        },
    )

    mocked_subtensor.subtensor_module.commit_timelocked_mechanism_weights.assert_awaited_once_with(
        1,
        json.dumps({"uids": [0, 1], "weights": [16384, 65535]}).encode(),
        1,
        123,
        commit_reveal_version=4,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_commit_mechanism_empty(
    mocked_subtensor, bittensor, alice_wallet, mocked_encrypted_commit
):
    subnet = bittensor.subnet(1)

    await subnet.weights.commit_mechanism(1, {})

    mocked_subtensor.subtensor_module.commit_timelocked_mechanism_weights.assert_awaited_once_with(
        1,
        json.dumps({"uids": [], "weights": []}).encode(),
        1,
        123,
        commit_reveal_version=4,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_commit_mechanism_zeros(
    mocked_subtensor, bittensor, alice_wallet, mocked_encrypted_commit
):
    subnet = bittensor.subnet(1)

    await subnet.weights.commit_mechanism(
        1,
        {
            0: 0.0,
            1: 0.0,
        },
    )

    mocked_subtensor.subtensor_module.commit_timelocked_mechanism_weights.assert_awaited_once_with(
        1,
        json.dumps({"uids": [0, 1], "weights": [0, 0]}).encode(),
        1,
        123,
        commit_reveal_version=4,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_set(mocked_subtensor, bittensor, alice_wallet):
    subnet = bittensor.subnet(1)

    await subnet.weights.set(
        {
            0: 0.2,
            1: 0.8,
        }
    )

    mocked_subtensor.subtensor_module.set_mechanism_weights.assert_awaited_once_with(
        1,
        [0, 1],
        0,
        [16384, 65535],
        version_key=BITTENSOR_VERSION_INT,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_set_empty(mocked_subtensor, bittensor, alice_wallet):
    subnet = bittensor.subnet(1)

    await subnet.weights.set({})

    mocked_subtensor.subtensor_module.set_mechanism_weights.assert_awaited_once_with(
        1,
        [],
        0,
        [],
        version_key=BITTENSOR_VERSION_INT,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_set_zeros(mocked_subtensor, bittensor, alice_wallet):
    subnet = bittensor.subnet(1)

    await subnet.weights.set(
        {
            0: 0.0,
            1: 0.0,
        }
    )

    mocked_subtensor.subtensor_module.set_mechanism_weights.assert_awaited_once_with(
        1,
        [0, 1],
        0,
        [0, 0],
        version_key=BITTENSOR_VERSION_INT,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_set_mechanism(mocked_subtensor, bittensor, alice_wallet):
    subnet = bittensor.subnet(1)

    await subnet.weights.set_mechanism(
        1,
        {
            0: 0.2,
            1: 0.8,
        },
    )

    mocked_subtensor.subtensor_module.set_mechanism_weights.assert_awaited_once_with(
        1,
        [0, 1],
        1,
        [16384, 65535],
        version_key=BITTENSOR_VERSION_INT,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_set_mechanism_empty(mocked_subtensor, bittensor, alice_wallet):
    subnet = bittensor.subnet(1)

    await subnet.weights.set_mechanism(1, {})

    mocked_subtensor.subtensor_module.set_mechanism_weights.assert_awaited_once_with(
        1,
        [],
        1,
        [],
        version_key=BITTENSOR_VERSION_INT,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_set_mechanism_zeros(mocked_subtensor, bittensor, alice_wallet):
    subnet = bittensor.subnet(1)

    await subnet.weights.set_mechanism(
        1,
        {
            0: 0.0,
            1: 0.0,
        },
    )

    mocked_subtensor.subtensor_module.set_mechanism_weights.assert_awaited_once_with(
        1,
        [0, 1],
        1,
        [0, 0],
        version_key=BITTENSOR_VERSION_INT,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_get(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    mocked_subtensor.subtensor_module.Weights.get.return_value = [
        ZippedWeights(100, 16384),
        ZippedWeights(101, 32768),
    ]

    result = await subnet.weights.get(10)

    assert result == {
        100: u16_proportion_to_float(16384),
        101: u16_proportion_to_float(32768),
    }
    mocked_subtensor.subtensor_module.Weights.get.assert_awaited_once_with(
        1, 10, block_hash=None
    )


@pytest.mark.asyncio
async def test_get_empty(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    mocked_subtensor.subtensor_module.Weights.get.return_value = None

    result = await subnet.weights.get(10)

    assert result == {}
    mocked_subtensor.subtensor_module.Weights.get.assert_awaited_once_with(
        1, 10, block_hash=None
    )


@pytest.mark.asyncio
async def test_get_mechanism(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    mocked_subtensor.subtensor_module.Weights.get.return_value = [
        ZippedWeights(100, 16384),
        ZippedWeights(101, 32768),
    ]

    result = await subnet.weights.get_mechanism(1, 10)

    assert result == {
        100: u16_proportion_to_float(16384),
        101: u16_proportion_to_float(32768),
    }
    mocked_subtensor.subtensor_module.Weights.get.assert_awaited_once_with(
        4097, 10, block_hash=None
    )


@pytest.mark.asyncio
async def test_get_mechanism_empty(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    mocked_subtensor.subtensor_module.Weights.get.return_value = None

    result = await subnet.weights.get_mechanism(1, 10)

    assert result == {}
    mocked_subtensor.subtensor_module.Weights.get.assert_awaited_once_with(
        4097, 10, block_hash=None
    )


@pytest.mark.asyncio
async def test_fetch(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    mocked_subtensor.subtensor_module.Weights.fetch.return_value = [
        ((1, 10), [ZippedWeights(100, 16384)]),
        ((1, 11), [ZippedWeights(101, 32768), ZippedWeights(102, 65535)]),
    ]

    result = await subnet.weights.fetch()

    assert result == {
        10: {100: u16_proportion_to_float(16384)},
        11: {
            101: u16_proportion_to_float(32768),
            102: u16_proportion_to_float(65535),
        },
    }
    mocked_subtensor.subtensor_module.Weights.fetch.assert_awaited_once_with(
        1, block_hash=None
    )


@pytest.mark.asyncio
async def test_fetch_empty(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    mocked_subtensor.subtensor_module.Weights.fetch.return_value = []

    result = await subnet.weights.fetch()

    assert result == {}
    mocked_subtensor.subtensor_module.Weights.fetch.assert_awaited_once_with(
        1, block_hash=None
    )


@pytest.mark.asyncio
async def test_fetch_mechanism(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    mocked_subtensor.subtensor_module.Weights.fetch.return_value = [
        ((1, 10), [ZippedWeights(100, 16384)]),
        ((1, 11), [ZippedWeights(101, 32768), ZippedWeights(102, 65535)]),
    ]

    result = await subnet.weights.fetch_mechanism(1)

    assert result == {
        10: {100: u16_proportion_to_float(16384)},
        11: {
            101: u16_proportion_to_float(32768),
            102: u16_proportion_to_float(65535),
        },
    }
    mocked_subtensor.subtensor_module.Weights.fetch.assert_awaited_once_with(
        4097, block_hash=None
    )


@pytest.mark.asyncio
async def test_fetch_mechanism_empty(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    mocked_subtensor.subtensor_module.Weights.fetch.return_value = []

    result = await subnet.weights.fetch_mechanism(1)

    assert result == {}
    mocked_subtensor.subtensor_module.Weights.fetch.assert_awaited_once_with(
        4097, block_hash=None
    )


@pytest.mark.asyncio
async def test_fetch_pending(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    hotkey_bytes = bytes.fromhex(
        "8eaf04151687736326c9fea17e25fc5287613693c912909cb226aa4794f26a48"
    )
    hotkey_ss58 = "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty"

    mocked_subtensor.subtensor_module.TimelockedWeightCommits.fetch.return_value = [
        ((1, 100), [(hotkey_bytes, 1000, "0x1234", 10)]),
    ]

    result = await subnet.weights.fetch_pending()

    assert result == {
        100: {
            hotkey_ss58: WeightsCommited(1000, b"\x124", 10),
        }
    }
    mocked_subtensor.subtensor_module.TimelockedWeightCommits.fetch.assert_awaited_once_with(
        1, block_hash=None
    )


@pytest.mark.asyncio
async def test_fetch_pending_empty(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    mocked_subtensor.subtensor_module.TimelockedWeightCommits.fetch.return_value = []

    result = await subnet.weights.fetch_pending()

    assert result == {}
    mocked_subtensor.subtensor_module.TimelockedWeightCommits.fetch.assert_awaited_once_with(
        1, block_hash=None
    )


@pytest.mark.asyncio
async def test_fetch_pending_mechanism(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    hotkey_bytes = bytes.fromhex(
        "8eaf04151687736326c9fea17e25fc5287613693c912909cb226aa4794f26a48"
    )
    hotkey_ss58 = "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty"

    mocked_subtensor.subtensor_module.TimelockedWeightCommits.fetch.return_value = [
        ((4097, 100), [(hotkey_bytes, 1000, "0x1234", 10)]),
    ]

    result = await subnet.weights.fetch_pending_mechanism(1)

    assert result == {
        100: {
            hotkey_ss58: WeightsCommited(1000, b"\x124", 10),
        }
    }
    mocked_subtensor.subtensor_module.TimelockedWeightCommits.fetch.assert_awaited_once_with(
        4097, block_hash=None
    )


@pytest.mark.asyncio
async def test_fetch_pending_mechanism_empty(mocked_subtensor, bittensor):
    subnet = bittensor.subnet(1)

    mocked_subtensor.subtensor_module.TimelockedWeightCommits.fetch.return_value = []

    result = await subnet.weights.fetch_pending_mechanism(1)

    assert result == {}
    mocked_subtensor.subtensor_module.TimelockedWeightCommits.fetch.assert_awaited_once_with(
        4097, block_hash=None
    )
