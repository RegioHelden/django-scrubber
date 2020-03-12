from datetime import date, timedelta

import django
from django.core.management import call_command
from django.db import connection
from django.test import TestCase

from django_scrubber import scrubbers
from .models import DataFactory, DataToBeScrubbed


class TestScrubbers(TestCase):
    def test_empty_scrubber(self):
        data = DataFactory.create(first_name='Foo')
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'first_name': scrubbers.Empty}):
            call_command('scrub_data')
        data.refresh_from_db()

        self.assertEqual(data.first_name, '')

    def test_null_scrubber(self):
        data = DataFactory.create(last_name='Foo')
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'last_name': scrubbers.Null}):
            call_command('scrub_data')
        data.refresh_from_db()

        self.assertEqual(data.last_name, None)

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

    def test_lorem_scrubber(self):
        data = DataFactory.create(description='Foo')
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'description': scrubbers.Lorem}):
            call_command('scrub_data')
        data.refresh_from_db()

        self.assertNotEqual(data.description, 'Foo')
        self.assertEqual(data.description[:11], 'Lorem ipsum')

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

        # The EAN Faker will by default emit ean13, so this would fail if the parameter was ignored
        self.assertEquals(8, len(data.ean8))

        # Add a new scrubber for ean13
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'ean8': scrubbers.Faker('ean', length=13)}):
            call_command('scrub_data')
        data.refresh_from_db()

        # make sure it doesn't reuse the ean with length=8 scrubber
        self.assertEquals(13, len(data.ean8))

    def test_faker_scrubber_datefield(self):
        """
        Use this as an example for Scrubber's capability of optimistically Casting to the current field's type
        There is a bug with django < 2.1 and sqlite, that's why we don't run the test there.
        """
        if django.VERSION >= (2, 1) or connection.vendor != "sqlite":
            data = DataFactory.create(date_past=date.today())
            with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={
                    'date_past': scrubbers.Faker('past_date', start_date="-30d", tzinfo=None)}):
                call_command('scrub_data')
            data.refresh_from_db()

            self.assertGreater(date.today(), data.date_past)
            self.assertLess(date.today() - timedelta(days=31), data.date_past)

    def test_faker_scrubber_run_twice(self):
        """
        Use this as an example of what happens when you want to run the same Faker scrubbers twice
        """
        data = DataFactory.create(company='Foo')
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={
                'company': scrubbers.Faker('company')}):
            call_command('scrub_data')
            call_command('scrub_data')
        data.refresh_from_db()

        self.assertNotEqual(data.company, 'Foo')
        self.assertNotEqual(data.company, '')
