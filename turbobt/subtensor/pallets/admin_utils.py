from bittensor.wallet import Wallet

from ...substrate.extrinsic import ExtrinsicResult
from ...substrate.pallets.author import DEFAULT_ERA, Era
from ._base import Pallet


class AdminUtils(Pallet):
    async def sudo_set_commit_reveal_weights_enabled(
        self,
        netuid: int,
        enabled: bool,
        wallet: Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Enables/disables commit-reveal weights for a subnet.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param enabled: Whether or not to enable commit-reveal weights.
        :type enabled: bool
        :param wallet: The wallet associated with the account making this call.
        :type wallet:
        :return: An asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        return await self.subtensor.author.submitAndWatchExtrinsic(
            "AdminUtils",
            "sudo_set_commit_reveal_weights_enabled",
            {
                "netuid": netuid,
                "enabled": enabled,
            },
            key=wallet.coldkey,
            era=era,
        )

    async def sudo_set_tempo(
        self,
        netuid: int,
        tempo: int,
        wallet: Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Sets the tempo for a subnet.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param tempo: The tempo to set.
        :type tempo: int
        :param wallet: The wallet associated with the account making this call.
        :type wallet:
        :return: An asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        return await self.subtensor.sudo.sudo(
            "AdminUtils",
            "sudo_set_tempo",
            {
                "netuid": netuid,
                "tempo": tempo,
            },
            wallet=wallet,
            era=era,
        )

    async def sudo_set_weights_set_rate_limit(
        self,
        netuid: int,
        weights_set_rate_limit: int,
        wallet: Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Sets the rate limit for setting weights for a subnet.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param weights_set_rate_limit: The rate limit to set.
        :type weights_set_rate_limit: int
        :param wallet: The wallet associated with the account making this call.
        :type wallet:
        :return: An asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        return await self.subtensor.sudo.sudo(
            "AdminUtils",
            "sudo_set_weights_set_rate_limit",
            {
                "netuid": netuid,
                "weights_set_rate_limit": weights_set_rate_limit,
            },
            wallet=wallet,
            era=era,
        )
