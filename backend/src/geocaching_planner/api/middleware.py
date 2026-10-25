from uuid import uuid4

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestIdMiddleware:
    """Assigns each HTTP request an ID stored in the shared ASGI scope.

    The scope dict is used (rather than contextvars) because the catch-all
    exception handler runs outside user middleware, after contextvars are reset.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            scope.setdefault("state", {})["request_id"] = uuid4().hex
        await self.app(scope, receive, send)


def get_request_id(request: Request) -> str:
    state = request.scope.get("state", {})
    request_id = state.get("request_id") if isinstance(state, dict) else None
    return str(request_id) if request_id else uuid4().hex
