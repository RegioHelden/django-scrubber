import importlib
import warnings

from django.apps import apps
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, IntegerField, Model
from django.db.models.expressions import Func
from django.db.utils import DataError, IntegrityError

from django_scrubber import settings_with_fallback
from django_scrubber.models import FakeData
from django_scrubber.scrubbers import Keep
from django_scrubber.services.validator import ScrubberValidatorService


class StringToInt(Func):
    """
    database-specific implementations for reproducible conversion of a field value to an integer
    """

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template="ABS(CAST(SUBSTR(UPPER(MD5(CAST(%(expressions)s AS VARCHAR))), 1, 16) AS BIGINT))",
            **extra_context,
        )

    def as_mysql(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template="ABS(CONV(SUBSTRING(MD5(CONCAT('x', %(expressions)s)), 1, 16), 16, 10))",
            **extra_context,
        )

    def as_postgresql(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler,
            connection,
            template="ABS(CAST(CAST(('x' || MD5(CAST(%(expressions)s AS VARCHAR))) AS BIT(64)) AS BIGINT))",
            **extra_context,
        )

    def as_oracle(self, compiler, connection, **extra_context):
        raise Exception("No custom implementation for Oracle (yet)")


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
        if not settings.DEBUG:
            # avoid logger, otherwise we might silently fail if we're on live and logging is being sent somewhere else
            self.stderr.write("This command should only be run with DEBUG=True, to avoid running on live systems")
            return False

        # Check STRICT mode
        if settings_with_fallback("SCRUBBER_STRICT_MODE"):
            service = ScrubberValidatorService()
            non_scrubbed_field_list = service.process()
            if len(non_scrubbed_field_list) > 0:
                self.stderr.write(
                    'When "SCRUBBER_STRICT_MODE" is enabled, you have to define a scrubbing policy '
                    "for every text-based field.",
                )
                return False

        global_scrubbers = settings_with_fallback("SCRUBBER_GLOBAL_SCRUBBERS")

        # run only for selected model
        if kwargs.get("model") is not None:
            app_label, model_name = kwargs.get("model").rsplit(".", 1)
            try:
                models = [apps.get_model(app_label=app_label, model_name=model_name)]
            except LookupError as e:
                raise CommandError("--model should be defined as <app_label>.<model_name>") from e

        # run for all models of all apps
        else:
            models = apps.get_models()

        scrubber_apps_list = settings_with_fallback("SCRUBBER_APPS_LIST")
        for model_class in models:
            self._scrub_model(model_class, scrubber_apps_list, global_scrubbers)

        # Truncate session data
        if not kwargs.get("keep_sessions", False):
            Session.objects.all().delete()

        # Truncate Faker data
        if kwargs.get("remove_fake_data", False):
            FakeData.objects.all().delete()
            return None
        return None

    def _scrub_model(self, model_class, scrubber_apps_list, global_scrubbers):
        if (
            model_class._meta.proxy
            or (settings_with_fallback("SCRUBBER_SKIP_UNMANAGED") and not model_class._meta.managed)
            or (scrubber_apps_list and model_class._meta.app_config.name not in scrubber_apps_list)
        ):
            return

        scrubbers = {}
        for field in model_class._meta.fields:
            if field.name in global_scrubbers:
                scrubbers[field] = global_scrubbers[field.name]
            elif type(field) in global_scrubbers:
                scrubbers[field] = global_scrubbers[type(field)]

        scrubbers.update(_get_model_scrubbers(model_class))

        # Filter out all fields marked as "to be kept"
        scrubbers_without_kept_fields = {}
        for field, scrubbing_method in scrubbers.items():
            if scrubbing_method != Keep:
                scrubbers_without_kept_fields[field] = scrubbing_method
        scrubbers = scrubbers_without_kept_fields

        if not scrubbers:
            return

        realized_scrubbers = _filter_out_disabled(_call_callables(scrubbers))

        self.stdout.write(f"Scrubbing {model_class._meta.label} with {realized_scrubbers}")

        try:
            if is_primary_key_integer(model_class=model_class):
                model_class.objects.annotate(
                    mod_pk=F("pk") % settings_with_fallback("SCRUBBER_ENTRIES_PER_PROVIDER"),
                ).update(**realized_scrubbers)
            else:
                model_class.objects.annotate(
                    mod_pk=StringToInt(F("pk")) % settings_with_fallback("SCRUBBER_ENTRIES_PER_PROVIDER"),
                ).update(**realized_scrubbers)
        except IntegrityError as e:
            raise CommandError(
                f"Integrity error while scrubbing {model_class} ({e}); maybe increase SCRUBBER_ENTRIES_PER_PROVIDER?",
            ) from e
        except DataError as e:
            raise CommandError(f"DataError while scrubbing {model_class} ({e})") from e


def is_primary_key_integer(model_class: Model):
    # checks if the primary key of a model is an integer or integer-derived (e.g. AutoField) field
    for field in model_class._meta.concrete_fields:
        if field.primary_key is True:
            return isinstance(field, IntegerField)
    raise Exception("no primary key defined in model")


def _call_callables(d):
    """
    Helper to realize lazy scrubbers, like Faker, or global field-type scrubbers
    """
    return {k.name: (v(k) if callable(v) else v) for k, v in d.items()}


def _parse_scrubber_class_from_string(path: str):
    """
    Takes a string to a certain scrubber class and returns a python class definition - not an instance.
    """
    try:
        module_name, class_name = path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except (ImportError, ValueError) as e:
        raise ImportError(f'Mapped scrubber class "{path}" could not be found.') from e


def _get_model_scrubbers(model):
    # Get model-scrubber-mapping from settings
    scrubber_mapping = settings_with_fallback("SCRUBBER_MAPPING")

    # Initialise scrubber list
    scrubbers = {}

    # Check if model has a settings-defined...
    if model._meta.label in scrubber_mapping:
        scrubber_cls = _parse_scrubber_class_from_string(scrubber_mapping[model._meta.label])
    # If not...
    else:
        # Try to get the scrubber metaclass from the given model
        try:
            scrubber_cls = model.Scrubbers
        except AttributeError:
            return scrubbers  # no model-specific scrubbers

    # Get field mappings from scrubber class
    for k, v in _get_fields(scrubber_cls):
        try:
            field = model._meta.get_field(k)
            scrubbers[field] = v
        except FieldDoesNotExist:
            warnings.warn(f"Scrubber defined for {model.__name__}.{k} but field does not exist", stacklevel=2)

    # Return scrubber-field-mapping
    return scrubbers


def _get_fields(d):
    """
    Helper to get "normal" (i.e.: non-magic and non-dunder) instance attributes.
    Returns an iterator of (field_name, field) tuples.
    """
    return ((k, v) for k, v in vars(d).items() if not k.startswith("_"))


def _filter_out_disabled(d):
    """
    Helper to remove Nones (actually any false-like type) from the scrubbers.
    This is needed so we can disable global scrubbers in a per-model basis.
    """
    return {k: v for k, v in d.items() if v}
