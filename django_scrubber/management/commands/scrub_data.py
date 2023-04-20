import datetime
import importlib
import logging
import warnings

from django.apps import apps
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, signals
from django.db.utils import IntegrityError, DataError

from ... import settings_with_fallback
from ...models import FakeData
from ...scrubbers import Keep
from ...services.validator import ScrubberValidatorService

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
        if settings.ENVIRONMENT not in ['STAGING', 'DEVELOP'] :
            # avoid logger, otherwise we might silently fail if we're on live and logging is being sent somewhere else
            self.stderr.write('This command should only be run in our STAGING environment, to avoid running on live systems')
            return False

        # Check STRICT mode
        if settings_with_fallback('SCRUBBER_STRICT_MODE'):
            service = ScrubberValidatorService()
            non_scrubbed_field_list = service.process()
            if len(non_scrubbed_field_list) > 0:
                self.stderr.write('When "SCRUBBER_STRICT_MODE" is enabled, you have to define a scrubbing policy '
                                  'for every text-based field.')
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
            if scrubber_apps_list and model._meta.app_config.name not in scrubber_apps_list:
                continue

            scrubbers = dict()
            for field in model._meta.fields:
                if field.name in global_scrubbers:
                    scrubbers[field] = global_scrubbers[field.name]
                elif type(field) in global_scrubbers:
                    scrubbers[field] = global_scrubbers[type(field)]

            scrubbers.update(_get_model_scrubbers(model))

            # Filter out all fields marked as "to be kept"
            scrubbers_without_kept_fields = {}
            for field, scrubbing_method in scrubbers.items():
                if scrubbing_method != Keep:
                    scrubbers_without_kept_fields[field] = scrubbing_method
            scrubbers = scrubbers_without_kept_fields

            if not scrubbers:
                continue

            realized_scrubbers = _filter_out_disabled(_call_callables(scrubbers))

            logger.info('Scrubbing %s with %s', model._meta.label, realized_scrubbers)

            options = dict(_get_options(model))

            if 'disconnect_signals' in options:
                disconnect_signals = options['disconnect_signals']

                for signal_data in disconnect_signals:
                    model_signal = getattr(signals, signal_data['type'])
                    model_signal.disconnect(
                        sender=signal_data['sender'],
                        dispatch_uid=signal_data['dispatch_uid'],
                    )

            if 'trim_table' in options:
                filter_kwargs = {options['trim_attribute'] + '__gte': datetime.datetime.now() - datetime.timedelta(days=30)}
                delete_queryset = model.objects.filter(**filter_kwargs)

                _large_delete(delete_queryset, model)

            records = model.objects.all()

            if 'exclude' in options:
                records = records.exclude(**options['exclude'])

            try:
                records.annotate(
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

def _get_options(model):
    try:
        options = model.Scrubbers.Meta
    except AttributeError:
        return {}

    return _get_fields(options)

def _large_delete(queryset, model):
    qs_count = queryset.count()
    slice_step = 1000

    for i, qs in enumerate(queryset):
        if hasattr(qs, 'orders'):
            if i % slice_step == 0:
                logger.info('Deleting orders from model {} (progress: {}/{})'.format(model._meta.label, i, qs_count))
            qs.orders.all().hard_delete()
    logger.info('Deleting orders from model {} (progress: {}/{})'.format(model._meta.label, qs_count, qs_count))

    for slice_start in range(0, qs_count, slice_step):
        slice_end = slice_start + slice_step
        logger.info('Deleting model {} (progress: {}/{})'.format(model._meta.label, slice_start, qs_count))
        ids = queryset.values_list('id', flat=True)[slice_start:slice_end]
        model.objects.filter(id__in=ids).delete()
    logger.info('Deleting model {} (progress: {}/{})'.format(model._meta.label, qs_count, qs_count))

    for i, qs in enumerate(queryset):
        if i % slice_step == 0:
            logger.info('Deleting queryset (progress: {}/{})'.format(i, qs_count))
        qs.delete()
    queryset.delete()
    logger.info('Deleting queryset (progress: {}/{})'.format(qs_count, qs_count))

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
        if k == 'Meta':
            continue
        try:
            field = model._meta.get_field(k)
            scrubbers[field] = v
        except FieldDoesNotExist:
            warnings.warn(f'Scrubber defined for {model.__name__}.{k} but field does not exist')

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
