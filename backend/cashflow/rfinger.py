"""rfinger is our service for profile pictures."""

import json

import requests
from django.conf import settings
from django.contrib.auth.models import User
from drf_problems.utils import register_exception
from pydantic import RootModel, HttpUrl, TypeAdapter
from rest_framework.exceptions import APIException
from structlog import get_logger

from core.exceptions import ErrorToDictMixin
from users.pictures import ProfilePictureProvider, ProfilePicture

logger = get_logger(__name__)


class _RFingerResponse(RootModel):
    root: dict[str, HttpUrl]


URL_ADAPTER = TypeAdapter(HttpUrl)


class RFingerRequestFailed(APIException, ErrorToDictMixin):
    status_code = 500
    default_code = "rfinger_request_failed"
    title = "rfinger request Failed"
    default_detail = (
        "An error occurred while trying to fetch profile pictures from rfinger."
    )


register_exception(RFingerRequestFailed)


class RFingerClient:
    """An API client for retrieving profile pictures from rfinger."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    def _request(self, method: str, path: str, body: object | None = None) -> str:
        """Call rfinger and return the response body. Logs and raises on non-200."""
        headers = {"Authorization": "Bearer " + self.api_key}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body)
        response = requests.request(
            method, self.base_url + path, data=data, headers=headers
        )
        if response.status_code != 200:
            logger.error(
                "rfinger request failed",
                method=method,
                status_code=response.status_code,
                response_body=response.text[:500],
                path=path,
            )
            raise RFingerRequestFailed()
        return response.text

    def get(self, user: User | str) -> ProfilePicture:
        """Takes a Django user or username and returns their profile picture."""
        username = user if isinstance(user, str) else user.username
        text = self._request("GET", f"/api/{username}")
        url = URL_ADAPTER.validate_python(text)
        return ProfilePicture(username=username, url=url)

    def batch(self, users: list[User | str]) -> dict[str, ProfilePicture]:
        """Takes a list of Django users or usernames and returns their profile pictures."""
        usernames = [user if isinstance(user, str) else user.username for user in users]
        text = self._request("POST", "/api/batch", usernames)
        data = _RFingerResponse.model_validate_json(text)
        return {
            username: ProfilePicture(username=username, url=url)
            for username, url in data.root.items()
        }


rfinger_client = RFingerClient(settings.RFINGER_API_KEY, settings.RFINGER_API_URL)
"""Singleton instance of the rfinger client class"""


class RFinger(ProfilePictureProvider):
    """rfinger-backed implementation of ProfilePictureProvider."""

    def __init__(self, client: RFingerClient = rfinger_client):
        self.client = client

    def get_many(self, usernames: list[str]) -> dict[str, ProfilePicture | None]:
        found = self.client.batch(list(usernames))
        return {username: found.get(username) for username in usernames}
