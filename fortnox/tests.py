import datetime
from unittest.mock import patch, MagicMock

import factory
import requests
from django.contrib.auth import get_user_model
from django.utils import timezone
from pytest import fixture, raises

from admin.views.fortnox import account_expense, account_invoice
from expenses.models import Expense, Profile
from fortnox import FortnoxAPIClient, FortnoxNotFound
from fortnox.api_client.models import CostCenter, Voucher
from fortnox.models import APIUser
from invoices.models import Invoice

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


class VoucherFactory(factory.Factory):
    class Meta:
        model = Voucher
        rename = {"url": "@url"}

    url = factory.Maybe(factory.Faker("boolean"), yes_declaration=factory.Faker("url"), no_declaration=None)
    Description = factory.Faker("pystr", min_chars=1, max_chars=200)
    TransactionDate = "2025-01-01"
    VoucherNumber = factory.Sequence(lambda n: n + 1)
    VoucherSeries = factory.Faker("pystr", min_chars=1, max_chars=10)
    Year = 2025


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


@fixture
def profile(db, user):
    # Profile is auto-created via a post_save signal on User
    return user.profile


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


def _voucher_page_response(vouchers, current_page, total_pages):
    """Build a fake requests.Response shaped like Fortnox's paginated voucher list endpoint."""
    response = MagicMock(spec=requests.Response)
    response.status_code = 200
    response.json.return_value = {
        "MetaInformation": {"@TotalResources": total_pages * len(vouchers), "@TotalPages": total_pages,
            "@CurrentPage": current_page, }, "Vouchers": [v.model_dump(by_alias=True) for v in vouchers], }
    return response


def test_find_voucher_walks_all_pages(fortnox_client):
    target = VoucherFactory.create(Description="needle")
    page_1 = VoucherFactory.create_batch(3)
    page_2 = VoucherFactory.create_batch(3)
    page_3 = [*VoucherFactory.create_batch(2), target]

    responses = [_voucher_page_response(page_1, current_page=1, total_pages=3),
        _voucher_page_response(page_2, current_page=2, total_pages=3),
        _voucher_page_response(page_3, current_page=3, total_pages=3), ]

    with patch.object(fortnox_client, "_get", side_effect=responses) as mock_get:
        result = fortnox_client.find_voucher(Description="needle")

    assert result.Description == "needle"
    assert mock_get.call_count == 3
    requested_pages = [call.kwargs["parameters"]["page"] for call in mock_get.call_args_list]
    assert requested_pages == [1, 2, 3]


def test_find_voucher_stops_on_first_page_when_only_one_page(fortnox_client):
    target = VoucherFactory.create(Description="needle")
    page = [*VoucherFactory.create_batch(3), target]

    response = _voucher_page_response(page, current_page=1, total_pages=1)

    with patch.object(fortnox_client, "_get", side_effect=[response]) as mock_get:
        result = fortnox_client.find_voucher(Description="needle")

    assert result.Description == "needle"
    assert mock_get.call_count == 1


def test_find_vouchers_handles_many_vouchers(fortnox_client):
    vouchers = VoucherFactory.create_batch(2000)
    target = VoucherFactory.create(Description="needle")
    vouchers.insert(len(vouchers) // 2, target)

    page_size = 50
    chunks = [vouchers[i:i + page_size] for i in range(0, len(vouchers), page_size)]
    total_pages = len(chunks)
    target_page = next(i for i, chunk in enumerate(chunks, start=1) if target in chunk)

    responses = [_voucher_page_response(chunk, current_page=i + 1, total_pages=total_pages) for i, chunk in
        enumerate(chunks)]

    with patch.object(fortnox_client, "_get", side_effect=responses) as mock_get:
        result = fortnox_client.find_voucher(Description="needle")

    assert result.Description == "needle"
    assert mock_get.call_count == target_page


def test_find_nonexisting_voucher_raises_exception(fortnox_client):
    page_1 = _voucher_page_response(VoucherFactory.create_batch(3), current_page=1, total_pages=2)
    page_2 = _voucher_page_response(VoucherFactory.create_batch(3), current_page=2, total_pages=2)

    with patch.object(fortnox_client, "_get", side_effect=[page_1, page_2]):
        with raises(FortnoxNotFound):
            fortnox_client.find_voucher(Description="I don't exist")


def test_account_expense_returns_409_when_already_accounted(db, user, profile):
    expense = Expense.objects.create(expense_date=datetime.date(2025, 1, 1), owner=profile, description="lunch")

    fortnox_service = MagicMock()
    fortnox_service.find_voucher.return_value = VoucherFactory.build()

    request = RequestFactory().post(f'/admin/fortnox/expenses/account/{expense.id}/')
    request.user = user
    request.fortnox_service = fortnox_service

    response = account_expense(request, id=str(expense.id))

    assert response.status_code == 409
    fortnox_service.create_voucher.assert_not_called()
    expense.refresh_from_db()
    assert expense.verification == ""


def test_account_invoice_returns_409_when_already_accounted(db, user, profile):
    invoice = Invoice.objects.create(invoice_date=datetime.date(2025, 1, 1), owner=profile, description="server",
                                     file_is_original=True)

    fortnox_service = MagicMock()
    fortnox_service.find_voucher.return_value = VoucherFactory.build()

    request = RequestFactory().post(f'/admin/fortnox/invoices/account/{invoice.id}/')
    request.user = user
    request.fortnox_service = fortnox_service

    response = account_invoice(request, id=str(invoice.id))

    assert response.status_code == 409
    fortnox_service.create_voucher.assert_not_called()
    invoice.refresh_from_db()
    assert invoice.verification == ""
