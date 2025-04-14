from django.conf import settings
from django.db import models

defaults = {
    "SCRUBBER_RANDOM_SEED": 42,  # we prefer idempotent scrubbing
    "SCRUBBER_ENTRIES_PER_PROVIDER": 1000,
    "SCRUBBER_GLOBAL_SCRUBBERS": {},
    "SCRUBBER_SKIP_UNMANAGED": True,
    "SCRUBBER_APPS_LIST": None,
    "SCRUBBER_ADDITIONAL_FAKER_PROVIDERS": {*()},
    "SCRUBBER_FAKER_LOCALE": None,
    "SCRUBBER_MAPPING": {},
    "SCRUBBER_STRICT_MODE": False,
    "SCRUBBER_REQUIRED_FIELD_TYPES": (
        models.CharField,
        models.TextField,
        models.URLField,
        models.JSONField,
        models.GenericIPAddressField,
        models.EmailField,
    ),
    "SCRUBBER_REQUIRED_FIELD_MODEL_WHITELIST": (
        "auth.Group",
        "auth.Permission",
        "contenttypes.ContentType",
        "db.TestModel",
        "sessions.Session",
        "sites.Site",
        "django_scrubber.FakeData",
    ),
}


def settings_with_fallback(key):
    return getattr(settings, key, defaults[key])


class ScrubberInitError(Exception):
    pass
