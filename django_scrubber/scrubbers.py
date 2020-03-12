from builtins import str as text

import importlib
import logging

import faker

from django.db import router, connections
from django.db.models import Field, Func, Subquery, OuterRef
from django.db.models.functions import Concat as DjangoConcat, Cast
from django.db.utils import IntegrityError
from django.utils.translation import to_locale, get_language

from . import ScrubberInitError, settings_with_fallback

logger = logging.getLogger(__name__)


class FieldFunc(Func):
    """
    Base class for creating Func-like scrubbers.
    Unlike Func, may receive a Field object as first argument, in which case it populates self.extra with its __dict__.
    This enable derived classes to use the Field's attributes, either in methods or as interpolation variables in
    self.template.
    """
    def __init__(self, field, *args, **kwargs):
        if isinstance(field, Field):
            super(FieldFunc, self).__init__(field.name, *args, **kwargs)
            self.extra.update(field.__dict__)
            self.connection_setup(connections[router.db_for_write(field.model)])
        else:
            super(FieldFunc, self).__init__(field, *args, **kwargs)

    def connection_setup(self, db_connection):
        """
        This function is called when initializing the scrubber, and allows doing setup necessary to support certain DB
        vendors. It should be implemented by derived classes of FieldFunc.
        """
        pass


class Empty(FieldFunc):
    template = "''"


class Null(FieldFunc):
    template = 'NULL'


class Hash(FieldFunc):
    """
    Simple md5 hashing of content.
    If initialized with a Field object, will use its max_length attribute to truncate the generated hash.
    Otherwise, if initialized with a field name as string, will use the full hash length.
    """

    template = 'NULL'  # replaced during __init__
    arity = 1

    def __init__(self, *args, **kwargs):
        super(Hash, self).__init__(*args, **kwargs)
        if self.extra.get('max_length') is not None:
            self.template = 'SUBSTR(MD5(%(expressions)s), 1, %(max_length)s)'
        else:
            self.template = 'MD5(%(expressions)s)'

    def connection_setup(self, db_connection):
        if db_connection.vendor == 'sqlite':
            # add MD5 support for sqlite; this calls back to python and will probably have a performance impact
            import hashlib
            import sqlite3
            sqlite3.enable_callback_tracebacks(True)  # otherwise errors get ignored
            db_connection.connection.create_function("MD5", 1, lambda c: hashlib.md5(c.encode('utf8')).hexdigest())


class Lorem(FieldFunc):
    """
    Simple fixed-text scrubber, which replaces content with one paragraph of the well-known "lorem ipsum" text.
    """

    template = (
        "'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore "
        "et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
        "aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse "
        "cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
        "culpa qui officia deserunt mollit anim id est laborum.'")


class Concat(object):
    """
    Wrapper around django.db.functions.Concat for lazy concatenation of scrubbers.
    """

    def __init__(self, *expressions, **kwargs):
        self.expressions = expressions
        self.kwargs = kwargs

    def __call__(self, field):
        realized_expressions = list()
        for exp in self.expressions:
            realized_expressions.append(callable(exp) and exp(field) or exp)
        return DjangoConcat(*realized_expressions, **self.kwargs)


class Faker(object):
    INITIALIZED_PROVIDERS = set()

    def __init__(self, provider, *args, **kwargs):
        self.provider = provider
        self.provider_args = args
        self.provider_kwargs = kwargs
        args_hash = hash(self.provider_args) ^ hash(tuple(self.provider_kwargs.items()))
        self.provider_key = '%s - %s' % (self.provider, args_hash)

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
                    'module not found for provider defined in SCRUBBER_ADDITIONAL_FAKER_PROVIDERS: %s' % provider_name
                )

            # add provider to faker instance
            provider = getattr(module, class_name, None)
            if provider is None:
                raise ScrubberInitError(
                    'faker provider not found for provider defined in SCRUBBER_ADDITIONAL_FAKER_PROVIDERS: %s' %
                    provider_name)
            faker_instance.add_provider(provider)

        provider_args_str = ', '.join(str(i) for i in self.provider_args)
        provider_kwargs_str = ', '.join(str(i) for i in self.provider_kwargs)
        logger.info('Initializing fake scrub data for provider %s(%s, %s)',
            self.provider, provider_args_str, provider_kwargs_str
        )
        # TODO: maybe be a bit smarter and only regenerate if needed?
        FakeData.objects.filter(provider=self.provider_key).delete()
        fakedata = []

        # if we don't reset the seed for each provider, registering a new one might change all
        # data for subsequent providers
        faker.Generator.seed(settings_with_fallback('SCRUBBER_RANDOM_SEED'))
        for i in range(settings_with_fallback('SCRUBBER_ENTRIES_PER_PROVIDER')):
            fakedata.append(FakeData(provider=self.provider_key, provider_offset=i,
                                     content=faker_instance.format(self.provider, *self.provider_args,
                                                                   **self.provider_kwargs)))

        try:
            FakeData.objects.bulk_create(fakedata)
        except IntegrityError as e:
            raise ScrubberInitError('Integrity error initializing faker data (%s); maybe decrease '
                                    'SCRUBBER_ENTRIES_PER_PROVIDER?' % (e,))

        self.INITIALIZED_PROVIDERS.add(self.provider_key)

    def __call__(self, field):
        """
        Lazily instantiate the actual subquery used for scrubbing.

        The Faker scrubber ignores the field parameter.
        """
        if self.provider_key not in self.INITIALIZED_PROVIDERS:
            self._initialize_data()

        # import it here to enable global scrubbers in settings.py
        from .models import FakeData

        return Cast(Subquery(FakeData.objects.filter(
            provider=self.provider_key,
            provider_offset=OuterRef('mod_pk')  # this outer field gets annotated before .update()
            # TODO: This can be used instead of the annotated mod_pk, as soon as this issue is fixed:
            # https://code.djangoproject.com/ticket/28621
            # This would allow us to have per-provider cardinality.
            # provider_offset=Mod(OuterRef('pk'), Subquery(FakeData.objects.provider_count(OuterRef('provider'))))
        ).values('content')[:1]), field)
