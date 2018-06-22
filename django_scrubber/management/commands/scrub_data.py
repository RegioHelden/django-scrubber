from __future__ import absolute_import

import logging

from django.conf import settings
from django.db.models import F
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

from ... import settings_with_fallback

logger = logging.getLogger(__name__)

# py2/3 compat; no need for six
try:
    range = xrange
except NameError:
    range = range


class Command(BaseCommand):
    help = 'Replace database data according to model-specific or global scrubbing rules.'
    leave_locale_alone = True

    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            # avoid logger, otherwise we might silently fail if we're on live and logging is being sent somewhere else
            self.stderr.write('this command should only be run with DEBUG=True, to avoid running on live systems')
            return False

        global_scrubbers = settings_with_fallback('SCRUBBER_GLOBAL_SCRUBBERS')
        for model in apps.get_models():
            if settings_with_fallback('SCRUBBER_SKIP_UNMANAGED') and not model._meta.managed:
                continue
            if (settings_with_fallback('SCRUBBER_APPS_LIST') and
                    model._meta.app_config.name not in settings_with_fallback('SCRUBBER_APPS_LIST')):
                continue

            scrubbers = dict()
            for field in model._meta.fields:
                if field.name in global_scrubbers:
                    scrubbers[field.name] = global_scrubbers[field.name]
                elif type(field) in global_scrubbers:
                    scrubbers[field.name] = global_scrubbers[type(field)]

            try:
                scrubbers.update(_get_fields(getattr(model, 'Scrubbers')))
            except AttributeError:
                pass  # no model-specific scrubbers

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


def _call_callables(d):
    '''
    Helper to realize lazy scrubbers, like Faker, or global field-type scrubbers
    '''
    return {k: (callable(v) and v(k) or v) for k, v in d.items()}


def _get_fields(d):
    '''
    Helper to get "normal" (i.e.: non-magic and non-dunder) instance attributes
    '''
    return {k: v for k, v in vars(d).items() if not k.startswith('_')}


def _filter_out_disabled(d):
    '''
    Helper to remove Nones (actually any false-like type) from the scrubbers.
    This is needed so we can disable global scrubbers in a per-model basis.
    '''
    return {k: v for k, v in d.items() if v}
