import ipaddress

import pytest

from turbobt.neuron import AxonInfo, Neuron, PrometheusInfo
from turbobt.subnet import SubnetReference


@pytest.mark.asyncio
async def test_get(mocked_subtensor, bittensor):
    mocked_subtensor.neuron_info.get_neuron.return_value = {
        "hotkey": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        "coldkey": "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        "uid": 0,
        "netuid": 1,
        "active": True,
        "axon_info": {
            "block": 0,
            "version": 0,
            "ip": 0,
            "port": 0,
            "ip_type": 0,
            "protocol": 0,
            "placeholder1": 0,
            "placeholder2": 0,
        },
        "prometheus_info": {
            "block": 0,
            "version": 0,
            "ip": 0,
            "port": 0,
            "ip_type": 0,
        },
        "stake": {
            "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM": 1000000000,
        },
        "rank": 0,
        "emission": 0,
        "incentive": 0,
        "consensus": 0,
        "trust": 0,
        "validator_trust": 0,
        "dividends": 0,
        "last_update": 0,
        "validator_permit": True,
        "weights": [],
        "bonds": [],
        "pruning_score": 65535,
    }

    subnet_ref = bittensor.subnet(1)
    neuron_ref = subnet_ref.neuron(0)
    neuron = await neuron_ref.get()

    assert neuron == Neuron(
        active=True,
        axon_info=AxonInfo(
            ip=ipaddress.IPv4Address("0.0.0.0"),  # noqa: S104
            port=0,
            protocol=0,
        ),
        coldkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        consensus=0,
        dividends=0,
        emission=0,
        hotkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        incentive=0,
        last_update=0,
        prometheus_info=PrometheusInfo(
            ip=ipaddress.IPv4Address("0.0.0.0"),  # noqa: S104
            port=0,
        ),
        pruning_score=65535,
        rank=0,
        stake=1.0,
        subnet=SubnetReference(
            client=bittensor,
            netuid=1,
        ),
        trust=0,
        uid=0,
        validator_permit=True,
        validator_trust=0,
    )


@pytest.mark.asyncio
async def test_get_by_hotkey_not_exist(mocked_subtensor, bittensor):
    mocked_subtensor.subtensor_module.Uids.get.return_value = None

    subnet = bittensor.subnet(1)
    neuron = await subnet.get_neuron("5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM")

    assert neuron is None

    mocked_subtensor.neuron_info.get_neuron.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_stake(mocked_subtensor, bittensor, alice_wallet):
    subnet = bittensor.subnet(1)
    neuron = subnet.neurons["5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"]

    await neuron.add_stake(1_000_000_000)

    mocked_subtensor.subtensor_module.add_stake.assert_awaited_once_with(
        netuid=1,
        hotkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        amount_staked=1_000_000_000,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_remove_stake(mocked_subtensor, bittensor, alice_wallet):
    subnet = bittensor.subnet(1)
    neuron = subnet.neurons["5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"]

    await neuron.remove_stake(1_000_000_000)

    mocked_subtensor.subtensor_module.remove_stake.assert_awaited_once_with(
        netuid=1,
        hotkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",
        amount_unstaked=1_000_000_000,
        wallet=alice_wallet,
    )


@pytest.mark.asyncio
async def test_get_certificate_success(mocked_subtensor, bittensor):
    # Mock certificate data
    mock_certificate = {
        "algorithm": 1,
        "public_key": "0x1234567890abcdef",
        "signature": "0xfedcba0987654321",
    }
    mocked_subtensor.subtensor_module.NeuronCertificates.get.return_value = (
        mock_certificate
    )

    subnet_ref = bittensor.subnet(1)
    neuron_ref = subnet_ref.neuron(
        hotkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"
    )
    result = await neuron_ref.get_certificate()

    assert result == mock_certificate
    mocked_subtensor.subtensor_module.NeuronCertificates.get.assert_called_once_with(
        1,  # netuid
        "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",  # hotkey
        block_hash=None,
    )


@pytest.mark.asyncio
async def test_get_certificate_with_block_hash(mocked_subtensor, bittensor):
    # Mock certificate data
    mock_certificate = {
        "algorithm": 1,
        "public_key": "0x1234567890abcdef",
        "signature": "0xfedcba0987654321",
    }
    mocked_subtensor.subtensor_module.NeuronCertificates.get.return_value = (
        mock_certificate
    )

    subnet_ref = bittensor.subnet(1)
    neuron_ref = subnet_ref.neuron(
        hotkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"
    )
    block_hash = "0xabcdef1234567890"
    result = await neuron_ref.get_certificate(block_hash=block_hash)

    assert result == mock_certificate
    mocked_subtensor.subtensor_module.NeuronCertificates.get.assert_called_once_with(
        1,  # netuid
        "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM",  # hotkey
        block_hash=block_hash,
    )


@pytest.mark.asyncio
async def test_get_certificate_not_found(mocked_subtensor, bittensor):
    # Mock certificate not found
    mocked_subtensor.subtensor_module.NeuronCertificates.get.return_value = None

    subnet_ref = bittensor.subnet(1)
    neuron_ref = subnet_ref.neuron(
        hotkey="5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"
    )
    result = await neuron_ref.get_certificate()

    assert result is None
