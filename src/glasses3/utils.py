from __future__ import annotations

import asyncio
from asyncio import Future, Task
from enum import Enum, auto
from typing import Any, Coroutine, Union

from glasses3.g3typing import URI


class APIComponent:
    def __init__(self, api_uri: URI):
        self._api_uri = api_uri

    def generate_endpoint_uri(
        self, endpoint_kind: EndpointKind, endpoint_name: str
    ) -> URI:
        return URI(f"{self._api_uri}{endpoint_kind.uri_delimiter}{endpoint_name}")


class EndpointKind(Enum):
    PROPERTY = auto()
    ACTION = auto()
    SIGNAL = auto()

    @property
    def uri_delimiter(self):
        match self:
            case EndpointKind.PROPERTY:
                return "."
            case EndpointKind.ACTION:
                return "!"
            case EndpointKind.SIGNAL:
                return ":"


def create_task(coro: Coroutine[Any, Any, Any], *, name: Any = None) -> Task[Any]:
    task = asyncio.create_task(coro, name=name)
    task.add_done_callback(raise_error)
    return task


def raise_error(fut: Union[Task[Any], Future[Any]]):
    try:
        exception = fut.exception()
        if exception is not None:
            raise exception
    except asyncio.CancelledError:
        pass
