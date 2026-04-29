# Create your tests here.
# This is an economy system. Of course we cannot test an
# economy system, that would be considered smart.
#
# But we keep this file. It both looks good and makes things
# less complicated when we get serious.
#
# Better late than never

import factory
import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from factory.django import DjangoModelFactory
from rest_framework.test import APIClient

from cashflow.dauth import Permission
from expenses.models import Expense, ExpensePart, Profile, File


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = Profile
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)


class ExpenseFactory(DjangoModelFactory):
    class Meta:
        model = Expense

    owner = factory.SubFactory(ProfileFactory)
    description = factory.Faker("text")
    expense_date = factory.Faker("date")
    file = factory.RelatedFactory("expenses.tests.ExpenseFileFactory", factory_related_name="expense")


class ExpenseFileFactory(DjangoModelFactory):
    class Meta:
        model = File

    expense = factory.SubFactory(ExpenseFactory)
    invoice = None
    file = factory.django.FileField()


class ExpensePartFactory(DjangoModelFactory):
    class Meta:
        model = ExpensePart

    expense = factory.SubFactory(ExpenseFactory)
    cost_centre = factory.Faker("word")
    secondary_cost_centre = factory.Faker("word")
    budget_line = factory.Faker("word")
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def profile(user):
    return ProfileFactory(user=user)


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def expense(user):
    return ExpenseFactory(owner=user.profile)


# As of now, profiles should be automatically created using a signal
# when a user is created.
# This test might be useful if this changes
def test_profile_exists_after_new_user(db):
    user = UserFactory()
    assert Profile.objects.filter(user=user).exists()


def test_unauthenticated_get_returns_403():
    response = APIClient().get("/api/expenses/")
    assert response.status_code == 403


def test_normal_user_only_receives_own_expenses(user, client, mocker):
    mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
    ExpenseFactory.create_batch(20)
    ExpenseFactory.create_batch(5, owner=user.profile)
    response = client.get("/api/expenses/")
    assert response.status_code == 200
    assert len(response.data) == 5
    assert all([e["owner"] == user.profile.id for e in response.data])


def test_user_with_scope_receives_cc_expenses(user, client, mocker):
    permissions = {Permission.VIEW_EXPENSES: ["TestCostCenter"]}
    mocker.patch("cashflow.dauth.get_permissions", return_value=permissions, autospec=True)
    ExpenseFactory.create_batch(20)
    cc_expenses = ExpenseFactory.create_batch(2)
    ExpensePartFactory.create_batch(2, expense=cc_expenses[0], cost_centre="TestCostCenter")
    ExpensePartFactory.create_batch(2, expense=cc_expenses[1], cost_centre="TestCostCenter")

    response = client.get("/api/expenses/")
    assert response.status_code == 200
    assert len(response.data) == 2


def test_view_all_permission_returns_all_expenses(user, client, mocker):
    permissions = {Permission.VIEW_EXPENSES: "*"}
    mocker.patch("cashflow.dauth.get_permissions", return_value=permissions, autospec=True)

    ExpenseFactory.create_batch(20)
    response = client.get("/api/expenses/")
    assert response.status_code == 200
    assert len(response.data) == 20


def test_filter_by_username(user, client, mocker):
    permissions = {Permission.VIEW_EXPENSES: "*"}
    mocker.patch("cashflow.dauth.get_permissions", return_value=permissions, autospec=True)
    ExpenseFactory.create_batch(20)
    target_user = UserFactory()
    ExpenseFactory.create_batch(5, owner=target_user.profile)
    response = client.get("/api/expenses/", {"user": target_user.username})
    assert response.status_code == 200
    assert len(response.data) == 5
    assert all(e["owner"] == target_user.profile.id for e in response.data)


def test_filter_by_cost_center(user, client, mocker):
    permissions = {Permission.VIEW_EXPENSES: "*"}
    mocker.patch("cashflow.dauth.get_permissions", return_value=permissions, autospec=True)
    ExpenseFactory.create_batch(20)
    target_cc = "TestCostCenter"
    expenses = ExpenseFactory.create_batch(5)
    for expense in expenses:
        ExpensePartFactory.create_batch(2, expense=expense, cost_centre=target_cc)

    response = client.get("/api/expenses/", {"cost_center": target_cc})

    assert len(response.data) == 5


def test_expenses_create_accepts_files(user, client):
    file = SimpleUploadedFile("receipt.jpg", b"content", content_type="image/jpeg")
    file2 = SimpleUploadedFile("receipt2.jpg", b"content", content_type="image/jpeg")

    response = client.post("/api/expenses/",
                           {"description": "Test expense", "files": [file, file2], "expense_date": "2026-01-01"},
                           format="multipart")

    assert response.status_code == 201


def test_expenses_create_cant_set_other_owner(user, client):
    target_user = UserFactory()
    file = SimpleUploadedFile("receipt.jpg", b"content", content_type="image/jpeg")

    response = client.post("/api/expenses/", {"description": "Test expense", "expense_date": "2026-01-01",
                                              "owner": target_user.profile.id,  # not allowed
                                              "files": [file], }, format="multipart")

    assert response.data["owner"] == user.profile.id


def test_expenses_create_must_contain_file(user, client):
    response = client.post("/api/expenses/", {"description": "Test expense", "expense_date": "2026-01-01", })
    assert response.status_code == 400
