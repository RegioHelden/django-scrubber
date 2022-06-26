import importlib
import logging

from django.apps import apps
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from django.db.utils import IntegrityError, DataError

from ... import settings_with_fallback
from ...models import FakeData

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Replace database data according to model-specific or global scrubbing rules.'
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument('--model', type=str, required=False,
                            help='Scrub only a single model (format <app_label>.<model_name>)')
        parser.add_argument('--keep-sessions', action='store_true', required=False,
                            help='Will NOT truncate all (by definition critical) session data')
        parser.add_argument('--remove-fake-data', action='store_true', required=False,
                            help='Will truncate the database table storing preprocessed data for the Faker library. '
                                 'If you want to do multiple iterations of scrubbing, it will save you time to keep '
                                 'them. If not, you will add a huge bunch of data to your dump size.')

    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            # avoid logger, otherwise we might silently fail if we're on live and logging is being sent somewhere else
            self.stderr.write('this command should only be run with DEBUG=True, to avoid running on live systems')
            return False

        global_scrubbers = settings_with_fallback('SCRUBBER_GLOBAL_SCRUBBERS')

        # run only for selected model
        if kwargs.get('model', None) is not None:
            app_label, model_name = kwargs.get('model').rsplit('.', 1)
            try:
                models = [apps.get_model(app_label=app_label, model_name=model_name)]
            except LookupError:
                raise CommandError('--model should be defined as <app_label>.<model_name>')

        # run for all models of all apps
        else:
            models = apps.get_models()

        scrubber_apps_list = settings_with_fallback('SCRUBBER_APPS_LIST')
        for model in models:
            if model._meta.proxy:
                continue
            if settings_with_fallback('SCRUBBER_SKIP_UNMANAGED') and not model._meta.managed:
                continue
            if (scrubber_apps_list and model._meta.app_config.name not in scrubber_apps_list):
                continue

            scrubbers = dict()
            for field in model._meta.fields:
                if field.name in global_scrubbers:
                    scrubbers[field] = global_scrubbers[field.name]
                elif type(field) in global_scrubbers:
                    scrubbers[field] = global_scrubbers[type(field)]

            scrubbers.update(_get_model_scrubbers(model))

            if not scrubbers:
                continue

            realized_scrubbers = _filter_out_disabled(_call_callables(scrubbers))

            logger.info('Scrubbing %s with %s', model._meta.label, realized_scrubbers)

            try:
                model.objects.annotate(
                    mod_pk=F('pk') % settings_with_fallback('SCRUBBER_ENTRIES_PER_PROVIDER')
                ).update(**realized_scrubbers)
            except IntegrityError as e:
                raise CommandError('Integrity error while scrubbing %s (%s); maybe increase '
                                   'SCRUBBER_ENTRIES_PER_PROVIDER?' % (model, e))
            except DataError as e:
                raise CommandError('DataError while scrubbing %s (%s)' % (model, e))

        # Truncate session data
        if not kwargs.get('keep_sessions', False):
            Session.objects.all().delete()

        # Truncate Faker data
        if kwargs.get('remove_fake_data', False):
            FakeData.objects.all().delete()


def _call_callables(d):
    """
    Helper to realize lazy scrubbers, like Faker, or global field-type scrubbers
    """
    return {k.name: (callable(v) and v(k) or v) for k, v in d.items()}


def _parse_scrubber_class_from_string(path: str):
    """
    Takes a string to a certain scrubber class and returns a python class definition - not an instance.
    """
    try:
        module_name, class_name = path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except (ImportError, ValueError) as e:
        raise ImportError('Mapped scrubber class "%s" could not be found.' % path) from e


def _get_model_scrubbers(model):
    # Get model-scrubber-mapping from settings
    scrubber_mapping = settings_with_fallback('SCRUBBER_MAPPING')

    # Initialise scrubber list
    scrubbers = dict()

    # Check if model has a settings-defined...
    if model._meta.label in scrubber_mapping:
        scrubber_cls = _parse_scrubber_class_from_string(scrubber_mapping[model._meta.label])
    # If not...
    else:
        # Try to get the scrubber metaclass from the given model
        try:
            scrubber_cls = getattr(model, 'Scrubbers')
        except AttributeError:
            return scrubbers  # no model-specific scrubbers

    # Get field mappings from scrubber class
    for k, v in _get_fields(scrubber_cls):
        try:
            field = model._meta.get_field(k)
        except FieldDoesNotExist:
            raise

        scrubbers[field] = v

    # Return scrubber-field-mapping
    return scrubbers


def _get_fields(d):
    """
    Helper to get "normal" (i.e.: non-magic and non-dunder) instance attributes.
    Returns an iterator of (field_name, field) tuples.
    """
    return ((k, v) for k, v in vars(d).items() if not k.startswith('_'))


def _filter_out_disabled(d):
    """
    Helper to remove Nones (actually any false-like type) from the scrubbers.
    This is needed so we can disable global scrubbers in a per-model basis.
    """
    return {k: v for k, v in d.items() if v}
