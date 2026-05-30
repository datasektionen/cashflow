import pytest
from rest_framework.test import APIClient

from core.factories import ProfileFactory, UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def profile(user):
    return ProfileFactory(user=user)


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client
