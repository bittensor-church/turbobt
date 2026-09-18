from bittensor.wallet import Wallet

from ...substrate.extrinsic import ExtrinsicResult
from ...substrate.pallets.author import DEFAULT_ERA, Era
from ._base import Pallet


class Sudo(Pallet):
    async def sudo(
        self,
        call_module: str,
        call_function: str,
        call_args: dict,
        wallet: Wallet,
        era: Era | None = DEFAULT_ERA,
    ) -> ExtrinsicResult:
        """
        Calls a function with sudo permissions.

        :param call_module: The module to call.
        :type call_module: str
        :param call_function: The function to call.
        :type call_function: str
        :param call_args: The arguments to pass to the function.
        :type call_args: dict
        :param wallet: The wallet associated with the account making this call.
        :type wallet:
        :return: An asynchronous result of the extrinsic submission.
        :rtype: ExtrinsicResult
        """

        await self.subtensor._init_runtime()

        call = self.subtensor._registry.create_scale_object(
            "Call",
            metadata=self.subtensor._metadata,
        )
        call.encode(
            {
                "call_module": call_module,
                "call_function": call_function,
                "call_args": call_args,
            }
        )

        return await self.subtensor.author.submitAndWatchExtrinsic(
            call_module="Sudo",
            call_function="sudo",
            call_args={
                "call": call,
            },
            key=wallet.coldkey,
            era=era,
        )
