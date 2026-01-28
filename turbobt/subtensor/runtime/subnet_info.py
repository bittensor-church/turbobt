import typing

import scalecodec.utils.ss58

from ._base import RuntimeApi


class DynamicInfo(typing.TypedDict):
    subnet_name: str
    token_symbol: str
    owner_coldkey: str
    owner_hotkey: str
    tempo: float
    subnet_identity: str
    # ...


class SubnetHyperparams(typing.TypedDict):
    max_weights_limit: int
    # ...


class SubnetHyperparamsV2(typing.TypedDict):
    max_weights_limit: int
    # ...


class SubnetState(typing.TypedDict):
    hotkeys: list[str]
    coldkeys: list[str]
    # ...


class SubnetInfoRuntimeApi(RuntimeApi):
    async def get_dynamic_info(
        self,
        netuid: int,
        block_hash=None,
    ) -> DynamicInfo | None:
        """
        Fetches dynamic information about a subnet.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param block_hash: Optional block hash to query the subnet state at a specific block.
        :type block_hash: str, optional
        :return: A dictionary containing dynamic subnet information, or None if no subnet is found.
        :rtype: dict | None
        """

        result = await self.subtensor.api_call(
            "SubnetInfoRuntimeApi",
            "get_dynamic_info",
            netuid=netuid,
            block_hash=block_hash,
        )

        if not result:
            return None

        for key in ("subnet_name", "token_symbol"):
            result[key] = bytes(result[key]).decode()

        for key in ("owner_coldkey", "owner_hotkey"):
            result[key] = scalecodec.utils.ss58.ss58_encode(
                result[key],
            )

        return result

    async def get_subnet_hyperparams(
        self,
        netuid: int,
        block_hash=None,
    ) -> SubnetHyperparams | None:
        """
        Fetches hyperparameters of a subnet.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param block_hash: Optional block hash to query the subnet state at a specific block.
        :type block_hash: str, optional
        :return: A dictionary containing hyperparameters of the subnet, or None if no subnet is found.
        :rtype: Hyperparameters | None
        """

        hyperparameters = await self.subtensor.api_call(
            "SubnetInfoRuntimeApi",
            "get_subnet_hyperparams",
            netuid=netuid,
            block_hash=block_hash,
        )

        if not hyperparameters:
            return None

        return hyperparameters

    async def get_subnet_hyperparams_v2(
        self,
        netuid: int,
        block_hash=None,
    ) -> SubnetHyperparamsV2 | None:
        """
        Fetches hyperparameters version 2 of a subnet.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param block_hash: Optional block hash to query the subnet state at a specific block.
        :type block_hash: str, optional
        :return: A dictionary containing hyperparameters of the subnet, or None if no subnet is found.
        :rtype: SubnetHyperparamsV2 | None
        """

        hyperparameters = await self.subtensor.api_call(
            "SubnetInfoRuntimeApi",
            "get_subnet_hyperparams_v2",
            netuid=netuid,
            block_hash=block_hash,
        )

        if not hyperparameters:
            return None

        return hyperparameters

    async def get_subnet_state(
        self,
        netuid: int,
        block_hash=None,
    ) -> SubnetState | None:
        """
        Fetches the state of a subnet.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param block_hash: Optional block hash to query the subnet state at a specific block.
        :type block_hash: str, optional
        :return: A dictionary containing the subnet state, or None if no subnet is found.
        :rtype: SubnetState | None
        """

        subnet_state = await self.subtensor.api_call(
            "SubnetInfoRuntimeApi",
            "get_subnet_state",
            netuid=netuid,
            block_hash=block_hash,
        )

        if not subnet_state:
            return

        subnet_state["hotkeys"] = [
            scalecodec.utils.ss58.ss58_encode(key) for key in subnet_state["hotkeys"]
        ]
        subnet_state["coldkeys"] = [
            scalecodec.utils.ss58.ss58_encode(key) for key in subnet_state["coldkeys"]
        ]

        return subnet_state
