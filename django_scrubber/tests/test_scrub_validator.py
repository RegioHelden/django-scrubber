from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from django_scrubber.services.validator import ScrubberValidatorService


class TestScrubValidator(TestCase):
    def test_scrub_validator_regular(self):
        with self.assertRaises(SystemExit):
            call_command("scrub_validation", verbosity=3, stdout=StringIO())

    @mock.patch.object(ScrubberValidatorService, "process")
    def test_scrub_validator_service_called(self, mocked_method):
        call_command("scrub_validation", verbosity=3, stdout=StringIO())

        mocked_method.assert_called_once()
