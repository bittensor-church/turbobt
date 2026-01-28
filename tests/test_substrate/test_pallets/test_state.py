import pytest


@pytest.mark.asyncio
async def test_call(substrate, mocked_transport):
    mocked_transport.responses["state_call"]["Metadata_metadata_at_version"] = {
        "result": "0x00",
    }

    result = await substrate.state.call(
        method="Metadata_metadata_at_version",
        data="0x0f000000",
        block_hash="0x3fe8c77075d8194ed0bb7fd70d7b8cc91c12826c7f04df9f04c4235f0f6a966b",
    )

    assert result == b"\x00"
