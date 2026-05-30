import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from expenses.models import Profile


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
