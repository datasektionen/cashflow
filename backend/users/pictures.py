from abc import ABC, abstractmethod

from pydantic import BaseModel, HttpUrl


class ProfilePicture(BaseModel):
    username: str
    url: HttpUrl


class ProfilePictureProvider(ABC):
    """Abstract base class for providing profile pictures.

    Enables dependency injection through subclassing.
    """

    @abstractmethod
    def get_many(self, usernames: list[str]) -> dict[str, ProfilePicture | None]:
        """Accepts a list of usernames and returns a dict mapping each username to its
        ProfilePicture, or None if no picture is available for that user."""
        pass
