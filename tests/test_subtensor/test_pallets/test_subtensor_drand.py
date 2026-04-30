import pytest


@pytest.mark.asyncio
async def test_get_last_stored_round(subtensor, mocked_transport):
    mocked_transport.responses.update(
        {
            "state_getStorage": {
                "result": "0x1b32000000000000"  # Hex representation of 12827 in u64 (little-endian)
            }
        }
    )

    last_round = await subtensor.drand.get_last_stored_round()

    assert last_round == 12827
    mocked_transport.send.assert_called()
    call_args = mocked_transport.send.call_args[0][0]
    assert call_args.method == "state_getStorage"
    assert (
        call_args.params["key"]
        == "0xa285cdb66e8b8524ea70b1693c7b1e05087f3dd6e0ceded0e388dd34f810a73d"
    )
