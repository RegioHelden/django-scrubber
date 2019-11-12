# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

import django
import dj_database_url

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "uzbLoOIYlJnzGDYlUfynNyocjZH9NLSc3AAREwLDaugQkCzsQn"

DATABASES = {
    "default": dj_database_url.config(default='sqlite://:memory:')
}

ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django_scrubber",
]

SITE_ID = 1

if django.VERSION >= (1, 10):
    MIDDLEWARE = ()
else:
    MIDDLEWARE_CLASSES = ()
