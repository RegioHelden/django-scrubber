from __future__ import absolute_import

import logging

import faker

from django.db.models import Func, Subquery, OuterRef
from django.db.utils import IntegrityError
from django.utils.translation import to_locale, get_language

from . import ScrubberInitError, settings_with_fallback
from .models import FakeData

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


class Faker(object):
    INITIALIZED_PROVIDERS = set()

    def __init__(self, provider):
        self.provider = provider

    def _initialize_data(self):
        faker_instance = faker.Faker(locale=to_locale(get_language()))

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

    def __call__(self, *args, **kwargs):
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
