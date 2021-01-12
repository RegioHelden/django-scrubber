from django.conf import settings

__version__ = '0.5.2'

defaults = {
    'SCRUBBER_RANDOM_SEED': 42,  # we prefer idempotent scrubbing
    'SCRUBBER_ENTRIES_PER_PROVIDER': 1000,
    'SCRUBBER_GLOBAL_SCRUBBERS': {},
    'SCRUBBER_SKIP_UNMANAGED': True,
    'SCRUBBER_APPS_LIST': None,
    'SCRUBBER_ADDITIONAL_FAKER_PROVIDERS': [],
}


# TODO: replace with ChainMap now that we only support py3
def settings_with_fallback(key):
    return getattr(settings, key, defaults[key])


class ScrubberInitError(Exception):
    pass
