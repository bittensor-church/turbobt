import pytest
import pytest_asyncio
from bittensor.keyfiles import Keypair

import turbobt
from turbobt.substrate._hashers import two_x64_concat
from turbobt.subtensor.pallets.commitments import Registration


@pytest.mark.asyncio
async def test_get_commitment(mocked_subtensor, bittensor, alice_wallet):
    hotkey = alice_wallet.hotkey.ss58_address
    netuid = 1

    data_str = "0x64617461"
    data_bytes = bytes.fromhex(data_str[2:])

    registration: Registration = {
        "block": 100,
        "deposit": 1000,
        "info": {"fields": ["resetBondsFlag", {"Raw4": data_str}]},
    }

    mocked_subtensor.commitments.CommitmentOf.get.return_value = registration

    commitment = await bittensor.subnets[netuid].commitments.get(hotkey)

    assert commitment["kind"] == "hex_data"
    assert commitment["data"] == data_bytes
    assert commitment["block"] == 100
    mocked_subtensor.commitments.CommitmentOf.get.assert_called_once_with(
        netuid, hotkey, block_hash=None
    )


@pytest.mark.asyncio
async def test_get_commitment_none(mocked_subtensor, bittensor, alice_wallet):
    hotkey = alice_wallet.hotkey.ss58_address
    netuid = 1

    mocked_subtensor.commitments.CommitmentOf.get.return_value = None

    commitment = await bittensor.subnets[netuid].commitments.get(hotkey)

    assert commitment is None


@pytest.mark.asyncio
async def test_get_revealed_commitments(mocked_subtensor, bittensor, alice_wallet):
    hotkey = alice_wallet.hotkey.ss58_address
    netuid = 1

    revealed_data = [
        (chr(0) + "data0", 110),
        (chr(1) + chr(0) + "data1", 120),
        (chr(2) + chr(0) * 3 + "data2", 130),
        # cases for scalecodec Vec<u8> decode ambiguity resolving
        (f"0x{bytes([128, *('a' * 32).encode()]).hex()}", 140),
        (
            "0xż123456789",
            150,
        ),  # chr(len(bytes("xż123456789".encode())) * 4) + "xż123456789"
    ]

    mocked_subtensor.commitments.RevealedCommitments.get.return_value = revealed_data

    revealed = await bittensor.subnets[netuid].commitments.get_revealed(hotkey)

    assert len(revealed) == 5
    assert revealed[0]["data"] == "data0"
    assert revealed[0]["reveal_block"] == 110
    assert revealed[1]["data"] == "data1"
    assert revealed[1]["reveal_block"] == 120
    assert revealed[2]["data"] == "data2"
    assert revealed[2]["reveal_block"] == 130
    assert revealed[3]["data"] == "a" * 32
    assert revealed[3]["reveal_block"] == 140
    assert revealed[4]["data"] == "xż123456789"
    assert revealed[4]["reveal_block"] == 150


@pytest.mark.asyncio
async def test_get_revealed_commitments_none(mocked_subtensor, bittensor, alice_wallet):
    hotkey = alice_wallet.hotkey.ss58_address
    netuid = 1

    mocked_subtensor.commitments.RevealedCommitments.get.return_value = None

    revealed = await bittensor.subnets[netuid].commitments.get_revealed(hotkey)

    assert revealed is None


@pytest.mark.asyncio
async def test_fetch_commitments(mocked_subtensor, bittensor):
    netuid = 1
    hotkey1 = "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"
    hotkey2 = "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhN"

    data1_str = "0x64617461"
    data1_bytes = bytes.fromhex(data1_str[2:])
    data2_str = "0x656e63727970746564"
    data2_bytes = bytes.fromhex(data2_str[2:])

    registrations = [
        (
            (netuid, hotkey1),
            {"block": 100, "deposit": 1000, "info": {"fields": [{"Raw4": data1_str}]}},
        ),
        (
            (netuid, hotkey2),
            {
                "block": 200,
                "deposit": 2000,
                "info": {
                    "fields": [
                        "resetBondsFlag",
                        {
                            "TimelockEncrypted": {
                                "encrypted": data2_str,
                                "reveal_round": 123,
                            }
                        },
                    ]
                },
            },
        ),
    ]

    mocked_subtensor.commitments.CommitmentOf.fetch.return_value = registrations

    commitments = await bittensor.subnets[netuid].commitments.fetch()

    assert len(commitments) == 2
    assert commitments[hotkey1]["kind"] == "hex_data"
    assert commitments[hotkey1]["data"] == data1_bytes
    assert commitments[hotkey2]["kind"] == "timelock_encrypted"
    assert commitments[hotkey2]["data"] == data2_bytes
    assert commitments[hotkey2]["reveal_round"] == 123


@pytest.mark.asyncio
async def test_fetch_commitments_empty(mocked_subtensor, bittensor):
    netuid = 1
    mocked_subtensor.commitments.CommitmentOf.fetch.return_value = []

    commitments = await bittensor.subnets[netuid].commitments.fetch()

    assert commitments == {}


@pytest.mark.asyncio
async def test_fetch_revealed_commitments(mocked_subtensor, bittensor):
    netuid = 1
    hotkey1 = "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"
    hotkey2 = "5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhN"

    revealed_data = [
        ((netuid, hotkey1), [(chr(0) + "revealed1", 120)]),
        (
            (netuid, hotkey2),
            [(chr(0) + "revealed2a", 130), (chr(0) + "revealed2b", 140)],
        ),
    ]

    mocked_subtensor.commitments.RevealedCommitments.fetch.return_value = revealed_data

    revealed = await bittensor.subnets[netuid].commitments.fetch_revealed()

    assert len(revealed) == 2
    assert revealed[hotkey1][0]["data"] == "revealed1"
    assert revealed[hotkey1][0]["reveal_block"] == 120
    assert len(revealed[hotkey2]) == 2
    assert revealed[hotkey2][0]["data"] == "revealed2a"
    assert revealed[hotkey2][0]["reveal_block"] == 130
    assert revealed[hotkey2][1]["data"] == "revealed2b"
    assert revealed[hotkey2][1]["reveal_block"] == 140


@pytest.mark.asyncio
async def test_fetch_revealed_commitments_empty(mocked_subtensor, bittensor):
    netuid = 1
    mocked_subtensor.commitments.RevealedCommitments.fetch.return_value = []

    revealed = await bittensor.subnets[netuid].commitments.fetch_revealed()

    assert revealed == {}


@pytest.mark.asyncio
async def test_set_commitment(mocked_subtensor, bittensor, alice_wallet):
    netuid = 1
    data = b"new_data"

    await bittensor.subnets[netuid].commitments.set(data, wallet=alice_wallet)

    expected_info = {
        "fields": [
            [
                {
                    f"Raw{len(data)}": data,
                },
            ],
        ],
    }
    mocked_subtensor.commitments.set_commitment.assert_called_once_with(
        netuid, expected_info, wallet=alice_wallet
    )


@pytest.mark.asyncio
async def test_set_revealed_commitment(
    mocked_subtensor, bittensor, alice_wallet, mocker
):
    netuid = 1
    data = "secret"
    encrypted = b"encrypted_secret"
    reveal_round = 456

    mocker.patch(
        "bittensor_drand.get_encrypted_commitment",
        return_value=(encrypted, reveal_round),
    )

    result = await bittensor.subnets[netuid].commitments.set_revealed(
        data, wallet=alice_wallet
    )

    assert result == reveal_round

    expected_info = {
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
    }
    mocked_subtensor.commitments.set_commitment.assert_called_once_with(
        netuid, expected_info, wallet=alice_wallet
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("size", "variant"),
    [(1, "Raw1"), (128, "Raw128"), (129, "BigRaw"), (512, "BigRaw")],
)
async def test_set_commitment_variant(
    mocked_subtensor, bittensor, alice_wallet, size, variant
):
    data = b"x" * size

    await bittensor.subnets[1].commitments.set(data, wallet=alice_wallet)

    mocked_subtensor.commitments.set_commitment.assert_called_once_with(
        1, {"fields": [[{variant: data}]]}, wallet=alice_wallet
    )


@pytest.mark.asyncio
async def test_set_commitment_rejects_over_512_bytes(
    mocked_subtensor, bittensor, alice_wallet
):
    with pytest.raises(ValueError, match="512"):
        await bittensor.subnets[1].commitments.set(b"x" * 513, wallet=alice_wallet)

    mocked_subtensor.commitments.set_commitment.assert_not_called()


@pytest.mark.asyncio
async def test_get_big_raw_commitment(mocked_subtensor, bittensor, alice_wallet):
    data = b"y" * 300
    mocked_subtensor.commitments.CommitmentOf.get.return_value = {
        "block": 100,
        "deposit": 0,
        "info": {"fields": [{"BigRaw": "0x" + data.hex()}]},
    }

    commitment = await bittensor.subnets[1].commitments.get(
        alice_wallet.hotkey.ss58_address
    )

    assert commitment["kind"] == "hex_data"
    assert commitment["data"] == data


# The tests below run against the bundled chain metadata instead of a mocked subtensor,
# so they cover the SCALE encoding and decoding of the chain's Data type.

BIG_RAW_PAYLOADS = [
    pytest.param(b'{"endpoint": "https://example.com"}'.ljust(300), id="text"),
    pytest.param(b"0x" + b"ab" * 100, id="hex-text"),
    pytest.param(bytes(range(256)) + b"\xff" * 44, id="binary"),
]


def _big_raw(data: bytes) -> bytes:
    """SCALE encoding of Data::BigRaw: index 136, compact length, payload."""
    assert 64 <= len(data) < 2**14
    return b"\x88" + ((len(data) << 2) | 1).to_bytes(2, "little") + data


def _registration(field: bytes) -> str:
    """SCALE encoding of a single-field Registration made at block 289."""
    return "0x" + (bytes(8) + (289).to_bytes(4, "little") + b"\x04" + field).hex()


def _commitment_key(netuid: int, keypair: Keypair) -> str:
    prefix = "0xca407206ec1ab726b2636c4b145ac287419a60ae8b01e6dcaebd7317e43c69bf"
    return (
        prefix
        + netuid.to_bytes(2, "little").hex()
        + two_x64_concat(keypair.public_key).hex()
    )


@pytest_asyncio.fixture
async def chain_bittensor(mocked_transport, alice_wallet):
    async with turbobt.Bittensor(
        "ws://127.0.0.1:9944",
        transport=mocked_transport,
        verify=None,
        wallet=alice_wallet,
    ) as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.parametrize("data", BIG_RAW_PAYLOADS)
async def test_get_big_raw_commitment_from_chain(
    chain_bittensor, mocked_transport, alice_wallet, data
):
    mocked_transport.responses["state_getStorage"] = {
        "result": _registration(_big_raw(data)),
    }

    commitment = await chain_bittensor.subnets[1].commitments.get(
        alice_wallet.hotkey.ss58_address
    )

    assert commitment == {"kind": "hex_data", "data": data, "block": 289}


@pytest.mark.asyncio
async def test_fetch_big_raw_commitments_from_chain(chain_bittensor, mocked_transport):
    alice = Keypair.create_from_uri("//Alice")
    bob = Keypair.create_from_uri("//Bob")
    text = b"miner endpoint ".ljust(200)
    hex_text = b"0x" + b"ab" * 100
    changes = [
        [_commitment_key(2, alice), _registration(_big_raw(text))],
        [_commitment_key(2, bob), _registration(_big_raw(hex_text))],
    ]
    mocked_transport.responses["state_getKeys"] = {
        "result": [key for key, _ in changes],
    }
    mocked_transport.responses["state_queryStorageAt"] = {
        "result": [{"block": "0x" + "00" * 32, "changes": changes}],
    }

    commitments = await chain_bittensor.subnets[2].commitments.fetch()

    assert commitments == {
        alice.ss58_address: {"kind": "hex_data", "data": text, "block": 289},
        bob.ss58_address: {"kind": "hex_data", "data": hex_text, "block": 289},
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("size", "encoded_prefix"),
    [
        pytest.param(128, bytes([129]), id="Raw128"),
        pytest.param(129, b"\x88" + bytes([0x05, 0x02]), id="BigRaw-129"),
        pytest.param(512, b"\x88" + bytes([0x01, 0x08]), id="BigRaw-512"),
    ],
)
async def test_set_commitment_encoding(
    chain_bittensor, mocked_transport, mocker, size, encoded_prefix
):
    mocker.patch("turbobt.substrate.extrinsic.ExtrinsicResult.wait_for_finalization")
    mocked_transport.responses["system_accountNextIndex"] = {"result": 1}
    mocked_transport.responses["chain_getHeader"] = {
        "result": {
            "parentHash": "0x" + "00" * 32,
            "number": "0xf54",
            "stateRoot": "0x" + "00" * 32,
            "extrinsicsRoot": "0x" + "00" * 32,
            "digest": {"logs": []},
        },
    }
    mocked_transport.responses["chain_getBlockHash"] = {"result": "0x" + "00" * 32}
    mocked_transport.responses["author_submitAndWatchExtrinsic"] = {
        "result": "0x53364b7062576d6853326a5341736338",
    }
    data = bytes(range(256)) * 2
    data = data[:size]

    await chain_bittensor.subnets[1].commitments.set(data)

    (extrinsic,) = (
        bytes.fromhex(call.args[0].params["bytes"][2:])
        for call in mocked_transport.send.call_args_list
        if call.args[0].method == "author_submitAndWatchExtrinsic"
    )
    # set_commitment(netuid=1, info) with a single field ends the extrinsic.
    assert extrinsic.endswith(b"\x01\x00\x04" + encoded_prefix + data)
