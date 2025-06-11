from datetime import timedelta
from io import StringIO

import django
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.utils import timezone

from django_scrubber import scrubbers
from django_scrubber.models import FakeData
from example.models import DataFactory, DataToBeScrubbed


class TestScrubbers(TestCase):
    def test_empty_scrubber(self):
        data = DataFactory.create(first_name="Foo")
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"first_name": scrubbers.Empty}):
            call_command("scrub_data", stdout=StringIO())
        data.refresh_from_db()

        self.assertEqual(data.first_name, "")

    def test_null_scrubber(self):
        data = DataFactory.create(date_past=timezone.now().date())
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"date_past": scrubbers.Null}):
            call_command("scrub_data", stdout=StringIO())
        data.refresh_from_db()

        self.assertEqual(data.date_past, None)

    def test_hash_scrubber_max_length(self):
        data = DataFactory.create(first_name="Foo")
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"first_name": scrubbers.Hash}):
            call_command("scrub_data", stdout=StringIO())
        data.refresh_from_db()

        self.assertNotEqual(data.first_name, "Foo")
        self.assertEqual(
            len(data.first_name),
            DataToBeScrubbed._meta.get_field("first_name").max_length,
            "len({}) != {}".format(data.first_name, DataToBeScrubbed._meta.get_field("first_name").max_length),
        )

    def test_hash_scrubber_textfield(self):
        data = DataFactory.create(description="Foo")
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"description": scrubbers.Hash}):
            call_command("scrub_data", stdout=StringIO())
        data.refresh_from_db()

        self.assertNotEqual(data.description, "Foo")

    def test_lorem_scrubber(self):
        data = DataFactory.create(description="Foo")
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"description": scrubbers.Lorem}):
            call_command("scrub_data", stdout=StringIO())
        data.refresh_from_db()

        self.assertNotEqual(data.description, "Foo")
        self.assertEqual(data.description[:11], "Lorem ipsum")

    def test_faker_scrubber_charfield(self):
        data = DataFactory.create(last_name="Foo")
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"last_name": scrubbers.Faker("last_name")}):
            call_command("scrub_data", stdout=StringIO())
        data.refresh_from_db()

        self.assertNotEqual(data.last_name, "Foo")
        self.assertNotEqual(data.last_name, "")

    def test_faker_scrubber_with_provider_arguments(self):
        """
        Use this as an example for Faker scrubbers with parameters passed along
        """
        data = DataFactory.create(ean8="8")
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"ean8": scrubbers.Faker("ean", length=8)}):
            call_command("scrub_data", stdout=StringIO())
        data.refresh_from_db()

        # The EAN Faker will by default emit ean13, so this would fail if the parameter was ignored
        self.assertEqual(8, len(data.ean8))

        # Add a new scrubber for ean13
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"ean8": scrubbers.Faker("ean", length=13)}):
            call_command("scrub_data", stdout=StringIO())
        data.refresh_from_db()

        # make sure it doesn't reuse the ean with length=8 scrubber
        self.assertEqual(13, len(data.ean8))

    def test_faker_scrubber_datefield(self):
        """
        Use this as an example for Scrubber's capability of optimistically Casting to the current field's type
        There is a bug with django < 2.1 and sqlite, that's why we don't run the test there.
        """
        if django.VERSION >= (2, 1) or connection.vendor != "sqlite":
            today = timezone.now().date()

            data = DataFactory.create(date_past=today)
            with self.settings(
                DEBUG=True,
                SCRUBBER_GLOBAL_SCRUBBERS={
                    "date_past": scrubbers.Faker(
                        "past_date",
                        start_date="-30d",
                        tzinfo=timezone.get_current_timezone(),
                    ),
                },
            ):
                call_command("scrub_data", stdout=StringIO())
            data.refresh_from_db()

            self.assertGreater(today, data.date_past)
            self.assertLess(today - timedelta(days=31), data.date_past)

    def test_faker_scrubber_run_twice(self):
        """
        Use this as an example of what happens when you want to run the same Faker scrubbers twice
        """
        data = DataFactory.create(company="Foo")
        with self.settings(DEBUG=True, SCRUBBER_GLOBAL_SCRUBBERS={"company": scrubbers.Faker("company")}):
            call_command("scrub_data", stdout=StringIO())
            call_command("scrub_data", stdout=StringIO())
        data.refresh_from_db()

        self.assertNotEqual(data.company, "Foo")
        self.assertNotEqual(data.company, "")

    @override_settings(DEBUG=True)
    def test_faker_scrubber_run_clear_session_by_default(self):
        """
        Ensures that the session table will be emptied by default
        """
        # Create session object
        Session.objects.create(session_key="foo", session_data="Lorem ipsum", expire_date=timezone.now())

        # Sanity check
        self.assertTrue(Session.objects.all().exists())

        # Call command
        call_command("scrub_data", stdout=StringIO())

        # Assertion that session table is empty now
        self.assertFalse(Session.objects.all().exists())

    @override_settings(DEBUG=True)
    def test_faker_scrubber_run_disable_session_clearing(self):
        """
        Ensures that the session table will be emptied by default
        """
        # Create session object
        Session.objects.create(session_key="foo", session_data="Lorem ipsum", expire_date=timezone.now())

        # Sanity check
        self.assertTrue(Session.objects.all().exists())

        # Call command
        call_command("scrub_data", keep_sessions=True, stdout=StringIO())

        # Assertion that session table is empty now
        self.assertTrue(Session.objects.all().exists())

    @override_settings(DEBUG=True)
    def test_faker_scrubber_run_clear_faker_data_not_by_default(self):
        """
        Ensure that scrubbing does not delete stored faker data unless explicitly requested.
        """
        # Create faker data object
        FakeData.objects.create(provider="company", content="Foo", provider_offset=1)

        # Sanity check
        self.assertTrue(FakeData.objects.filter(provider="company", content="Foo").exists())

        # Call command
        call_command("scrub_data", stdout=StringIO())

        # Assertion that faker data still exists
        self.assertTrue(FakeData.objects.filter(provider="company", content="Foo").exists())

    @override_settings(DEBUG=True)
    def test_faker_scrubber_run_clear_faker_data_works(self):
        """
        Ensures that fake data is cleared when requested
        """
        # Create faker data object
        FakeData.objects.create(provider="company", content="Foo", provider_offset=1)

        # Sanity check
        self.assertTrue(FakeData.objects.filter(provider="company", content="Foo").exists())

        # Call command
        call_command("scrub_data", remove_fake_data=True, stdout=StringIO())

        # Assertion that the faker data was removed
        self.assertFalse(FakeData.objects.filter(provider="company", content="Foo").exists())
