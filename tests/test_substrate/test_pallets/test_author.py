import unittest.mock

import pytest

import turbobt.substrate.pallets.author


@pytest.mark.asyncio
async def test_submit_and_watch_extrinsic(substrate, mocked_transport, alice_wallet):
    mocked_transport.responses["system_accountNextIndex"] = {
        "result": 1,
    }
    mocked_transport.responses["chain_getHeader"] = {
        "result": {
            "parentHash": "0x2bb80cc429296b4da191bcec87d4b526ca0e407b4756f2a387a87d3b8e26ae42",
            "number": "0xf54",
            "stateRoot": "0xfb9e07dd769d95a30ab04e1e801b1400df1261487cddab93dc64628ad95cec56",
            "extrinsicsRoot": "0xe5b4ae1cda6591fa8a8026bef64c5d712f7dc6c0dc700f74d1670139e55c220d",
            "digest": {
                "logs": [],
            },
        },
    }
    mocked_transport.responses["chain_getBlockHash"] = {
        "result": "0xf0aa135ddac82c7b5ea0de2b021945381bc6a449fdd44386d9956fa0a5ee1e05",
    }
    mocked_transport.responses["author_submitAndWatchExtrinsic"] = {
        "result": bytearray(b"S6KpbWmhS2jSAsc8"),
    }

    result = await substrate.author.submitAndWatchExtrinsic(
        "SubtensorModule",
        "register_network",
        {
            "hotkey": alice_wallet.hotkey.ss58_address,
            "mechid": 1,
        },
        key=alice_wallet.coldkey,
        era=turbobt.substrate.pallets.author.Era(
            period=5,
        ),
    )

    assert result.subscription.id == "0x53364b7062576d6853326a5341736338"
    assert result.extrinsic.value == {
        "account_id": "0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d",
        "address": "0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d",
        "asset_id": {
            "asset_id": None,
            "tip": 0,
        },
        "call_args": {
            "hotkey": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            "mechid": 1,
        },
        "call_function": "register_network",
        "call_module": "SubtensorModule",
        "call": {
            "call_args": {
                "hotkey": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "mechid": 1,
            },
            "call_function": "register_network",
            "call_module": "SubtensorModule",
        },
        "era": {
            "current": 3924,
            "period": 5,
        },
        "mode": "Disabled",
        "nonce": 1,
        "signature_version": 1,
        "signature": {
            "Sr25519": unittest.mock.ANY,
        },
        "tip": 0,
    }


@pytest.mark.asyncio
async def test_unwatch_extrinsic(substrate, mocked_transport):
    mocked_transport.responses["author_unwatchExtrinsic"] = {
        "result": True,
    }

    result = await substrate.author.unwatchExtrinsic(
        "0x53364b7062576d6853326a5341736338"
    )

    assert result is True
