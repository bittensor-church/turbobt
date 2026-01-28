import asyncio
import collections

import turbobt.substrate.transports.base
from turbobt.substrate._models import Request, Response


class MockedTransport(turbobt.substrate.transports.base.BaseTransport):
    def __init__(self):
        self.responses = {}
        self.subscriptions = collections.defaultdict(
            asyncio.Queue,
        )

    async def send(self, request: Request) -> Response:
        if request.method in self.responses:
            response = self.responses[request.method]

            if request.method == "state_call":
                try:
                    response = response[request.params[0]]
                except (KeyError, IndexError):
                    response = {}

            return Response(
                request=request,
                result=response.get("result"),
                error=response.get("error"),
            )

        return Response(
            request=request,
            result=None,
            error=None,  # TODO?
        )

    def subscribe(self, subscription_id) -> asyncio.Queue:
        return self.subscriptions[subscription_id]

    def unsubscribe(self, subscription_id) -> asyncio.Queue | None:
        return self.subscriptions.pop(subscription_id, None)
