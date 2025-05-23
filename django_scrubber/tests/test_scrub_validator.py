from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings

from django_scrubber.services.validator import ScrubberValidatorService


class TestScrubValidator(TestCase):
    @override_settings(SCRUBBER_STRICT_MODE=False)
    def test_scrub_validator_regular(self):
        out = StringIO()

        with self.assertRaises(SystemExit) as exc:
            call_command(
                "scrub_validation",
                verbosity=3,
                stdout=out,
            )

        self.assertEqual(exc.exception.code, 0)
        self.assertIn("unscrubbed field(s) detected", out.getvalue())
        self.assertIn("However strict mode is deactivated and scrubbing is not enforced.", out.getvalue())

    @override_settings(SCRUBBER_STRICT_MODE=True)
    def test_scrub_validator_strict_mode(self):
        out = StringIO()

        with self.assertRaises(SystemExit) as exc:
            call_command(
                "scrub_validation",
                verbosity=3,
                stdout=out,
            )

        self.assertEqual(exc.exception.code, 1)
        self.assertIn("unscrubbed field(s) detected", out.getvalue())
        self.assertNotIn("However strict mode is deactivated and scrubbing is not enforced.", out.getvalue())

    @mock.patch.object(ScrubberValidatorService, "process")
    def test_scrub_validator_service_called(self, mocked_method):
        out = StringIO()

        call_command("scrub_validation", verbosity=3, stdout=out)

        mocked_method.assert_called_once()
        self.assertIn("No unscrubbed fields detected. Yeah!", out.getvalue())
