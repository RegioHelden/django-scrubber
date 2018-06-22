from __future__ import absolute_import

from django.db.models import Func, Subquery, OuterRef


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
    PROVIDERS = []

    def __init__(self, provider):
        self.provider = provider
        self.PROVIDERS.append(provider)

    def __call__(self, *args, **kwargs):
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
