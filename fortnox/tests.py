import datetime
from unittest.mock import patch, MagicMock

import factory
import requests
from django.contrib.auth import get_user_model
from django.utils import timezone
from pytest import fixture, raises

from fortnox import FortnoxAPIClient, FortnoxNotFound
from fortnox.api_client.models import CostCenter
from fortnox.models import APIUser

UserModel = get_user_model()


class CostCenterFactory(factory.Factory):
    class Meta:
        model = CostCenter
        rename = {"url": "@url"}

    url = factory.Maybe(factory.Faker("boolean"), yes_declaration=factory.Faker("url"), no_declaration=None)
    Active = factory.Faker("boolean")
    Code = factory.Faker("pystr", min_chars=1, max_chars=6)
    Description = factory.Faker("pystr", min_chars=1)
    Note = factory.Faker("pystr")


@fixture
def user(db):
    return UserModel.objects.create_user(username='testuser')


@fixture
def fortnox_client():
    return FortnoxAPIClient(client_id='test', client_secret='test', scope=[], token_provider=lambda: "token")


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


def _cost_center_page_response(cost_centers, current_page, total_pages):
    """Build a fake requests.Response shaped like Fortnox's paginated list endpoint."""
    response = MagicMock(spec=requests.Response)
    response.status_code = 200
    response.json.return_value = {
        "MetaInformation": {"@TotalResources": total_pages * len(cost_centers), "@TotalPages": total_pages,
            "@CurrentPage": current_page, }, "CostCenters": [cc.model_dump(by_alias=True) for cc in cost_centers], }
    return response


def test_find_cost_center_walks_all_pages(fortnox_client):
    target = CostCenterFactory.create(Description="needle")
    page_1 = CostCenterFactory.create_batch(3)
    page_2 = CostCenterFactory.create_batch(3)
    page_3 = [*CostCenterFactory.create_batch(2), target]

    responses = [_cost_center_page_response(page_1, current_page=1, total_pages=3),
        _cost_center_page_response(page_2, current_page=2, total_pages=3),
        _cost_center_page_response(page_3, current_page=3, total_pages=3), ]

    with patch.object(fortnox_client, "_get", side_effect=responses) as mock_get:
        result = fortnox_client.find_cost_center(Description="needle")

    assert result.Description == "needle"
    assert mock_get.call_count == 3
    requested_pages = [call.kwargs["parameters"]["page"] for call in mock_get.call_args_list]
    assert requested_pages == [1, 2, 3]


def test_find_cost_center_stops_on_first_page_when_only_one_page(fortnox_client):
    target = CostCenterFactory.create(Description="needle")
    page = [*CostCenterFactory.create_batch(3), target]

    response = _cost_center_page_response(page, current_page=1, total_pages=1)

    with patch.object(fortnox_client, "_get", side_effect=[response]) as mock_get:
        result = fortnox_client.find_cost_center(Description="needle")

    assert result.Description == "needle"
    assert mock_get.call_count == 1


def test_find_cost_centers_handles_many_cost_centers(fortnox_client):
    cost_centers = CostCenterFactory.create_batch(2000)
    target = CostCenterFactory.create(Description="needle")
    cost_centers.insert(len(cost_centers) // 2, target)

    page_size = 50
    chunks = [cost_centers[i:i + page_size] for i in range(0, len(cost_centers), page_size)]
    total_pages = len(chunks)
    target_page = next(i for i, chunk in enumerate(chunks, start=1) if target in chunk)

    responses = [_cost_center_page_response(chunk, current_page=i + 1, total_pages=total_pages) for i, chunk in
        enumerate(chunks)]

    with patch.object(fortnox_client, "_get", side_effect=responses) as mock_get:
        result = fortnox_client.find_cost_center(Description="needle")

    assert result.Description == "needle"
    assert mock_get.call_count == target_page


def test_find_nonexisting_cost_center_raises_exception(fortnox_client):
    page_1 = _cost_center_page_response(CostCenterFactory.create_batch(3), current_page=1, total_pages=2)
    page_2 = _cost_center_page_response(CostCenterFactory.create_batch(3), current_page=2, total_pages=2)

    with patch.object(fortnox_client, "_get", side_effect=[page_1, page_2]):
        with raises(FortnoxNotFound):
            fortnox_client.find_cost_center(Description="I don't exist")
