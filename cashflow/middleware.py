"""General-purpose Django middleware.

Contains middleware that is not specific to any certain app.
"""
import random
import re
import string

from django.http import HttpResponse, HttpRequest
from structlog.contextvars import clear_contextvars, bind_contextvars
from structlog import get_logger

logger = get_logger(__name__)


class StructlogContextMiddleware:
    """Clears structlog contextvars between requests and attaches a unique ID to every request.

    This prevents old contextvars being placed in logs from newer requests if they have not been overwritten. The
    request ID makes it easier to trace issues in error logs.
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

        bind_contextvars(request_id=request.headers.get("X-Request-ID"))
        response: HttpResponse = self.get_response(request)
        response.headers["X-Request-ID"] = request_id
        return response

    def generate_id(self):

        return ''.join(random.choices(self._ID_ALPHABET, k=8))
