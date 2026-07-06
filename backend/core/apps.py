from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Contains functionality that is shared between other apps and is not specific to any one app or tailored towards
    the Computer Science Chapter's system.
    """

    name = "core"
