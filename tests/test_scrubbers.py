from __future__ import absolute_import

from django.core.management import call_command
from django.test import TestCase

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

    def test_hash_scrubber_textfield(self):
        data = DataFactory.create(description='Foo')
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'description': scrubbers.Hash}):
            call_command('scrub_data')
        data.refresh_from_db()

        self.assertNotEqual(data.description, 'Foo')

    def test_faker_scrubber_charfield(self):
        data = DataFactory.create(last_name='Foo')
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'last_name': scrubbers.Faker('last_name')}):
            call_command('scrub_data')
        data.refresh_from_db()

        self.assertNotEqual(data.last_name, 'Foo')
        self.assertNotEqual(data.last_name, '')

    def test_faker_scrubber_with_provider_arguments(self):
        """
        Use this as an example for Faker scrubbers with parameters passed along
        """
        data = DataFactory.create(ean8='8')
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'ean8': scrubbers.Faker('ean', length=8)}):
            call_command('scrub_data')
        data.refresh_from_db()

        # The EAN Faker will by default emit ean13, so this should fail
        self.assertEquals(8, len(data.ean8))
