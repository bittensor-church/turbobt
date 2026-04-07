import pytest

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
        "info": {
            "fields": [
                "resetBondsFlag",
                {"Raw4": data_str}
            ]
        }
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
    ]
    
    mocked_subtensor.commitments.RevealedCommitments.get.return_value = revealed_data
    
    revealed = await bittensor.subnets[netuid].commitments.get_revealed(hotkey)
    
    assert len(revealed) == 3
    assert revealed[0]["data"] == "data0"
    assert revealed[0]["reveal_block"] == 110
    assert revealed[1]["data"] == "data1"
    assert revealed[1]["reveal_block"] == 120
    assert revealed[2]["data"] == "data2"
    assert revealed[2]["reveal_block"] == 130

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
        ((netuid, hotkey1), {
            "block": 100,
            "deposit": 1000,
            "info": {
                "fields": [
                    {"Raw4": data1_str}
                ]
            }
        }),
        ((netuid, hotkey2), {
            "block": 200,
            "deposit": 2000,
            "info": {
                "fields": [
                    "resetBondsFlag",
                    {
                        "TimelockEncrypted": {
                            "encrypted": data2_str,
                            "reveal_round": 123
                        }
                    }
                ]
            }
        })
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
        ((netuid, hotkey2), [(chr(0) + "revealed2a", 130), (chr(0) + "revealed2b", 140)])
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
async def test_set_revealed_commitment(mocked_subtensor, bittensor, alice_wallet, mocker):
    netuid = 1
    data = "secret"
    encrypted = b"encrypted_secret"
    reveal_round = 456
    
    mocker.patch("bittensor_drand.get_encrypted_commitment", return_value=(encrypted, reveal_round))
    
    result = await bittensor.subnets[netuid].commitments.set_revealed(data, wallet=alice_wallet)
    
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
