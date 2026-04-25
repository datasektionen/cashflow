import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from pytest import fixture, raises

from fortnox.models import APIUser

UserModel = get_user_model()


@fixture
def user(db):
    return UserModel.objects.create_user(username='testuser')


@fixture
def api_user(db, user):
    return APIUser.objects.create(authenticated_by=user, access_token='', refresh_token='',
                                  expires_at=timezone.now() + datetime.timedelta(days=1))


def test_only_one_api_client_allowed(db, user):
    APIUser.objects.create(authenticated_by=user, access_token='', refresh_token='',
        expires_at=timezone.now() + datetime.timedelta(days=1), )

    with raises(ValueError):
        APIUser.objects.create(authenticated_by=user, access_token='', refresh_token='',
            expires_at=timezone.now() + datetime.timedelta(days=1), )


def test_api_user_can_be_updated(db, api_user):
    new_user = UserModel.objects.create(is_staff=True, is_superuser=True)
    APIUser.objects.update(authenticated_by=new_user, access_token='', refresh_token='',
        expires_at=timezone.now() + datetime.timedelta(days=1), )