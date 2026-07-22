"""General-purpose Django middleware.

Contains middleware that is not specific to any certain app.
"""

import random
import re
import string
import time

from django.http import HttpResponse, HttpRequest
from structlog.contextvars import clear_contextvars, bind_contextvars
from structlog import get_logger

logger = get_logger(__name__)


class StructlogContextMiddleware:
    """Clears structlog contextvars between requests and binds per-request identifiers.

    Clearing prevents contextvars from one request leaking into log lines emitted by the next request handled by the
    same worker. On every request the following keys are bound for the duration of the request:

    - ``request_id``: an 8-character ID echoed back as ``X-Request-ID``. If the client supplies a well-formed
      ``X-Request-ID`` header, that value is used; otherwise a fresh one is generated.
    - ``user_id`` and ``username``: the authenticated Django user, or ``None`` for anonymous requests.
    """

    _ID_ALPHABET = string.ascii_lowercase + string.digits
    _ID_PATTERN = re.compile(r"[a-z0-9]{8}")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        clear_contextvars()
        incoming = request.headers.get("X-Request-ID")

        # Check that the incoming header matches the expected format
        if incoming:
            if not re.fullmatch(self._ID_PATTERN, incoming):
                request_id = self.generate_id()
                logger.warning(
                    "invalid request id provided by client",
                    peer=request.META["REMOTE_ADDR"],
                    forwarded_for=request.get_host(),
                    header_length=len(incoming),
                    new_request_id=request_id,
                )
            else:
                request_id = incoming
        else:
            request_id = self.generate_id()

        bind_contextvars(request_id=request_id)
        if getattr(request, "user", None) and request.user.is_authenticated:
            bind_contextvars(user_id=request.user.id, username=request.user.username)
        else:
            bind_contextvars(user_id=None, username=None)

        start = time.perf_counter()
        response: HttpResponse = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request completed",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response

    def generate_id(self):

        return "".join(random.choices(self._ID_ALPHABET, k=8))
