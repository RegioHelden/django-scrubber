from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from django_scrubber import scrubbers
from django_scrubber.management.commands.scrub_data import _get_model_scrubbers, _parse_scrubber_class_from_string

User = get_user_model()


class TestScrubData(TestCase):
    def setUp(self):
        self.user = User.objects.create(first_name="test_first_name")

    def test_scrub_data(self):
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"first_name": scrubbers.Faker("first_name")}):
            call_command("scrub_data", verbosity=3)
        self.user.refresh_from_db()

        self.assertNotEqual(self.user.first_name, "test_first_name")

    def test_scrub_data_debug_is_false(self):
        err = StringIO()

        with self.settings(DEBUG=False):
            call_command("scrub_data", stderr=err)
        output = err.getvalue()
        self.user.refresh_from_db()

        self.assertIn("This command should only be run with DEBUG=True, to avoid running on live systems", output)
        self.assertEqual(self.user.first_name, "test_first_name")

    @override_settings(SCRUBBERS_STRICT_MODE=True)
    def test_scrub_data_strict_mode_enabled_scrubbing_blocked(self):
        err = StringIO()

        with self.settings(DEBUG=False):
            call_command("scrub_data", stderr=err)
        output = err.getvalue()
        self.user.refresh_from_db()

        self.assertIn("This command should only be run with DEBUG=True, to avoid running on live systems", output)
        self.assertEqual(self.user.first_name, "test_first_name")

    def test_hash_simple_global_scrubber(self):
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"first_name": scrubbers.Hash}):
            call_command("scrub_data")
        self.user.refresh_from_db()

        self.assertNotEqual(self.user.first_name, "test_first_name")

    def test_hash_simple_class_scrubber(self):
        class Scrubbers:
            first_name = scrubbers.Hash

        with self.settings(DEBUG=True), patch.object(User, "Scrubbers", Scrubbers, create=True):
            call_command("scrub_data")
        self.user.refresh_from_db()

        self.assertNotEqual(self.user.first_name, "test_first_name")

    def test_scrub_invalid_field(self):
        class Scrubbers:
            this_does_not_exist_382784 = scrubbers.Null

        with (
            self.settings(DEBUG=True),
            patch.object(User, "Scrubbers", Scrubbers, create=True),
            self.assertWarnsRegex(
                Warning,
                "Scrubber defined for User.this_does_not_exist_382784 but field does not exist",
            ),
        ):
            call_command("scrub_data")

    @override_settings(SCRUBBER_MAPPING={"auth.User": "tests.scrubbers.UserScrubbers"})
    def test_get_model_scrubbers_mapper_from_settings_used(self):
        with (
            patch(
                "django_scrubber.management.commands.scrub_data._parse_scrubber_class_from_string",
                return_value={},
            ) as mocked_method,
            patch("django_scrubber.management.commands.scrub_data._get_fields", return_value=[]),
        ):
            test_scrubbers = _get_model_scrubbers(User)
        mocked_method.assert_called_once()
        self.assertEqual(test_scrubbers, {})

    def test_parse_scrubber_class_from_string_regular(self):
        class_type = _parse_scrubber_class_from_string("tests.test_models.TestDjangoScrubber")
        self.assertIsInstance(class_type, type)

    def test_parse_scrubber_class_from_string_wrong_path(self):
        with self.assertRaises(ImportError):
            _parse_scrubber_class_from_string("not.valid.path")

    def test_parse_scrubber_class_from_string_path_no_separator(self):
        with self.assertRaises(ImportError):
            _parse_scrubber_class_from_string("broken_path")
