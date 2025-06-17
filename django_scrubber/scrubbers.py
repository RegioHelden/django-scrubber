import importlib
import logging
from builtins import str as text
from typing import ClassVar

import faker
from django.db import connections, router
from django.db.models import Field, Func, OuterRef, Subquery
from django.db.models.functions import Cast
from django.db.models.functions import Concat as DjangoConcat
from django.db.utils import IntegrityError
from django.utils.translation import get_language, to_locale

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
            super().__init__(field.name, *args, **kwargs)
            self.extra.update(field.__dict__)
            self.connection_setup(connections[router.db_for_write(field.model)])
        else:
            super().__init__(field, *args, **kwargs)

    def connection_setup(self, db_connection):
        """
        This function is called when initializing the scrubber, and allows doing setup necessary to support certain DB
        vendors. It should be implemented by derived classes of FieldFunc.
        """


class Empty(FieldFunc):
    template = "''"


class Null(FieldFunc):
    template = "NULL"


class Keep(FieldFunc):
    template = None


class Hash(FieldFunc):
    """
    Simple md5 hashing of content.
    If initialized with a Field object, will use its max_length attribute to truncate the generated hash.
    Otherwise, if initialized with a field name as string, will use the full hash length.
    """

    template = "NULL"  # replaced during __init__
    arity = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.extra.get("max_length") is not None:
            self.template = "SUBSTR(MD5(%(expressions)s), 1, %(max_length)s)"
        else:
            self.template = "MD5(%(expressions)s)"


class Lorem(FieldFunc):
    """
    Simple fixed-text scrubber, which replaces content with one paragraph of the well-known "lorem ipsum" text.
    """

    template = (
        "'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore "
        "et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
        "aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse "
        "cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
        "culpa qui officia deserunt mollit anim id est laborum.'"
    )


class Concat:
    """
    Wrapper around django.db.functions.Concat for lazy concatenation of scrubbers.
    """

    def __init__(self, *expressions, **kwargs):
        self.expressions = expressions
        self.kwargs = kwargs

    def __call__(self, field):
        realized_expressions = []
        for exp in self.expressions:
            realized_expressions.append((callable(exp) and exp(field)) or exp)
        return DjangoConcat(*realized_expressions, **self.kwargs)


class Faker:
    INITIALIZED_PROVIDERS: ClassVar[set[str]] = set()

    def __init__(self, provider, *args, **kwargs):
        self.provider = provider
        self.provider_args = args
        self.provider_kwargs = kwargs
        args_hash = hash(self.provider_args) ^ hash(tuple(self.provider_kwargs.items()))
        self.provider_key = f"{self.provider} - {args_hash}"

    def _initialize_data(self):
        from .models import FakeData

        # get locale from config and fall back to django's default one
        locale = settings_with_fallback("SCRUBBER_FAKER_LOCALE")
        if not locale:
            locale = to_locale(get_language())
        faker_instance = faker.Faker(locale=locale)

        # load additional faker providers
        for provider_name in settings_with_fallback("SCRUBBER_ADDITIONAL_FAKER_PROVIDERS"):
            # try to load module
            try:
                module_name, class_name = text(provider_name).rsplit(".", 1)
                module = importlib.import_module(module_name)
            except Exception as e:
                raise ScrubberInitError(
                    f"module not found for provider defined in SCRUBBER_ADDITIONAL_FAKER_PROVIDERS: {provider_name}",
                ) from e

            # add provider to faker instance
            provider = getattr(module, class_name, None)
            if provider is None:
                raise ScrubberInitError(
                    "faker provider not found for provider defined in "
                    f"SCRUBBER_ADDITIONAL_FAKER_PROVIDERS: {provider_name}",
                )
            faker_instance.add_provider(provider)

        provider_args_str = ", ".join(str(i) for i in self.provider_args)
        provider_kwargs_str = ", ".join(str(i) for i in self.provider_kwargs)
        logger.info(
            "Initializing fake scrub data for provider %s(%s, %s)",
            self.provider,
            provider_args_str,
            provider_kwargs_str,
        )
        # TODO: maybe be a bit smarter and only regenerate if needed?
        FakeData.objects.filter(provider=self.provider_key).delete()
        fakedata = []

        # if we don't reset the seed for each provider, registering a new one might change all
        # data for subsequent providers
        faker.Generator.seed(settings_with_fallback("SCRUBBER_RANDOM_SEED"))
        for i in range(settings_with_fallback("SCRUBBER_ENTRIES_PER_PROVIDER")):
            fakedata.append(
                FakeData(
                    provider=self.provider_key,
                    provider_offset=i,
                    content=faker_instance.format(self.provider, *self.provider_args, **self.provider_kwargs),
                ),
            )

        try:
            FakeData.objects.bulk_create(fakedata)
        except IntegrityError as e:
            raise ScrubberInitError(
                f"Integrity error initializing faker data ({e}); maybe decrease SCRUBBER_ENTRIES_PER_PROVIDER?",
            ) from e

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

        return Cast(
            Subquery(
                FakeData.objects.filter(
                    provider=self.provider_key,
                    provider_offset=OuterRef("mod_pk"),
                ).values("content")[:1],
            ),
            field,
        )
