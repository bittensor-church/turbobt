import asyncio

import bittensor_wallet

from .batch import Batch, Transaction
from .block import BlockReference, Blocks
from .drand import ChainDrand
from .subnet import (
    SubnetReference,
    Subnets,
)
from .subtensor import CacheSubtensor


class Bittensor:
    def __init__(
        self,
        *args,
        wallet: bittensor_wallet.Wallet | None = None,
        **kwargs,
    ):
        self.subtensor = CacheSubtensor(
            *args,
            **kwargs,
        )

        self.subnets = Subnets(self)
        self.drand = ChainDrand(self)
        self.blocks = Blocks(self)
        self.wallet = wallet

    async def __aenter__(self):
        await self.subtensor.__aenter__()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.subtensor.__aexit__(*args, **kwargs)

    @property
    def head(self) -> BlockReference:
        return BlockReference(
            -1,
            client=self,
        )

    async def batch(self, *calls):
        async with Batch(self):
            await asyncio.gather(*calls)

    def block(self, block_number: int) -> BlockReference:
        return BlockReference(
            block_number,
            client=self,
        )

    async def close(self):
        await self.subtensor.close()

    def subnet(self, netuid: int) -> SubnetReference:
        return SubnetReference(
            netuid,
            client=self,
        )

    def transaction(self) -> Transaction:
        return Transaction(self)
