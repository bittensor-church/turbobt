import typing

import scalecodec.utils.ss58

from ._base import RuntimeApi


class NeuronLite(typing.TypedDict):
    coldkey: str
    hotkey: str
    stake: dict[str, int]
    uid: int


class NeuronInfoRuntimeApi(RuntimeApi):
    async def get_neuron(
        self,
        netuid: int,
        uid: int,
        block_hash: str | None = None,
    ) -> dict | None:
        """
        Fetches information about a specific neuron in a subnet.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param uid: The unique identifier of the neuron within the subnet.
        :type uid: int
        :param block_hash: Optional block hash to query the neuron state at a specific block.
        :type block_hash: str, optional
        :return: A dictionary containing neuron information or None if the neuron does not exist.
        :rtype: dict or None
        """

        neuron = await self.subtensor.api_call(
            "NeuronInfoRuntimeApi",
            "get_neuron",
            netuid=netuid,
            uid=uid,
            block_hash=block_hash,
        )

        if not neuron:
            return None

        return self._decode_neuron(neuron)

    async def get_neurons_lite(
        self,
        netuid: int,
        block_hash=None,
    ) -> list[NeuronLite] | None:
        """
        Fetches a lite version of all neurons in a subnet.

        :param netuid: The unique identifier of the subnet.
        :type netuid: int
        :param block_hash: Optional block hash to query the neuron states at a specific block.
        :type block_hash: str, optional
        :return: A list of dictionaries containing lite neuron information, or None if no neurons are found.
        :rtype: list[NeuronLite] or None
        """

        result = await self.subtensor.api_call(
            "NeuronInfoRuntimeApi",
            "get_neurons_lite",
            netuid=netuid,
            block_hash=block_hash,
        )

        if not result:
            return None

        return [self._decode_neuron(neuron) for neuron in result]

    def _decode_neuron(self, neuron: dict) -> dict:
        for key in ("coldkey", "hotkey"):
            neuron[key] = scalecodec.utils.ss58.ss58_encode(neuron[key])

        neuron["stake"] = {
            scalecodec.utils.ss58.ss58_encode(key): value
            for key, value in neuron["stake"]
        }

        return neuron
