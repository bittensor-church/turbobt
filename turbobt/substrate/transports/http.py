import typing

import httpx

from .._models import Request, Response
from .base import BaseTransport

T = typing.TypeVar("T", bound="HTTPTransport")

__all__ = [
    "HTTPTransport",
]


class HTTPTransport(BaseTransport):
    def __init__(
        self,
        url: str,
        **kwargs,
    ):
        self._client = httpx.AsyncClient(
            base_url=url,
            **kwargs,
        )

        self._id = 0

    async def __aenter__(self: T) -> T:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self._client.__aexit__(*args, **kwargs)

    async def send(self, request: Request) -> Response:
        self._id += 1

        response = await self._client.post(
            "/",
            headers={
                "Accept": "application/json",
            },
            json={
                "method": request.method,
                "params": self._wire_params(request.params),
                "id": self._id,
                "jsonrpc": "2.0",
            },
        )
        response_body = response.json()

        if "error" in response_body:
            return Response(
                error=response_body["error"],
                request=request,
                result=None,
            )

        return Response(
            request=request,
            result=response_body["result"],
        )

    async def close(self):
        return await self._client.aclose()
