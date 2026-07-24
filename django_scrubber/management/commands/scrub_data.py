import importlib

from django.core.management.base import BaseCommand

from django_scrubber import settings_with_fallback

# Re-exported for backwards compatibility: these used to live in this module and may be imported from here.
from django_scrubber.services.scrubber import (  # noqa: F401
    ScrubberService,
    StringToInt,
    _call_callables,
    _filter_out_disabled,
    _get_fields,
    _get_model_scrubbers,
    _parse_scrubber_class_from_string,
    is_primary_key_integer,
)


def _get_scrubber_service_class() -> type[ScrubberService]:
    """
    Resolve the scrubber service class configured via the ``SCRUBBER_SERVICE_CLASS`` setting.
    """
    path = settings_with_fallback("SCRUBBER_SERVICE_CLASS")
    module_name, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


class Command(BaseCommand):
    help = "Replace database data according to model-specific or global scrubbing rules."
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            required=False,
            help="Scrub only a single model (format <app_label>.<model_name>)",
        )
        parser.add_argument(
            "--keep-sessions",
            action="store_true",
            required=False,
            help="Will NOT truncate all (by definition critical) session data",
        )
        parser.add_argument(
            "--remove-fake-data",
            action="store_true",
            required=False,
            help="Will truncate the database table storing preprocessed data for the Faker library. "
            "If you want to do multiple iterations of scrubbing, it will save you time to keep "
            "them. If not, you will add a huge bunch of data to your dump size.",
        )

    def handle(self, *args, **kwargs):
        service_class = _get_scrubber_service_class()
        service = service_class(stdout=self.stdout, stderr=self.stderr)
        service.run(
            model=kwargs.get("model"),
            keep_sessions=kwargs.get("keep_sessions", False),
            remove_fake_data=kwargs.get("remove_fake_data", False),
        )
