try:
    from unittest import mock
except ImportError:
    import mock

from django.test import override_settings, TestCase

from django_scrubber import scrubbers
from django_scrubber.services.validator import ScrubberValidatorService


class ScrubberValidatorServiceTest(TestCase):
    class TestScrubbers:
        name = scrubbers.Hash

    def test_process_no_scrubbing(self):
        service = ScrubberValidatorService()
        result = service.process()

        self.assertEqual(len(result), 7)

        model_list = tuple(result.keys())
        self.assertIn('auth.Permission', model_list)
        self.assertIn('auth.Group', model_list)
        self.assertIn('auth.User', model_list)
        self.assertIn('contenttypes.ContentType', model_list)
        self.assertIn('sessions.Session', model_list)
        self.assertIn('sites.Site', model_list)
        self.assertIn('django_scrubber.FakeData', model_list)

    @override_settings(SCRUBBER_MAPPING={"auth.Group": "TestScrubbers"})
    @mock.patch('django_scrubber.management.commands.scrub_data._parse_scrubber_class_from_string',
                return_value=TestScrubbers)
    def test_process_scrubber_mapper(self, mocked_function):
        service = ScrubberValidatorService()
        result = service.process()

        self.assertEqual(len(result), 6)

        model_list = tuple(result.keys())
        self.assertNotIn('auth.Group', model_list)

    @override_settings(SCRUBBER_REQUIRED_FIELD_TYPES=tuple())
    def test_process_scrubber_required_field_type_variable_used(self):
        service = ScrubberValidatorService()
        result = service.process()

        self.assertEqual(len(result), 0)
