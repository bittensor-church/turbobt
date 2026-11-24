import pytest
from scalecodec.base import RuntimeConfigurationObject
from scalecodec.type_registry import load_type_registry_preset

from turbobt.subtensor.pallets.commitments import _decode_registration


@pytest.mark.asyncio
async def test_get_commitment(subtensor, alice_wallet, mocked_transport):
    mocked_transport.responses["state_getStorage"] = {
        "result": "0x000000000000000021010000040500010203",
    }

    netuid = 1

    commitment = await subtensor.commitments.CommitmentOf.get(
        netuid,
        alice_wallet.hotkey.ss58_address,
    )

    assert commitment == {
        "block": 289,
        "deposit": 0,
        "info": {
            "fields": [
                {
                    "Raw4": "0x00010203",
                },
            ],
        },
    }


@pytest.mark.asyncio
async def test_get_commitments(subtensor, alice_wallet, mocked_transport):
    prefix = "0xca407206ec1ab726b2636c4b145ac287419a60ae8b01e6dcaebd7317e43c69bf"
    key1 = f"{prefix}0200518366b5b1bc7c99d43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d"
    key2 = f"{prefix}0200518366b5b1bc7c99d43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d"

    mocked_transport.responses["state_getKeys"] = {
        "result": [
            key1,
            key2,
        ],
    }
    mocked_transport.responses["state_queryStorageAt"] = {
        "result": [
            {
                "block": "0xe9670fb7fa6fbfd6cad6010501a3b4780f200a9977c802f1eac15bf935cfba48",
                "changes": [
                    [
                        key1,
                        "0x000000000000000021010000040500010203",
                    ],
                    [
                        key2,
                        "0x000000000000000021010000040500010203",
                    ],
                ],
            },
        ],
    }

    netuid = 2

    commitments = await subtensor.commitments.CommitmentOf.fetch(
        netuid,
    )

    assert commitments == [
        (
            (
                2,
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ),
            {
                "deposit": 0,
                "block": 289,
                "info": {
                    "fields": [
                        {
                            "Raw4": "0x00010203",
                        },
                    ],
                },
            },
        ),
        (
            (
                2,
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ),
            {
                "deposit": 0,
                "block": 289,
                "info": {
                    "fields": [
                        {
                            "Raw4": "0x00010203",
                        },
                    ],
                },
            },
        ),
    ]


@pytest.mark.asyncio
async def test_set_commitment(subtensor, alice_wallet):
    extrinsic = await subtensor.commitments.set_commitment(
        netuid=1,
        info={
            "fields": [
                [
                    {
                        "Raw4": "0x00010203",
                    },
                ],
            ],
        },
        era=None,
        wallet=alice_wallet,
    )

    assert extrinsic.subscription.id == "0x53364b7062576d6853326a5341736338"

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "Commitments",
        "set_commitment",
        {
            "netuid": 1,
            "info": {
                "fields": [
                    [
                        {
                            "Raw4": "0x00010203",
                        },
                    ],
                ],
            },
        },
        era=None,
        key=alice_wallet.hotkey,
    )


@pytest.mark.asyncio
async def test_get_revealed_commitments(subtensor, alice_wallet, mocked_transport):
    mocked_transport.responses["state_getStorage"] = {
        "result": "0x040c616263de01000000000000",
    }

    netuid = 1

    revealed = await subtensor.commitments.RevealedCommitments.get(
        netuid,
        alice_wallet.hotkey.ss58_address,
    )

    assert revealed == [
        ("abc", 478),
    ]


@pytest.mark.asyncio
async def test_fetch_revealed_commitments(subtensor, alice_wallet, mocked_transport):
    prefix = "0xca407206ec1ab726b2636c4b145ac2879055a2cffd4b296f38f2de8d9b333cab"
    key1 = f"{prefix}0200518366b5b1bc7c99d43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d"

    mocked_transport.responses["state_getKeys"] = {
        "result": [
            key1,
        ],
    }
    mocked_transport.responses["state_queryStorageAt"] = {
        "result": [
            {
                "block": "0xe9670fb7fa6fbfd6cad6010501a3b4780f200a9977c802f1eac15bf935cfba48",
                "changes": [
                    [
                        key1,
                        "0x040c616263de01000000000000",
                    ],
                ],
            },
        ],
    }

    netuid = 2

    revealed = await subtensor.commitments.RevealedCommitments.fetch(
        netuid,
    )

    assert revealed == [
        (
            (
                2,
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ),
            [("abc", 478)],
        ),
    ]


@pytest.mark.asyncio
async def test_set_revealed_commitment(subtensor, alice_wallet):
    encrypted = "0x010203"
    reveal_round = 100
    extrinsic = await subtensor.commitments.set_commitment(
        netuid=1,
        info={
            "fields": [
                [
                    {
                        "TimelockEncrypted": {
                            "encrypted": encrypted,
                            "reveal_round": reveal_round,
                        },
                    },
                ],
            ],
        },
        era=None,
        wallet=alice_wallet,
    )

    assert extrinsic.subscription.id == "0x53364b7062576d6853326a5341736338"

    subtensor.author.submitAndWatchExtrinsic.assert_called_once_with(
        "Commitments",
        "set_commitment",
        {
            "netuid": 1,
            "info": {
                "fields": [
                    [
                        {
                            "TimelockEncrypted": {
                                "encrypted": encrypted,
                                "reveal_round": reveal_round,
                            },
                        },
                    ],
                ],
            },
        },
        era=None,
        key=alice_wallet.hotkey,
    )


@pytest.fixture
def registration_type():
    # The bundled test metadata predates BigRaw, so mirror its shape in a local registry.
    runtime_config = RuntimeConfigurationObject()
    runtime_config.update_type_registry(load_type_registry_preset("core"))
    runtime_config.update_type_registry(
        {
            "types": {
                "TestData": {
                    "type": "enum",
                    "type_mapping": [
                        ["None", "Null"],
                        ["Raw2", "[u8; 2]"],
                        ["BigRaw", "BoundedVec<u8, ConstU32<512>>"],
                    ],
                },
                "TestInfo": {
                    "type": "struct",
                    "type_mapping": [["fields", "Vec<TestData>"]],
                },
                "TestRegistration": {
                    "type": "struct",
                    "type_mapping": [
                        ["deposit", "u64"],
                        ["block", "u32"],
                        ["info", "TestInfo"],
                    ],
                },
            },
        }
    )
    return lambda: runtime_config.create_scale_object("TestRegistration")


@pytest.mark.parametrize(
    "data",
    [
        b"<F:" + b"x" * 296 + b">",
        b"0x" + b"ab" * 100,
        bytes(range(256)) + b"\xff" * 44,
    ],
)
def test_decode_registration_big_raw_exact_bytes(registration_type, data):
    encoded = registration_type().encode(
        {
            "deposit": 0,
            "block": 5,
            "info": {"fields": [{"BigRaw": data}, {"Raw2": "0x0102"}, "None"]},
        }
    )
    registration = registration_type()
    registration.decode(encoded)

    assert _decode_registration(registration) == {
        "deposit": 0,
        "block": 5,
        "info": {
            "fields": [{"BigRaw": f"0x{data.hex()}"}, {"Raw2": "0x0102"}, "None"],
        },
    }
