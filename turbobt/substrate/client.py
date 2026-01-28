import asyncio
import ssl
import types
import typing

import scalecodec.base
import scalecodec.type_registry

from ._models import (
    Request,
    Subscription,
)
from ._scalecodec import load_type_registry_v15_types
from .exceptions import (
    CustomTransactionError,
    SubstrateException,
    UnknownBlock,
)
from .pallets import (
    Author,
    Chain,
    State,
    System,
    Timestamp,
    Utility,
)
from .runtime import (
    Metadata,
)
from .transports.base import BaseTransport
from .transports.websocket import WebSocketTransport

T = typing.TypeVar("T", bound="Substrate")


class Substrate:
    """
    Async Substrate Client.
    """

    def __init__(
        self,
        uri: str = "finney",
        *,
        verify: ssl.SSLContext | bool | None = None,
        transport: BaseTransport | None = None,
        timeout: float = 15.0,
    ):
        self._transport = self._init_transport(
            uri=uri,
            verify=verify,
            transport=transport,
        )

        self._registry = None
        self._metadata = None
        self._apis = None

        self.author = Author(self)
        self.chain = Chain(self)
        self.metadata = Metadata(self)
        self.state = State(self)
        self.system = System(self)
        self.timestamp = Timestamp(self)
        self.utility = Utility(self)

        self.__lock = asyncio.Lock()

    async def __aenter__(self: T) -> T:
        await self._transport.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: types.TracebackType | None = None,
    ) -> None:
        await self._transport.__aexit__(exc_type, exc_value, traceback)

    def _init_transport(
        self,
        uri: str,
        verify: ssl.SSLContext | bool | None,
        transport: BaseTransport | None = None,
    ) -> BaseTransport:
        if transport is not None:
            return transport

        if not isinstance(uri, str):
            raise TypeError(f'Invalid "uri" param: {uri!r}')

        kwargs = {}

        if verify is not None:
            kwargs["ssl"] = verify

        if uri == "finney":
            uri = "wss://entrypoint-finney.opentensor.ai"
        elif uri == "archive":
            uri = "wss://archive.chain.opentensor.ai:443"
        elif uri == "test":
            uri = "wss://test.finney.opentensor.ai:443"
        elif uri == "local":
            uri = "ws://127.0.0.1:9944"

        if uri.startswith(("ws://", "wss://")):
            return WebSocketTransport(
                uri,
                **kwargs,
            )

        if uri.startswith(("http://", "https://")):
            from .transports.http import HTTPTransport

            return HTTPTransport(
                uri,
                **kwargs,
            )

        raise ValueError(f'Invalid "uri" param: {uri}')

    async def _init_runtime(self) -> scalecodec.base.RuntimeConfigurationObject:
        async with self.__lock:
            if self._registry:
                return

            runtime_config = scalecodec.base.RuntimeConfigurationObject()
            runtime_config.update_type_registry(
                scalecodec.type_registry.load_type_registry_preset(name="core"),
            )

            # patching-in MetadataV15 support
            runtime_config.update_type_registry_types(load_type_registry_v15_types())
            runtime_config.type_registry["types"]["metadataall"].type_mapping.append(
                ["V15", "MetadataV15"],
            )

            self._registry = runtime_config

            metadata = await self.metadata.metadata_at_version(15)
            metadata15 = metadata.value[1]["V15"]

            runtime_config.add_portable_registry(metadata)

            self._registry = runtime_config
            self._metadata = metadata
            self._apis = {
                api["name"]: api
                | {
                    "methods": {
                        api_method["name"]: api_method for api_method in api["methods"]
                    }
                }
                for api in metadata15["apis"]
            }

    async def close(self) -> None:
        await self._transport.close()

    async def rpc(self, method: str, params: dict | list) -> int | bytearray | dict:
        """
        Send a JSON-RPC Request.

        :param method: The name of the method to be invoked.
        :type method: str
        :param params: Parameter values to be used during the invocation of the method.
        :type params: dict | list
        :return: JSON-RPC Response
        :rtype: int | bytearray | dict
        """

        if isinstance(params, dict):
            params_list = list(params.values())
            while params_list and params_list[-1] is None:
                params_list.pop()
            params = params_list

        request = Request(
            method=method,
            params=params,
        )

        response = await self._transport.send(request)

        if response.error:
            # https://docs.bittensor.com/errors/custom
            if response.error["code"] == 1010:
                raise CustomTransactionError(response.error)

            if response.error["code"] == 4003:
                raise UnknownBlock(response.error["message"])

            raise SubstrateException(response.error["message"])

        result = response.result

        if isinstance(result, str) and result.startswith("0x"):
            return bytearray.fromhex(result[2:])

        return result

    async def subscribe(self, subscription_id: str) -> Subscription:
        return Subscription(
            subscription_id,
            self._transport.subscribe(subscription_id),
        )

    async def unsubscribe(self, subscription_id: str):
        self._transport.unsubscribe(subscription_id)
