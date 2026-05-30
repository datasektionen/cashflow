from django.contrib.auth.models import User
from rest_framework.request import Request


def authenticated_user(request: Request) -> User:
    """Enforces an authenticated user and narrows the type.

    Django requests use AbstractBaseUser as the user class, which can be both User (authenticated) or AnonymousUser (not authenticated).
    This can cause issues with typing, e.g. when trying to access the Profile field. When you are expecting only authenticated users, this function
    can be used to ensure the correct type and avoid type warnings.
    """
    user = request.user
    assert isinstance(user, User)
    return user


class AuthenticatedUserMixin:
    """Uses the authenticated_user function to provide a current_user property with the correct type."""

    request: Request

    @property
    def current_user(self) -> User:
        return authenticated_user(self.request)
