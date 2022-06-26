import os

import django

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "uzbLoOIYlJnzGDYlUfynNyocjZH9NLSc3AAREwLDaugQkCzsQn"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
        }
    }
}

if os.environ.get('GITHUB_WORKFLOW', False):
    DATABASE_ENGINE = os.environ.get('DATABASE_ENGINE', 'sqlite')
    if 'mysql' in DATABASE_ENGINE:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'test',
                'USER': 'root',
                'PASSWORD': '',
                'HOST': '127.0.0.1',
                'PORT': '3306',
            },
        }
    elif 'postgres' in DATABASE_ENGINE:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'postgres',
                'USER': 'postgres',
                'PASSWORD': 'postgres',
                'HOST': '127.0.0.1',
                'PORT': '5432',
            },
        }

ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django_scrubber",
]

SITE_ID = 1

if django.VERSION >= (1, 10):
    MIDDLEWARE = ()
else:
    MIDDLEWARE_CLASSES = ()

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
