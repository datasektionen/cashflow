from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from pytest import fixture

from cashflow.utils import may_authenticate_fortnox

UserModel = get_user_model()


@fixture
def user(db):
    return UserModel.objects.create_user(username='testuser')


def test_normal_user_cant_authenticate_fortnox(user):
    with patch('cashflow.dauth.get_permissions', return_value={}):
        assert not may_authenticate_fortnox(user)


def test_permitted_user_may_authenticate_fortnox(user):
    with patch('cashflow.dauth.get_permissions', return_value={'manage-fortnox': True}):
        assert may_authenticate_fortnox(user)


def test_auth_endpoint_forbidden_without_permission(db, user):
    client = Client()
    client.force_login(user)
    with patch('cashflow.utils.has_accounting_permissions', return_value=False), \
         patch('cashflow.utils.may_authenticate_fortnox', return_value=False):
        response = client.get(reverse('fortnox-auth-get'))
    assert response.status_code == 403


def test_auth_endpoint_accessible_with_permission(db, user):
    client = Client()
    client.force_login(user)
    with patch('cashflow.utils.has_accounting_permissions', return_value=False), \
         patch('cashflow.utils.may_authenticate_fortnox', return_value=True):
        response = client.get(reverse('fortnox-auth-get'))
    assert response.status_code != 403
