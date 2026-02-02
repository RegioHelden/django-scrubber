import importlib
import logging
from builtins import str as text
from typing import ClassVar

import faker
from django.db import connections, router
from django.db.models import Case, ExpressionWrapper, F, Field, Func, OuterRef, Q, Subquery, When
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
    Simple hashing of content.
    If initialized with a Field object, will use its max_length attribute to truncate the generated hash.
    Otherwise, if initialized with a field name as string, will use the full hash length.

    Supported vendors out of the box are : mysql, postgresql and sqlite
    If you use any other vendor and the default implementation (sqlite) does not work,
    then please use settings SCRUBBER_HASH_TEMPLATE and SCRUBBER_HASH_TEMPLATE_MAX_LENGTH to define
    custom templates.
    """

    template = "NULL"  # replaced during `as_sql`
    arity = 1

    TEMPLATE_SQLITE: str = "MD5(%(expressions)s)"
    TEMPLATE_SQLITE_MAX_LENGTH: str = f"SUBSTR({TEMPLATE_SQLITE}, 1, %(max_length)s)"
    TEMPLATE_MYSQL: str = "SHA2(%(expressions)s, 256)"
    TEMPLATE_MYSQL_MAX_LENGTH: str = f"SUBSTR({TEMPLATE_MYSQL}, 1, %(max_length)s)"
    TEMPLATE_POSTGRESQL: str = "ENCODE(SHA256(CONVERT_TO(%(expressions)s, 'UTF-8')), 'hex')"
    TEMPLATE_POSTGRESQL_MAX_LENGTH: str = f"SUBSTR({TEMPLATE_POSTGRESQL}, 1, %(max_length)s)"

    def as_sql(
        self,
        compiler,
        connection,
        function=None,
        template=None,
        arg_joiner=None,
        **extra_context,
    ) -> str:
        # dynamically replace template by vendor specific code
        if self.extra.get("max_length") is not None:
            template: str = self._get_template_max_length(vendor=connection.vendor)
        else:
            template: str = self._get_template(vendor=connection.vendor)

        return super().as_sql(
            compiler,
            connection,
            function=function,
            template=template,
            arg_joiner=arg_joiner,
            **extra_context,
        )

    def _get_template(self, vendor: str) -> str:
        # custom hash template might be defined in settings
        custom_template: str | None = settings_with_fallback("SCRUBBER_HASH_TEMPLATE")
        if custom_template is not None:
            return custom_template

        if vendor == "mysql":
            return self.TEMPLATE_MYSQL

        if vendor == "postgresql":
            return self.TEMPLATE_POSTGRESQL

        if vendor == "sqlite":
            return self.TEMPLATE_SQLITE

        raise ScrubberInitError(
            f"Unsupported database vendor '{vendor}' for Hash scrubber. "
            "Please define a custom template using SCRUBBER_HASH_TEMPLATE setting or open a MR.",
        )

    def _get_template_max_length(self, vendor: str) -> str:
        # custom hash template might be defined in settings
        custom_template: str | None = settings_with_fallback(key="SCRUBBER_HASH_TEMPLATE_MAX_LENGTH")
        if custom_template is not None:
            return custom_template

        if vendor == "mysql":
            return self.TEMPLATE_MYSQL_MAX_LENGTH

        if vendor == "postgresql":
            return self.TEMPLATE_POSTGRESQL_MAX_LENGTH

        if vendor == "sqlite":
            return self.TEMPLATE_SQLITE_MAX_LENGTH

        raise ScrubberInitError(
            f"Unsupported database vendor '{vendor}' for Hash scrubber. "
            "Please define a custom template using SCRUBBER_HASH_TEMPLATE setting or open a MR.",
        )


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
        from .models import FakeData  # noqa: PLC0415

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
        provider_kwargs_str = ", ".join(f"{k}={v}" for k, v in self.provider_kwargs.items())
        logger.info(
            "Initializing fake scrub data for provider %s(%s, %s)",
            self.provider,
            provider_args_str,
            provider_kwargs_str,
        )
        # TODO: maybe be a bit smarter and only regenerate if needed?
        FakeData.objects.filter(provider=self.provider_key).delete()

        # if we don't reset the seed for each provider, registering a new one might change all
        # data for subsequent providers
        faker.Generator.seed(settings_with_fallback("SCRUBBER_RANDOM_SEED"))

        fakedata: list[FakeData] = [
            FakeData(
                provider=self.provider_key,
                provider_offset=i,
                content=str(faker_instance.format(self.provider, *self.provider_args, **self.provider_kwargs)),
            )
            for i in range(settings_with_fallback("SCRUBBER_ENTRIES_PER_PROVIDER"))
        ]

        # check if fake data is fitting our data structure
        # warn and truncate if not
        max_length: int = FakeData._meta.get_field("content").max_length
        if any(len(item.content) > max_length for item in fakedata):
            logger.warning(
                "Fake data content exceeds max length of %s characters. "
                "django-scrubber will automatically truncate it. "
                "This might however lead to invalid data, e.g. cut off email addresses",
                max_length,
            )
            [setattr(x, "content", x.content[:max_length]) for x in fakedata]

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
        from .models import FakeData  # noqa: PLC0415

        return Cast(
            Subquery(
                FakeData.objects.filter(
                    provider=self.provider_key,
                    provider_offset=OuterRef("mod_pk"),
                ).values("content")[:1],
            ),
            field,
        )


class IfNotEmpty:
    """
    wrapper around other scrubber expressions that will only be executed if the field already contained a value
    """

    def __init__(self, expression, **kwargs):
        self.expression = expression
        self.kwargs = kwargs

    def __call__(self, field):
        # fall back to field class for output field
        if "output_field" not in self.kwargs:
            self.kwargs["output_field"] = field.__class__()

        return Case(
            When(
                ~Q(**{field.name: ""}),
                then=ExpressionWrapper(
                    expression=self.expression(field) if callable(self.expression) else self.expression,
                    **self.kwargs,
                ),
            ),
            default=F(field.name),
        )
