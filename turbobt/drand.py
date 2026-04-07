from __future__ import annotations

import typing

from .block import get_ctx_block_hash

if typing.TYPE_CHECKING:
    from .client import Bittensor

class ChainDrand:
    def __init__(self, client: Bittensor):
        self.client = client

    async def get_last_stored_round(self, block_hash: str | None = None) -> int:
        """
        Returns the last stored round from the Drand pallet.

        :param block_hash: The hash of a specific block in the chain.
        :type block_hash: str | None
        :return: The last stored round number.
        :rtype: int
        """

        if not block_hash:
            block_hash = get_ctx_block_hash()

        return await self.client.subtensor.drand.get_last_stored_round(
            block_hash=block_hash,
        )
