import pytest
from datetime import date, timedelta

from freezegun import freeze_time

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


@pytest.fixture
def today():
    d = date.today()
    with freeze_time(d):
        yield d


@pytest.fixture
def yesterday():
    d = date.today() - timedelta(days=1)
    with freeze_time(date.today()):
        yield d


@pytest.fixture
def tomorrow():
    d = date.today() + timedelta(days=1)
    with freeze_time(date.today()):
        yield d
