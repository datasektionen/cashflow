import pytest
from rest_framework.test import APIClient

from expenses.factories import ExpenseFactory


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def expense(user):
    return ExpenseFactory(owner=user.profile)
