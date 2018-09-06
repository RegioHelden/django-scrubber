from __future__ import absolute_import

from django.test import TestCase
from django.core.management import call_command

from django_scrubber import scrubbers

from .models import DataFactory, DataToBeScrubbed


class TestScrubbers(TestCase):
    def test_hash_scrubber_max_length(self):
        data = DataFactory.create(first_name='Foo')
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'first_name': scrubbers.Hash}):
            call_command('scrub_data')
        data.refresh_from_db()

        self.assertNotEqual(data.first_name, 'Foo')
        self.assertEqual(
            len(data.first_name),
            DataToBeScrubbed._meta.get_field('first_name').max_length,
            'len(%s) != %d' % (data.first_name, DataToBeScrubbed._meta.get_field('first_name').max_length)
        )
