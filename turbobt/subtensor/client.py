import scalecodec

from turbobt.substrate.exceptions import CustomTransactionError
from turbobt.subtensor.exceptions import (
    SUBSTRATE_CUSTOM_ERRORS,
    SubtensorException,
)

from ..substrate.client import Substrate
from .cache import (
    CacheControl,
    CacheTransport,
    InMemoryStorage,
)
from .pallets import (
    AdminUtils,
    Commitments,
    Drand,
    SubtensorModule,
    Sudo,
)
from .runtime import (
    NeuronInfoRuntimeApi,
    SubnetInfoRuntimeApi,
)


class Subtensor(Substrate):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """
        Initialize a Subtensor instance.
        See Substrate.__init__ for more details.
        """

        super().__init__(*args, **kwargs)

        self.admin_utils = AdminUtils(self)
        self.commitments = Commitments(self)
        self.drand = Drand(self)
        self.subtensor_module = SubtensorModule(self)
        self.sudo = Sudo(self)

        self.neuron_info = NeuronInfoRuntimeApi(self)
        self.subnet_info = SubnetInfoRuntimeApi(self)

    async def api_call(
        self,
        api: str,
        method: str,
        block_hash: str | None,
        **kwargs,
    ):
        await self._init_runtime()

        api = self._apis[api]
        method = api["methods"][method]
        data = bytearray()

        for param in method["inputs"]:
            scale = self._registry.create_scale_object(f"scale_info::{param['type']}")
            scale.encode(kwargs[param["name"]])

            data.extend(scale.data.data)

        response = await self.state.call(
            f"{api['name']}_{method['name']}",
            data.hex(),
            block_hash,
        )

        if not isinstance(response, bytearray):
            return response

        output = self._registry.create_scale_object(f"scale_info::{method['output']}")

        return output.decode(
            scalecodec.ScaleBytes(response),
        )

    async def rpc(self, method: str, params: dict) -> int | bytearray | dict:
        try:
            return await super().rpc(method, params)
        except CustomTransactionError as e:
            error = e.args[0]

            # https://docs.bittensor.com/errors/custom
            try:
                error_cls = SUBSTRATE_CUSTOM_ERRORS[error["data"]]
            except KeyError:
                error_cls = SubtensorException

            raise error_cls(error["message"])


class CacheSubtensor(Subtensor):
    def _init_transport(self, *args, **kwargs):
        transport = super()._init_transport(*args, **kwargs)

        return CacheTransport(
            transport=transport,
            cache_control=CacheControl(),
            storage=InMemoryStorage(),
        )
