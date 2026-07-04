import pytest
from hypothesis import given, strategies as st
from rest_framework.test import APIClient

from pydantic import HttpUrl

from users.pictures import ProfilePictureProvider, ProfilePicture


class FakeProfilePictureProvider(ProfilePictureProvider):

    def get_many(self, usernames: list[str]) -> dict[str, ProfilePicture | None]:
        return {
            username: ProfilePicture(
                username=username,
                url=HttpUrl(f"https://pictures.example.com/{username}.jpg"),
            )
            for username in usernames
        }


class TestGetProfilePictures:

    @pytest.mark.django_db
    @given(
        usernames=st.from_regex(r"\s*[\w.@+-]+(\s*,\s*[\w.@+-]+)*\s*", fullmatch=True)
    )
    def test_correct_request(self, usernames):
        client = APIClient()
        client.force_authenticate()
        response = client.get(f"/api/users/profile-pictures/", {"usernames": usernames})
        assert response.status_code == 200
        names = {name.strip() for name in usernames.split(",")}
        expected = {
            name: str(HttpUrl(f"https://pictures.example.com/{name}.jpg"))
            for name in names
        }
        assert response.json() == expected


class TestCurrentUserBankInfo:
    def test_bank_info_included(self, user, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        user.profile.bank_account = "1234567"
        user.profile.sorting_number = "8327"
        user.profile.bank_name = "Swedbank"
        user.profile.save()

        response = api_client.get("/api/users/me/")
        assert response.status_code == 200
        assert response.data["bank_info"] == {
            "bank_account": "1234567",
            "sorting_number": "8327",
            "bank_name": "Swedbank",
        }

    def test_patch_updates_bank_info(self, user, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)

        response = api_client.patch(
            "/api/users/me/",
            {
                "bank_info": {
                    "bank_account": "7654321",
                    "sorting_number": "8123",
                    "bank_name": "Nordea",
                }
            },
            format="json",
        )
        assert response.status_code == 200, response.json()
        user.profile.refresh_from_db()
        assert user.profile.bank_account == "7654321"
        assert user.profile.sorting_number == "8123"
        assert user.profile.bank_name == "Nordea"

    def test_patch_cannot_change_identity_fields(self, user, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        original_username = user.username

        response = api_client.patch(
            "/api/users/me/",
            {"username": "hacker", "email": "hacker@example.com"},
            format="json",
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.username == original_username
        assert user.email != "hacker@example.com"

    def test_patch_rejects_too_long_bank_account(self, user, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)

        response = api_client.patch(
            "/api/users/me/",
            {"bank_info": {"bank_account": "1" * 14}},
            format="json",
        )
        assert response.status_code == 400

    def test_unauthenticated_cannot_patch(self, db):
        response = APIClient().patch(
            "/api/users/me/", {"bank_info": {"bank_name": "X"}}, format="json"
        )
        assert response.status_code == 403


class TestHasBankInfo:
    def test_flag_reflects_account_and_clearing(self, user, api_client, mocker):
        mocker.patch("cashflow.dauth.get_permissions", return_value={}, autospec=True)
        from expenses.factories import ExpenseFactory

        ExpenseFactory(owner=user.profile)
        response = api_client.get("/api/expenses/")
        assert response.status_code == 200
        assert response.data["data"][0]["owner"]["has_bank_info"] is False

        user.profile.bank_account = "1234567"
        user.profile.sorting_number = "8327"
        user.profile.save()
        response = api_client.get("/api/expenses/")
        assert response.data["data"][0]["owner"]["has_bank_info"] is True

    def test_bank_name_alone_is_not_enough(self, profile):
        profile.bank_name = "Swedbank"
        assert profile.has_bank_info is False
