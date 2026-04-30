import pytest


@pytest.mark.asyncio
async def test_get_last_stored_round(mocked_subtensor, bittensor):
    expected_round = 12345
    mocked_subtensor.drand.get_last_stored_round.return_value = expected_round

    result = await bittensor.drand.get_last_stored_round()
    assert result == expected_round
    mocked_subtensor.drand.get_last_stored_round.assert_called_once_with(
        block_hash=None
    )

    mocked_subtensor.drand.get_last_stored_round.reset_mock()


@pytest.mark.asyncio
async def test_get_last_stored_round_with_block_hash(mocked_subtensor, bittensor):
    expected_round = 54321
    block_hash = "0x" + "a" * 64
    mocked_subtensor.drand.get_last_stored_round.return_value = expected_round

    result = await bittensor.drand.get_last_stored_round(block_hash=block_hash)
    assert result == expected_round
    mocked_subtensor.drand.get_last_stored_round.assert_called_once_with(
        block_hash=block_hash
    )
