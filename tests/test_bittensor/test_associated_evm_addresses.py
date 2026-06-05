import pytest

from turbobt.subtensor.pallets.subtensor_module import AssociatedEvmAddress


@pytest.mark.asyncio
async def test_fetch_associated_evm_addresses(mocked_subtensor, bittensor):
    # Mock the response from the subtensor module
    mocked_subtensor.subtensor_module.AssociatedEvmAddress.fetch.return_value = [
        ((1, 0), AssociatedEvmAddress("0x77407f1709d339f5583feac922c0592e248f785f", 5668432)),
        ((1, 1), AssociatedEvmAddress("0xa873b6e2ed71bae54f232fb622b713239f0ec54c", 5471944)),
    ]

    subnet = bittensor.subnet(1)
    evm_addresses = await subnet.associated_evm_addresses.fetch()

    assert evm_addresses == {
        0: AssociatedEvmAddress("0x77407f1709d339f5583feac922c0592e248f785f", 5668432),
        1: AssociatedEvmAddress("0xa873b6e2ed71bae54f232fb622b713239f0ec54c", 5471944),
    }
    
    mocked_subtensor.subtensor_module.AssociatedEvmAddress.fetch.assert_called_once_with(
        1,
        block_hash=None
    )
