import pytest

from turbobt.subtensor.pallets.subtensor_module import CommitRevealVersion


@pytest.mark.asyncio
async def test_burned_register(subtensor, alice_wallet):
    await subtensor.subtensor_module.burned_register(
        netuid=1,
        hotkey=alice_wallet.hotkey.ss58_address,
        era=None,
        wallet=alice_wallet,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "burned_register",
        {
            "netuid": 1,
            "hotkey": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
        },
        era=None,
        key=alice_wallet.coldkey,
    )


@pytest.mark.asyncio
async def test_commit_crv3_weights(subtensor, alice_wallet):
    await subtensor.subtensor_module.commit_crv3_weights(
        netuid=1,
        commit=b"TEST",
        reveal_round=204,
        era=None,
        wallet=alice_wallet,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "commit_timelocked_mechanism_weights",
        {
            "netuid": 1,
            "commit": "0x54455354",
            "mecid": 0,
            "reveal_round": 204,
            "commit_reveal_version": CommitRevealVersion.CRV3,
        },
        era=None,
        key=alice_wallet.hotkey,
    )


@pytest.mark.asyncio
async def test_commit_timelocked_weights(subtensor, alice_wallet):
    await subtensor.subtensor_module.commit_timelocked_weights(
        netuid=1,
        commit=b"TEST",
        reveal_round=204,
        commit_reveal_version=4,
        era=None,
        wallet=alice_wallet,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "commit_timelocked_mechanism_weights",
        {
            "netuid": 1,
            "commit": "0x54455354",
            "reveal_round": 204,
            "mecid": 0,
            "commit_reveal_version": 4,
        },
        era=None,
        key=alice_wallet.hotkey,
    )


@pytest.mark.asyncio
async def test_commit_timelocked_mechanism_weights(subtensor, alice_wallet):
    await subtensor.subtensor_module.commit_timelocked_mechanism_weights(
        netuid=1,
        commit=b"TEST",
        reveal_round=204,
        mechanism_id=123,
        commit_reveal_version=4,
        era=None,
        wallet=alice_wallet,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "commit_timelocked_mechanism_weights",
        {
            "netuid": 1,
            "commit": "0x54455354",
            "reveal_round": 204,
            "mecid": 123,
            "commit_reveal_version": 4,
        },
        era=None,
        key=alice_wallet.hotkey,
    )


@pytest.mark.asyncio
async def test_register_network(subtensor, alice_wallet):
    await subtensor.subtensor_module.register_network(
        hotkey=alice_wallet.hotkey.ss58_address,
        mechid=1,
        era=None,
        wallet=alice_wallet,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "register_network",
        {
            "hotkey": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            "mechid": 1,
        },
        era=None,
        key=alice_wallet.coldkey,
    )


@pytest.mark.asyncio
async def test_root_register(subtensor, alice_wallet):
    await subtensor.subtensor_module.root_register(
        hotkey=alice_wallet.hotkey.ss58_address,
        era=None,
        wallet=alice_wallet,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "root_register",
        {
            "hotkey": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
        },
        era=None,
        key=alice_wallet.coldkey,
    )


@pytest.mark.asyncio
async def test_serve_axon(subtensor, alice_wallet):
    await subtensor.subtensor_module.serve_axon(
        netuid=1,
        ip="192.168.0.2",
        port=8080,
        wallet=alice_wallet,
        protocol=4,
        version=100,
        era=None,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "serve_axon",
        {
            "ip_type": 4,
            "ip": 3232235522,
            "netuid": 1,
            "placeholder1": 0,
            "placeholder2": 0,
            "port": 8080,
            "protocol": 4,
            "version": 100,
        },
        era=None,
        key=alice_wallet.hotkey,
    )


@pytest.mark.asyncio
async def test_serve_axon_tls(subtensor, alice_wallet):
    await subtensor.subtensor_module.serve_axon_tls(
        netuid=1,
        ip="192.168.0.2",
        port=8080,
        certificate=b"CERT",
        wallet=alice_wallet,
        protocol=4,
        version=100,
        era=None,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "serve_axon_tls",
        {
            "certificate": b"CERT",
            "ip_type": 4,
            "ip": 3232235522,
            "netuid": 1,
            "placeholder1": 0,
            "placeholder2": 0,
            "port": 8080,
            "protocol": 4,
            "version": 100,
        },
        era=None,
        key=alice_wallet.hotkey,
    )


@pytest.mark.asyncio
async def test_set_weights(subtensor, alice_wallet):
    await subtensor.subtensor_module.set_weights(
        netuid=1,
        dests=[0, 1],
        weights=[0, 65535],
        version_key=1000,
        era=None,
        wallet=alice_wallet,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "set_mechanism_weights",
        {
            "netuid": 1,
            "dests": [0, 1],
            "weights": [0, 65535],
            "mecid": 0,
            "version_key": 1000,
        },
        era=None,
        key=alice_wallet.hotkey,
    )


@pytest.mark.asyncio
async def test_set_mechanism_weights(subtensor, alice_wallet):
    await subtensor.subtensor_module.set_mechanism_weights(
        netuid=1,
        dests=[0, 1],
        mechanism_id=123,
        weights=[0, 65535],
        version_key=1000,
        era=None,
        wallet=alice_wallet,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "set_mechanism_weights",
        {
            "netuid": 1,
            "dests": [0, 1],
            "weights": [0, 65535],
            "mecid": 123,
            "version_key": 1000,
        },
        era=None,
        key=alice_wallet.hotkey,
    )


@pytest.mark.asyncio
async def test_evm_addresses_fetch(subtensor, mocked_transport):
    mocked_transport.responses["state_getKeys"] = {
        "result": [
            "0x658faa385070e074c85bf6b568cf05552ee3ea5cc28fb0bcd7e9c900544e35b24b9bd30d03d0266b0c00a71a89063ba6541ca300",
            "0x658faa385070e074c85bf6b568cf05552ee3ea5cc28fb0bcd7e9c900544e35b24b9bd30d03d0266b0c00ce2b3c8f6925c6c8c500",
            "0x658faa385070e074c85bf6b568cf05552ee3ea5cc28fb0bcd7e9c900544e35b24b9bd30d03d0266b0c00d149990e23eec1414200",
        ],
    }
    mocked_transport.responses["state_queryStorageAt"] = {
        "result": [
            {
                "block": "0x388b5c4daa4e254119cb1a62b061af72b4d562977a5ac7d698e79698da4ffaa2",
                "changes": [
                    [
                        "0x658faa385070e074c85bf6b568cf05552ee3ea5cc28fb0bcd7e9c900544e35b24b9bd30d03d0266b0c00a71a89063ba6541ca300",
                        "0x77407f1709d339f5583feac922c0592e248f785f507e560000000000",
                    ],
                    [
                        "0x658faa385070e074c85bf6b568cf05552ee3ea5cc28fb0bcd7e9c900544e35b24b9bd30d03d0266b0c00ce2b3c8f6925c6c8c500",
                        "0xa873b6e2ed71bae54f232fb622b713239f0ec54cc87e530000000000",
                    ],
                    [
                        "0x658faa385070e074c85bf6b568cf05552ee3ea5cc28fb0bcd7e9c900544e35b24b9bd30d03d0266b0c00d149990e23eec1414200",
                        "0xba6a023c87dd55a0b862925278e77056677e92b7f37e530000000000",
                    ],
                ],
            },
        ],
    }

    evm_addresses = await subtensor.subtensor_module.AssociatedEvmAddress.fetch(12)

    assert evm_addresses == [
        ((12, 163), ("0x77407f1709d339f5583feac922c0592e248f785f", 5668432)),
        ((12, 197), ("0xa873b6e2ed71bae54f232fb622b713239f0ec54c", 5471944)),
        ((12, 66), ("0xba6a023c87dd55a0b862925278e77056677e92b7", 5471987)),
    ]


@pytest.mark.asyncio
async def test_add_stake(subtensor, alice_wallet):
    await subtensor.subtensor_module.add_stake(
        hotkey=alice_wallet.hotkey.ss58_address,
        netuid=1,
        amount_staked=1_000_000_000,
        era=None,
        wallet=alice_wallet,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "add_stake",
        {
            "netuid": 1,
            "hotkey": alice_wallet.hotkey.ss58_address,
            "amount_staked": 1_000_000_000,
        },
        era=None,
        key=alice_wallet.coldkey,
    )


@pytest.mark.asyncio
async def test_remove_stake(subtensor, alice_wallet):
    await subtensor.subtensor_module.remove_stake(
        hotkey=alice_wallet.hotkey.ss58_address,
        netuid=1,
        amount_unstaked=1_000_000_000,
        era=None,
        wallet=alice_wallet,
    )

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "SubtensorModule",
        "remove_stake",
        {
            "netuid": 1,
            "hotkey": alice_wallet.hotkey.ss58_address,
            "amount_unstaked": 1_000_000_000,
        },
        era=None,
        key=alice_wallet.coldkey,
    )
