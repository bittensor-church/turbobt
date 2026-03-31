from __future__ import annotations

import typing

from ...substrate.pallets._types import StorageValue
from ._base import Pallet

if typing.TYPE_CHECKING:
    from .. import Subtensor


class Drand(Pallet):
    def __init__(self, subtensor: Subtensor):
        super().__init__(subtensor)

        self.LastStoredRound = StorageValue[int](
            subtensor,
            "Drand",
            "LastStoredRound",
        )

    async def get_last_stored_round(self, block_hash: str | None = None) -> int:
        """
        Returns the last stored round from the Drand pallet.

        :param block_hash: The hash of a specific block in the chain.
        :type block_hash: str | None
        :return: The last stored round number.
        :rtype: int
        """

        return await self.LastStoredRound.get(block_hash=block_hash)
