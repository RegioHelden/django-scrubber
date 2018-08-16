from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from django_scrubber import scrubbers
from .factories import UserFactory


class TestScrubData(TestCase):
    def setUp(self):
        self.user_1 = UserFactory.create(first_name='test_first_name')

    def test_scrub_data(self):
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={'first_name': scrubbers.Faker('first_name')}):
            call_command('scrub_data', verbosity=3)
        self.user_1.refresh_from_db()

        self.assertNotEqual(self.user_1.first_name, 'test_first_name')

    def test_scrub_data_debug_is_false(self):
        err = StringIO()

        with self.settings(DEBUG=False):
            call_command('scrub_data',  stderr=err)
        output = err.getvalue()
        self.user_1.refresh_from_db()

        self.assertIn("this command should only be run with DEBUG=True, to avoid running on live systems", output)
        self.assertEqual(self.user_1.first_name, 'test_first_name')
