from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.db.models import Value
from django.test import TestCase, override_settings
from django.utils import timezone

from django_scrubber import scrubbers
from django_scrubber.management.commands.scrub_data import _get_model_scrubbers, _parse_scrubber_class_from_string

User = get_user_model()


class TestScrubData(TestCase):
    DEFAULT_USER_FIRST_NAME = "default_test_first_name"
    DEFAULT_SESSION_DATA = "default_test_session_data"

    def setUp(self):
        # model with integer pk
        self.user = User.objects.create(first_name=self.DEFAULT_USER_FIRST_NAME)

        # model with non-integer pk
        self.session = Session.objects.create(
            session_key=uuid4(),
            session_data=self.DEFAULT_SESSION_DATA,
            expire_date=timezone.now() + timedelta(days=1),
        )

    def test_scrub_data(self):
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"first_name": scrubbers.Faker("first_name")}):
            call_command("scrub_data", stdout=StringIO())
        self.user.refresh_from_db()

        self.assertNotEqual(self.user.first_name, self.DEFAULT_USER_FIRST_NAME)

    def test_scrub_data_callable_scrubber(self):
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"first_name": scrubbers.Hash}):
            call_command("scrub_data", stdout=StringIO())
        self.user.refresh_from_db()

        self.assertNotEqual(self.user.first_name, self.DEFAULT_USER_FIRST_NAME)

        # make sure it's a md5 hash
        self.assertRegex(self.user.first_name, "[a-f0-9]{32}")

    def test_scrub_data_debug_is_false(self):
        err = StringIO()

        with self.settings(DEBUG=False):
            call_command("scrub_data", stdout=StringIO(), stderr=err)
        output = err.getvalue()
        self.user.refresh_from_db()

        self.assertIn("This command should only be run with DEBUG=True, to avoid running on live systems", output)
        self.assertEqual(self.user.first_name, self.DEFAULT_USER_FIRST_NAME)

    @override_settings(SCRUBBER_STRICT_MODE=True)
    def test_scrub_data_strict_mode_enabled_scrubbing_blocked(self):
        err = StringIO()

        with self.settings(DEBUG=True):
            call_command("scrub_data", stdout=StringIO(), stderr=err)
        output = err.getvalue()
        self.user.refresh_from_db()

        self.assertIn(
            'When "SCRUBBER_STRICT_MODE" is enabled, '
            "you have to define a scrubbing policy for every text-based field.",
            output,
        )
        self.assertEqual(self.user.first_name, self.DEFAULT_USER_FIRST_NAME)

    def test_hash_simple_global_scrubber(self):
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"first_name": scrubbers.Hash}):
            call_command("scrub_data", stdout=StringIO())
        self.user.refresh_from_db()

        self.assertNotEqual(self.user.first_name, self.DEFAULT_USER_FIRST_NAME)

    def test_hash_simple_class_scrubber(self):
        class Scrubbers:
            first_name = scrubbers.Hash

        with self.settings(DEBUG=True), patch.object(User, "Scrubbers", Scrubbers, create=True):
            call_command("scrub_data", stdout=StringIO())
        self.user.refresh_from_db()

        self.assertNotEqual(self.user.first_name, self.DEFAULT_USER_FIRST_NAME)

    def test_non_integer_primary_key(self):
        class Scrubbers:
            session_data = Value("this is a new value")

        with self.settings(DEBUG=True), patch.object(Session, "Scrubbers", Scrubbers, create=True):
            call_command("scrub_data", "--keep-sessions", stdout=StringIO())

        self.session.refresh_from_db()

        self.assertNotEqual(self.session.session_data, self.DEFAULT_SESSION_DATA)

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
            call_command("scrub_data", stdout=StringIO())

    @override_settings(SCRUBBER_MAPPING={"auth.User": "example.scrubbers.UserScrubbers"})
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
        class_type = _parse_scrubber_class_from_string("django_scrubber.tests.test_models.TestDjangoScrubber")
        self.assertIsInstance(class_type, type)

    def test_parse_scrubber_class_from_string_wrong_path(self):
        with self.assertRaises(ImportError):
            _parse_scrubber_class_from_string("not.valid.path")

    def test_parse_scrubber_class_from_string_path_no_separator(self):
        with self.assertRaises(ImportError):
            _parse_scrubber_class_from_string("broken_path")
