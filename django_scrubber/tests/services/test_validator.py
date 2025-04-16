import re
from unittest import mock

from django.test import TestCase, override_settings

from django_scrubber import scrubbers
from django_scrubber.services.validator import ScrubberValidatorService


class ScrubberValidatorServiceTest(TestCase):
    class FullUserScrubbers:
        first_name = scrubbers.Hash
        last_name = scrubbers.Hash
        email = scrubbers.Hash
        password = scrubbers.Hash
        username = scrubbers.Hash

    class PartUserScrubbers:
        first_name = scrubbers.Hash
        last_name = scrubbers.Hash
        password = scrubbers.Hash

    def test_process_no_scrubbing(self):
        service = ScrubberValidatorService()
        result = service.process()

        self.assertEqual(len(result), 2)

        model_list = tuple(result.keys())
        self.assertIn("auth.User", model_list)
        self.assertIn("example.DataToBeScrubbed", model_list)

    @override_settings(SCRUBBER_MAPPING={"auth.User": "FullUserScrubbers"})
    @mock.patch(
        "django_scrubber.management.commands.scrub_data._parse_scrubber_class_from_string",
        return_value=FullUserScrubbers,
    )
    def test_process_scrubber_mapper_all_fields(self, mocked_function):
        service = ScrubberValidatorService()
        result = service.process()

        self.assertEqual(len(result), 1)

        model_list = tuple(result.keys())
        self.assertIn("example.DataToBeScrubbed", model_list)

    @override_settings(SCRUBBER_MAPPING={"auth.User": "PartUserScrubbers"})
    @mock.patch(
        "django_scrubber.management.commands.scrub_data._parse_scrubber_class_from_string",
        return_value=PartUserScrubbers,
    )
    def test_process_scrubber_mapper_some_fields(self, mocked_function):
        service = ScrubberValidatorService()
        result = service.process()

        self.assertEqual(len(result), 2)

        model_list = tuple(result.keys())
        self.assertIn("auth.User", model_list)

    @override_settings(SCRUBBER_REQUIRED_FIELD_TYPES=())
    def test_process_scrubber_required_field_type_variable_used(self):
        service = ScrubberValidatorService()
        result = service.process()

        self.assertEqual(len(result), 0)

    @override_settings(
        SCRUBBER_REQUIRED_FIELD_MODEL_WHITELIST=[re.compile("auth.*")],
    )
    def test_process_scrubber_required_field_model_whitelist_regex(self):
        service = ScrubberValidatorService()
        result = service.process()

        model_list = tuple(result.keys())
        self.assertNotIn("auth.User", model_list)
        self.assertNotIn("auth.Permission", model_list)
