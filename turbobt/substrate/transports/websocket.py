import asyncio
import contextlib
import json
import logging
import os
import traceback
import types
import typing

import websockets.asyncio.client

from .._models import Request, Response
from .base import BaseTransport, Timeout

T = typing.TypeVar("T", bound="WebSocketTransport")

__all__ = [
    "WebSocketTransport",
]

logger = logging.getLogger(__name__)

class WebSocketTransport(BaseTransport):
    def __init__(
        self,
        uri: str,
        retries: int = int(os.environ.get('TURBOBT_RETRIES', 0)),
        timeout: Timeout = Timeout(
            connect=15.0,
            read=60.0,
            write=5.0,
        ),
        **kwargs,
    ):
        self.__lock = asyncio.Lock()
        self.__connections = self._connections_generator(
            websockets.asyncio.client.connect(
                uri,
                open_timeout=timeout.connect,
                **kwargs,
            ),
        )

        self._retries = retries
        self._timeout = timeout
        self._futures: dict[int, asyncio.Future] = {}
        self._subscriptions: dict[str, asyncio.Queue] = {}
        self._connection: websockets.asyncio.client.ClientConnection | None = None

        self._id = 0

    async def __aenter__(self: T) -> T:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: types.TracebackType | None = None,
    ) -> None:
        await self.close()

    @contextlib.asynccontextmanager
    async def connected(self):
        async with self.__lock:
            connection = await self.__connections.__anext__()

        try:
            yield connection
        except websockets.exceptions.ConnectionClosed as e:
            async with self.__lock:
                await self.__connections.athrow(e)

    async def _connections_generator(
        self,
        connect: websockets.asyncio.client.connect,
    ):
        task = None
        delays = None
        retries_left = self._retries

        while True:
            try:
                if self._connection:
                    await self._connection.close()
            except Exception as e:
                logger.info(f"Error when closing connection: {e!r}")
            try:
                async with connect as self._connection:
                    task = asyncio.create_task(self._recv(self._connection))
                    delays = None
                    retries_left = self._retries

                    while True:
                        yield self._connection
            except Exception as exc:
                retries_left -= 1

                try:
                    new_exc = connect.process_exception(exc)
                except Exception as raised_exc:
                    new_exc = raised_exc

                if new_exc or retries_left < 0:
                    connect.logger.exception("connect failed", exc_info=new_exc or exc)
                    yield
                    retries_left = self._retries
                    delays = None
                    continue

                if delays is None:
                    delays = websockets.asyncio.client.backoff()

                delay = next(delays)

                connect.logger.info(
                    "connect failed; reconnecting in %.1f seconds: %s",
                    delay,
                    traceback.format_exception_only(exc)[0].strip(),
                )

                await asyncio.sleep(delay)
            finally:
                if task:
                    task.cancel()  # TODO needed?

    async def _recv(
        self,
        connection: websockets.asyncio.client.ClientConnection,
    ) -> None:
        try:
            async for message in connection:
                message_body = json.loads(message)

                try:
                    future = self._futures.pop(message_body["id"])
                except KeyError:
                    try:
                        subscription = self._subscriptions[
                            message_body["params"]["subscription"]
                        ]
                    except KeyError:
                        # TODO capture notifications automatically?
                        continue

                    subscription.put_nowait(message_body["params"]["result"])
                    continue

                future.set_result(message_body)
                await asyncio.sleep(0)  # gives time for subscription?
        except asyncio.CancelledError:  # TODO WS Closed
            pass
            # await connection.close()
        except websockets.exceptions.ConnectionClosed as exc:
            for subscription in self._subscriptions.values():
                subscription.put_nowait(exc)

    async def send(self, request: Request) -> Response:
        """
        Send a JSON-RPC request over the WebSocket connection

        :param request: The JSON-RPC request to be sent.
        :type request: Request
        :return: The response received from the WebSocket connection.
        :rtype: Response
        """

        self._id += 1

        future = asyncio.get_event_loop().create_future()
        future_id = self._id

        try:
            self._futures[future_id] = future

            async with self.connected() as connection:
                async with asyncio.timeout(self._timeout.write):
                    await connection.send(
                        json.dumps(
                            {
                                "method": request.method,
                                "params": request.params,
                                "id": future_id,
                                "jsonrpc": "2.0",
                            }
                        ),
                    )

            async with asyncio.timeout(self._timeout.read):
                response = await future

            if "error" in response:
                return Response(
                    error=response["error"],
                    request=request,
                    result=None,
                )

            return Response(
                request=request,
                result=response["result"],
            )
        except Exception:
            del self._futures[future_id]
            raise

    async def close(self):
        for future in self._futures.values():
            future.cancel()

        self._futures.clear()
        self._subscriptions.clear()

        await self.__connections.aclose()

        try:
            if self._connection:
                await self._connection.close()
        except Exception as e:
            logger.info(f"Error when closing connection: {e!r}")

    def subscribe(self, subscription_id) -> asyncio.Queue:
        subscription = self._subscriptions[subscription_id] = asyncio.Queue()
        return subscription

    def unsubscribe(self, subscription_id) -> asyncio.Queue | None:
        return self._subscriptions.pop(subscription_id, None)
