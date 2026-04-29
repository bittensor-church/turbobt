import asyncio
import types
import typing

from .._models import Request, Response

T = typing.TypeVar("T", bound="BaseTransport")

__all__ = [
    "BaseTransport",
]


class Timeout:
    def __init__(
        self,
        connect: float | None = None,
        read: float | None = None,
        write: float | None = None,
    ):
        self.connect = connect
        self.read = read
        self.write = write


class BaseTransport:
    @staticmethod
    def _wire_params(params: dict | list) -> list:
        # this is shit; if we need positional params we'll have to do it properly
        if isinstance(params, dict):
            return list(params.values())

        return params

    async def __aenter__(self: T) -> T:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: types.TracebackType | None = None,
    ) -> None:
        await self.close()

    async def send(self, request: Request) -> Response:
        raise NotImplementedError

    async def close(self) -> None:
        pass

    def subscribe(self, subscription_id) -> asyncio.Queue:
        raise NotImplementedError

    def unsubscribe(self, subscription_id) -> asyncio.Queue | None:
        raise NotImplementedError
