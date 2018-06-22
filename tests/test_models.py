#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django_scrubber
------------

Tests for `django_scrubber` models module.
"""

from django.test import TestCase
from django.db.utils import IntegrityError

from django_scrubber import models


class TestDjango_scrubber(TestCase):

    def test_uniqueness(self):
        models.FakeData.objects.create(provider='foo', provider_offset=0, content='bar')
        with self.assertRaises(IntegrityError):
            models.FakeData.objects.create(provider='foo', provider_offset=0, content='baz')
