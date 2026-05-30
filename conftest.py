import pytest

from core.factories import ProfileFactory, UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def profile(user):
    return ProfileFactory(user=user)
