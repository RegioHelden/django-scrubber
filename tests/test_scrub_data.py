from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

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
