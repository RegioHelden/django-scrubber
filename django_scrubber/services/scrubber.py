import logging
import warnings
from inspect import getmembers

from django.apps import apps
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import CommandError
from django.db.models import F, IntegerField, Model
from django.db.models.expressions import Func
from django.db.utils import DataError, IntegrityError
from django.utils.module_loading import import_string

from django_scrubber import settings_with_fallback
from django_scrubber.models import FakeData
from django_scrubber.scrubbers import Keep
from django_scrubber.services.validator import ScrubberValidatorService

logger = logging.getLogger(__name__)


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


class ScrubberService:
    """
    Orchestrates the whole scrubbing process. The ``scrub_data`` management command delegates to an instance of
    this class (or a subclass thereof, configured via the ``SCRUBBER_SERVICE_CLASS`` setting).

    Subclass it and override :meth:`pre_scrub` / :meth:`post_scrub` to run custom logic before and/or after
    scrubbing. Configuration (what to clean up) is not done here but through the ``SCRUBBER_*`` settings and the
    command-line arguments, so the service stays purely about behaviour.
    The default implementation reproduces the historic ``scrub_data`` behaviour exactly, so scrubbing works
    out of the box without any additional configuration.
    """

    def __init__(self, *, stdout=None, stderr=None):
        # stdout/stderr are the management command's output streams (may be None when used programmatically)
        self.stdout = stdout
        self.stderr = stderr
        self.logger = logger

    def pre_scrub(self) -> None:
        """
        Hook executed once before any data is scrubbed. Override in a subclass and call your steps
        imperatively - their execution order is simply the order of your statements.
        """

    def post_scrub(self) -> None:
        """
        Hook executed once after all models have been scrubbed but before the admin-log/session/Faker-data
        cleanup. Override in a subclass; see :meth:`pre_scrub` for ordering semantics.
        """

    def run(self, *, model: str | None = None, keep_sessions: bool = False, remove_fake_data: bool = False) -> bool:
        """
        Run the full scrubbing process. ``model``, ``keep_sessions`` and ``remove_fake_data`` mirror the
        ``scrub_data`` command arguments.

        Returns ``True`` when scrubbing ran and ``False`` when it was aborted (e.g. because ``DEBUG`` is off).
        """
        if not settings.DEBUG:
            # avoid logger, otherwise we might silently fail if we're on live and logging is being sent somewhere else
            self._write_stderr("This command should only be run with DEBUG=True, to avoid running on live systems")
            return False

        # Check STRICT mode
        if settings_with_fallback("SCRUBBER_STRICT_MODE"):
            validator = ScrubberValidatorService()
            non_scrubbed_field_list = validator.process()
            if len(non_scrubbed_field_list) > 0:
                self._write_stderr(
                    'When "SCRUBBER_STRICT_MODE" is enabled, you have to define a scrubbing policy '
                    "for every text-based field.",
                )
                return False

        global_scrubbers = settings_with_fallback("SCRUBBER_GLOBAL_SCRUBBERS")

        # A --model-scoped run only touches the requested model; a full run scrubs every model.
        scrub_all_models = model is None

        # Custom pre-scrubbing. Runs before any data is scrubbed - and before the model list is
        # materialized - so a subclass may register/load additional models to be picked up below.
        self.pre_scrub()

        # run for all models of all apps
        if scrub_all_models:
            models = apps.get_models()
        # run only for the selected model
        else:
            try:
                app_label, model_name = model.rsplit(".", 1)
                models = [apps.get_model(app_label=app_label, model_name=model_name)]
            except (LookupError, ValueError) as e:
                raise CommandError("--model should be defined as <app_label>.<model_name>") from e

        scrubber_apps_list = settings_with_fallback("SCRUBBER_APPS_LIST")
        for model_class in models:
            self._scrub_model(model_class, scrubber_apps_list, global_scrubbers)

        # Custom post-scrubbing
        self.post_scrub()

        # The following are global side effects that are not tied to a single model. Only run them
        # on a full scrub, so a --model-scoped run never wipes global tables outside its scope.
        if scrub_all_models:
            # Truncate django admin log (may contain user-related data)
            if settings_with_fallback("SCRUBBER_CLEAR_DJANGO_ADMIN_LOG"):
                self._clear_django_admin_log()

            # Truncate session data
            if not keep_sessions:
                Session.objects.all().delete()

        # Truncate Faker data
        if remove_fake_data:
            FakeData.objects.all().delete()

        return True

    def _clear_django_admin_log(self) -> None:
        # django.contrib.admin is not a hard dependency, so only touch it when it is actually installed
        if not apps.is_installed("django.contrib.admin"):
            self.logger.warning(
                "SCRUBBER_CLEAR_DJANGO_ADMIN_LOG is enabled but 'django.contrib.admin' is not in "
                "INSTALLED_APPS; skipping admin log cleanup.",
            )
            return

        from django.contrib.admin.models import LogEntry  # noqa: PLC0415

        LogEntry.objects.all().delete()

    def _write_stdout(self, message: str) -> None:
        if self.stdout is not None:
            self.stdout.write(message)

    def _write_stderr(self, message: str) -> None:
        if self.stderr is not None:
            self.stderr.write(message)

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

        self._write_stdout(f"Scrubbing {model_class._meta.label} with {realized_scrubbers}")

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
        return import_string(path)
    except ImportError as e:
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
    return ((k, v) for k, v in getmembers(d) if not k.startswith("_"))


def _filter_out_disabled(d):
    """
    Helper to remove Nones (actually any false-like type) from the scrubbers.
    This is needed so we can disable global scrubbers in a per-model basis.
    """
    return {k: v for k, v in d.items() if v}
