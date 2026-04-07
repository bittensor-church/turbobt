import pytest


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
        key=alice_wallet.coldkey,
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
        key=alice_wallet.coldkey,
    )
