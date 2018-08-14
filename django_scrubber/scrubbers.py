from __future__ import absolute_import

from builtins import str as text

import importlib
import logging

import faker

from django.db.models import Func, Subquery, OuterRef
from django.db.models.functions import Concat as DjangoConcat
from django.db.utils import IntegrityError
from django.utils.translation import to_locale, get_language

from . import ScrubberInitError, settings_with_fallback

logger = logging.getLogger(__name__)


class Hash(Func):
    function = 'MD5'
    arity = 1


class Lorem(Func):
    arity = 0
    template = (
        "'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore "
        "et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
        "aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse "
        "cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
        "culpa qui officia deserunt mollit anim id est laborum.'")


class Concat(object):
    '''
    Wrapper around django.db.functions.Concat for lazy concatenation of scrubbers.
    '''

    def __init__(self, *expressions, **kwargs):
        self.expressions = expressions
        self.kwargs = kwargs

    def __call__(self, field_name):
        realized_expressions = list()
        for exp in self.expressions:
            realized_expressions.append(callable(exp) and exp(field_name) or exp)
        return DjangoConcat(*realized_expressions, **self.kwargs)


class Faker(object):
    INITIALIZED_PROVIDERS = set()

    def __init__(self, provider):
        self.provider = provider

    def _initialize_data(self):
        from .models import FakeData
        faker_instance = faker.Faker(locale=to_locale(get_language()))

        # load additional faker providers
        for provider_name in settings_with_fallback('SCRUBBER_ADDITIONAL_FAKER_PROVIDERS'):
            # try to load module
            try:
                module_name, class_name = text(provider_name).rsplit('.', 1)
                module = importlib.import_module(module_name)
            except Exception:
                raise ScrubberInitError(
                    'module not found for provider defined in SCRUBBER_ADDITIONAL_FAKER_PROVIDERS: %s' % provider_name)

            # add provider to faker instance
            provider = getattr(module, class_name, None)
            if provider is None:
                raise ScrubberInitError(
                    'faker provider not found for provider defined in SCRUBBER_ADDITIONAL_FAKER_PROVIDERS: %s' %
                    provider_name)
            faker_instance.add_provider(provider)

        logger.info('Initializing fake scrub data for provider %s' % self.provider)
        # TODO: maybe be a bit smarter and only regenerate if needed?
        FakeData.objects.filter(provider=self.provider).delete()
        fakedata = []

        # if we don't reset the seed for each provider, registering a new one might change all
        # data for subsequent providers
        faker_instance.seed(settings_with_fallback('SCRUBBER_RANDOM_SEED'))
        for i in range(settings_with_fallback('SCRUBBER_ENTRIES_PER_PROVIDER')):
            fakedata.append(FakeData(provider=self.provider, provider_offset=i,
                                     content=faker_instance.format(self.provider)))

        try:
            FakeData.objects.bulk_create(fakedata)
        except IntegrityError as e:
            raise ScrubberInitError('Integrity error initializing faker data (%s); maybe decrease '
                                    'SCRUBBER_ENTRIES_PER_PROVIDER?' % (e,))

        self.INITIALIZED_PROVIDERS.add(self.provider)

    def __call__(self, field_name):
        '''
        Lazily instantiate the actual subquery used for scrubbing.

        The Faker scrubber ignores the field_name parameter.
        '''
        if self.provider not in self.INITIALIZED_PROVIDERS:
            self._initialize_data()

        # import it here to enable global scrubbers in settings.py
        from .models import FakeData

        return Subquery(FakeData.objects.filter(
            provider=self.provider,
            provider_offset=OuterRef('mod_pk')  # this outer field gets annotated before .update()
            # TODO: This can be used instead of the annotated mod_pk, as soon as this issue is fixed:
            # https://code.djangoproject.com/ticket/28621
            # This would allow us to have per-provider cardinality.
            # provider_offset=Mod(OuterRef('pk'), Subquery(FakeData.objects.provider_count(OuterRef('provider'))))
        ).values('content')[:1])
