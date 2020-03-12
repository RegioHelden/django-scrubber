try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
from StringIO import StringIO

from django.core.management import call_command
from django.test import TestCase

from django_scrubber import scrubbers
from django.contrib.auth import get_user_model
User = get_user_model()


class TestScrubData(TestCase):
    def setUp(self):
        self.user = User.objects.create(first_name='test_first_name')

    def test_scrub_data(self):
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'first_name': scrubbers.Faker('first_name')}):
            call_command('scrub_data', verbosity=3)
        self.user.refresh_from_db()

        self.assertNotEqual(self.user.first_name, 'test_first_name')

    def test_scrub_data_debug_is_false(self):
        err = StringIO()

        with self.settings(DEBUG=False):
            call_command('scrub_data',  stderr=err)
        output = err.getvalue()
        self.user.refresh_from_db()

        self.assertIn("this command should only be run with DEBUG=True, to avoid running on live systems", output)
        self.assertEqual(self.user.first_name, 'test_first_name')

    def test_hash_simple_global_scrubber(self):
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'first_name': scrubbers.Hash}):
            call_command('scrub_data')
        self.user.refresh_from_db()

        self.assertNotEqual(self.user.first_name, 'test_first_name')

    def test_hash_simple_class_scrubber(self):
        class Scrubbers:
            first_name = scrubbers.Hash

        with self.settings(DEBUG=True), patch.object(User, 'Scrubbers', Scrubbers, create=True):
            call_command('scrub_data')
        self.user.refresh_from_db()

        self.assertNotEqual(self.user.first_name, 'test_first_name')
