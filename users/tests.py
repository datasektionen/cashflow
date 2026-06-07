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
