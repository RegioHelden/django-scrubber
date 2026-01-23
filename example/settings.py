import os

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "uzbLoOIYlJnzGDYlUfynNyocjZH9NLSc3AAREwLDaugQkCzsQn"  # noqa: S105

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {},
    },
    # replace default entry to use mysql for testing
    "mysql": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "app",
        "USER": "app",
        "PASSWORD": "app",
        "HOST": "mysql",
        "PORT": "3306",
        "TEST": {
            "NAME": "app",
        },
    },
    # replace default entry to use postgresql for testing
    "postgres": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "app",
        "USER": "app",
        "PASSWORD": "app",
        "HOST": "postgres",
        "PORT": "5432",
        "TEST": {
            "NAME": "app",
        },
    },
}

if os.environ.get("GITHUB_WORKFLOW", None):
    DATABASE_ENGINE = os.environ.get("DATABASE_ENGINE", "sqlite")
    if "mysql" in DATABASE_ENGINE:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": "test",
                "USER": "root",
                "PASSWORD": "",
                "HOST": "127.0.0.1",
                "PORT": "3306",
            },
        }
    elif "postgres" in DATABASE_ENGINE:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "postgres",
                "USER": "postgres",
                "PASSWORD": "postgres",
                "HOST": "127.0.0.1",
                "PORT": "5432",
            },
        }

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django_scrubber.apps.DjangoScrubberConfig",
    "example.apps.ExampleConfig",
]

SITE_ID = 1

MIDDLEWARE = ()

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
