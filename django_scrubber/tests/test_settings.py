from django.test import TestCase, override_settings

from django_scrubber import defaults, settings_with_fallback


class TestScrubbers(TestCase):
    def test_default(self):
        self.assertEqual(
            defaults["SCRUBBER_RANDOM_SEED"],
            settings_with_fallback("SCRUBBER_RANDOM_SEED"),
        )

    @override_settings(SCRUBBER_RANDOM_SEED=9001)
    def test_override(self):
        self.assertEqual(
            9001,
            settings_with_fallback("SCRUBBER_RANDOM_SEED"),
        )
