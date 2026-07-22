from core.factories import UserFactory
from expenses.models import Profile


class TestProfileSignal:
    # As of now, profiles should be automatically created using a signal
    # when a user is created.
    # This test might be useful if this changes
    def test_profile_exists_after_new_user(self, db):
        user = UserFactory()
        assert Profile.objects.filter(user=user).exists()
