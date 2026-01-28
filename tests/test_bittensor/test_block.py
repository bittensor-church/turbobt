import datetime

import pytest


@pytest.mark.asyncio
async def test_blocks_references(bittensor):
    block_ref = bittensor.blocks[1]

    assert block_ref.hash is None
    assert block_ref.number == 1

    block_ref = bittensor.blocks[
        "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
    ]

    assert (
        block_ref.hash
        == "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
    )
    assert block_ref.number is None

    with pytest.raises(TypeError):
        bittensor.blocks[None]


@pytest.mark.asyncio
async def test_blocks_head(mocked_subtensor, bittensor):
    mocked_subtensor.chain.getHeader.return_value = {
        "number": 1,
    }
    mocked_subtensor.chain.getBlockHash.return_value = (
        "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
    )

    block_ref = await bittensor.blocks.head()

    assert block_ref.number == 1
    assert block_ref.hash is None

    block = await bittensor.head.get()

    assert block.number == 1
    assert (
        block.hash
        == "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
    )


@pytest.mark.asyncio
async def test_block_context_by_number(mocked_subtensor, bittensor):
    mocked_subtensor.chain.getBlockHash.return_value = (
        "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
    )

    block_ref = bittensor.blocks[1]

    async with block_ref as block:
        assert (
            block.hash
            == "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
        )
        assert block.number == 1

        await bittensor.subnet(1).get()

        mocked_subtensor.subnet_info.get_dynamic_info.assert_called_once_with(
            1,
            block_hash="0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b",
        )


@pytest.mark.asyncio
async def test_block_context_by_hash(mocked_subtensor, bittensor):
    block_ref = bittensor.blocks[
        "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
    ]

    async with block_ref as block:
        assert (
            block.hash
            == "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
        )
        assert block.number is None

        await bittensor.subnet(1).get()

        mocked_subtensor.subnet_info.get_dynamic_info.assert_called_once_with(
            1,
            block_hash="0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b",
        )


@pytest.mark.asyncio
async def test_nested_context(mocked_subtensor, bittensor):
    NEWEST_BLOCK = "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
    OLDEST_BLOCK = "0x1fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"

    mocked_subtensor.chain.getHeader.return_value = {
        "number": 100,
    }
    mocked_subtensor.chain.getBlockHash.return_value = NEWEST_BLOCK

    async with bittensor.head as block:
        assert block.number == 100
        assert block.hash == NEWEST_BLOCK

        await bittensor.subnet(1).get()

        mocked_subtensor.subnet_info.get_dynamic_info.assert_called_once_with(
            1,
            block_hash=NEWEST_BLOCK,
        )

        mocked_subtensor.chain.getBlockHash.return_value = OLDEST_BLOCK

        async with bittensor.blocks[1] as first_block:
            assert first_block.number == 1
            assert (
                first_block.hash
                == "0x1fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
            )

            await bittensor.subnet(1).get()

            mocked_subtensor.subnet_info.get_dynamic_info.assert_called_with(
                1,
                block_hash=OLDEST_BLOCK,
            )

        await bittensor.subnet(1).get()

        mocked_subtensor.subnet_info.get_dynamic_info.assert_called_with(
            1,
            block_hash=NEWEST_BLOCK,
        )


@pytest.mark.asyncio
async def test_block_get_timestamp(mocked_subtensor, bittensor):
    mocked_subtensor.chain.getBlockHash.return_value = (
        "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b"
    )
    mocked_subtensor.timestamp.Now.get.return_value = 1751463936000

    block = await bittensor.head.get()
    block_timestamp = await block.get_timestamp()

    assert block_timestamp == datetime.datetime(
        2025,
        7,
        2,
        13,
        45,
        36,
        tzinfo=datetime.UTC,
    )

    mocked_subtensor.timestamp.Now.get.assert_awaited_once_with(
        "0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b",
    )
