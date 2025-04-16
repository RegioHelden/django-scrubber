# Django Scrubber

[![Build Status](https://github.com/RegioHelden/django-scrubber/workflows/Build/badge.svg)](https://github.com/RegioHelden/django-scrubber/actions)
[![PyPI](https://img.shields.io/pypi/v/django-scrubber.svg)](https://pypi.org/project/django-scrubber/)
[![Downloads](https://pepy.tech/badge/django-scrubber)](https://pepy.tech/project/django-scrubber)

`django_scrubber` is a django app meant to help you anonymize your project's database data. It destructively alters data
directly on the DB and therefore **should not be used on production**.

The main use case is providing developers with realistic data to use during development, without having to distribute
your customers' or users' potentially sensitive information.
To accomplish this, `django_scrubber` should be plugged in a step during the creation of your database dumps.

Simply mark the fields you want to anonymize and call the `scrub_data` management command. Data will be replaced based
on different *scrubbers* (see below), which define how the anonymous content will be generated.

If you want to be sure that you don't forget any fields in the ongoing development progress, you can use the 
management command `scrub_validation` in your CI/CD pipeline to check for any missing fields.

## Installation

Simply run:

```
pip install django-scrubber
```

And add `django_scrubber` to your django `INSTALLED_APPS`. I.e.: in `settings.py` add:

```
INSTALLED_APPS = [
  ...
  'django_scrubber.apps.DjangoScrubberConfig',
  ...
]
```

## Scrubbing data

In order to scrub data, i.e.: to replace DB data with anonymized versions, `django-scrubber` must know which models and
fields it should act on, and how the data should be replaced.

There are a few different ways to select which data should be scrubbed, namely: explicitly per model field; or globally
per name or field type.

Adding scrubbers directly to model, matching scrubbers to fields by name:

```python
class MyModel(Model):
    somefield = CharField()

    class Scrubbers:
        somefield = scrubbers.Hash('somefield')
```

Adding scrubbers globally, either by field name or field type:

```python
# (in settings.py)

SCRUBBER_GLOBAL_SCRUBBERS = {
    'name': scrubbers.Hash,
    EmailField: scrubbers.Hash,
}
```

Model scrubbers override field-name scrubbers, which in turn override field-type scrubbers.

To disable global scrubbing in some specific model, simply set the respective field scrubber to `None`.

Scrubbers defined for non-existing fields will raise a warning but not fail the scubbing process.

Which mechanism will be used to scrub the selected data is determined by using one of the provided scrubbers
in `django_scrubber.scrubbers`. See below for a list.
Alternatively, values may be anything that can be used as a value in a `QuerySet.update()` call (like `Func` instances,
string literals, etc), or any `callable` that returns such an object when called with a `Field` object as argument.

By default, `django_scrubber` will affect all models from all registered apps. This may lead to issues with third-party
apps if the global scrubbers are too general. This can be avoided with the `SCRUBBER_APPS_LIST` setting. Using this, you
might for instance split your `INSTALLED_APPS` into multiple `SYSTEM_APPS` and `LOCAL_APPS`, then
set `SCRUBBER_APPS_LIST = LOCAL_APPS`, to scrub only your own apps.

Finally just run `./manage.py scrub_data` to **destructively** scrub the registered fields.

### Arguments to the scrub_data command

`--model` Scrub only a single model (format <app_label>.<model_name>)

`--keep-sessions` Will NOT truncate all (by definition critical) session data.

`--remove-fake-data` Will truncate the database table storing preprocessed data for the Faker library.

## Built-In scrubbers

### Empty/Null

The simplest scrubbers: replace the field's content with the empty string or `NULL`, respectively.

```python
class Scrubbers:
    somefield = scrubbers.Empty
    someother = scrubbers.Null
```

These scrubbers have no options.

### Keeper

When running the validation or want to work in strict mode, you maybe want to actively decide to keep certain data
instead of scrubbing them. In this case, you can just define `scrubbers.Keep`.

```python
class Scrubbers:
    non_critical_field = scrubbers.Keep
```

These scrubber doesn't have any options.

### Hash

Simple hashing of content:

```python
class Scrubbers:
    somefield = scrubbers.Hash  # will use the field itself as source
    someotherfield = scrubbers.Hash('somefield')  # can optionally pass a different field name as hashing source
```

Currently, this uses the MD5 hash which is supported in a wide variety of DB engines. Additionally, since security is
not the main objective, a shorter hash length has a lower risk of being longer than whatever field it is supposed to
replace.

### Lorem

Simple scrubber meant to replace `TextField` with a static block of text. Has no options.

```python
class Scrubbers:
    somefield = scrubbers.Lorem
```

### Concat

Wrapper around `django.db.functions.Concat` to enable simple concatenation of scrubbers. This is useful if you want to
ensure a fields uniqueness through composition of, for instance, the `Hash` and `Faker` (see below) scrubbers.

When using different input field types, make sure to explicitly state an `output_field` type.

The following will generate random email addresses by hashing the user-part and using `faker` for the domain part:

```python
class Scrubbers:
    email = scrubbers.Concat(scrubbers.Hash('email'), models.Value('@'), scrubbers.Faker('domain_name'), output_field=models.EmailField())
```

### Faker

Replaces content with the help of [faker](https://pypi.python.org/pypi/Faker).

```python
class Scrubbers:
    first_name = scrubbers.Faker('first_name')
    last_name = scrubbers.Faker('last_name')
    past_date = scrubbers.Faker('past_date', start_date="-30d", tzinfo=None)
```

The replacements are done on the database-level and should therefore be able to cope with large amounts of data with
reasonable performance.

The `Faker` scrubber requires at least one argument: the faker provider used to generate random data.
All [faker providers](https://faker.readthedocs.io/en/latest/providers.html) are supported, and you can also register
your own custom providers.<br />
Any remaining arguments will be passed through to that provider. Please refer to the faker docs if a provider accepts
arguments and what to do with them.

#### Locales

Faker will be initialized with the current django `LANGUAGE_CODE` and will populate the DB with localized data. If you
want localized scrubbing, simply set it to some other value.

#### Idempotency

By default, the faker instance used to populate the DB uses a fixed random seed, in order to ensure different scrubbings
of the same data generate the same output. This is particularly useful if the scrubbed data is imported as a dump by
developers, since changing data during troubleshooting would otherwise be confusing.

This behaviour can be changed by setting `SCRUBBER_RANDOM_SEED=None`, which ensures every scrubbing will generate random
source data.

#### Limitations

Scrubbing unique fields may lead to `IntegrityError`s, since there is no guarantee that the random content will not be
repeated. Playing with different settings for `SCRUBBER_RANDOM_SEED` and `SCRUBBER_ENTRIES_PER_PROVIDER` may alleviate
the problem.
Unfortunately, for performance reasons, the source data for scrubbing with faker is added to the database, and
arbitrarily increasing `SCRUBBER_ENTRIES_PER_PROVIDER` will significantly slow down scrubbing (besides still not
guaranteeing uniqueness).

When using `django < 2.1` and working on `sqlite` a bug within django causes field-specific scrubbing (
e.g. `date_object`) to fail. Please consider using a different database backend or upgrade to the latest django version.

## Scrubbing third-party models

Sometimes you just don't have control over some code, but you still want to scrub the data of a given model.

A good example is the Django user model. It contains sensitive data, and you would have to overwrite the whole model
just to add the scrubber metaclass.

That's the way to go:

1. Define your Scrubber class **somewhere** in your codebase (like a `scrubbers.py`)

```python
# scrubbers.py
class UserScrubbers:
    scrubbers.Faker('de_DE')
    first_name = scrubbers.Faker('first_name')
    last_name = scrubbers.Faker('last_name')
    username = scrubbers.Faker('uuid4')
    password = scrubbers.Faker('sha1')
    last_login = scrubbers.Null
    email = scrubbers.Concat(first_name, models.Value('.'), last_name, models.Value('@'),
                             models.Value(settings.SCRUBBER_DOMAIN))
````

2. Set up a mapping between your third-party model and your scrubber class

```python
# settings.py
SCRUBBER_MAPPING = {
    "auth.User": "apps.account.scrubbers.UserScrubbers",
}
```

## Settings

### `SCRUBBER_GLOBAL_SCRUBBERS`:

Dictionary of global scrubbers. Keys should be either field names as strings or field type classes. Values should be one
of the scrubbers provided in `django_scrubber.scrubbers`.

Example:

```python
SCRUBBER_GLOBAL_SCRUBBERS = {
    'name': scrubbers.Hash,
    EmailField: scrubbers.Hash,
}
```

### `SCRUBBER_RANDOM_SEED`:

The seed used when generating random content by the Faker scrubber. Setting this to `None` means each scrubbing will
generate different data.

(default: `42`)

### `SCRUBBER_ENTRIES_PER_PROVIDER`:

Number of entries to use as source for Faker scrubber. Increasing this value will increase the randomness of generated
data, but decrease performance.

(default: `1000`)

### `SCRUBBER_SKIP_UNMANAGED`:

Do not attempt to scrub models which are not managed by the ORM.

(default: `True`)

### `SCRUBBER_APPS_LIST`:

Only scrub models belonging to these specific django apps. If unset, will scrub all installed apps.

(default: `None`)

### `SCRUBBER_ADDITIONAL_FAKER_PROVIDERS`:

Add additional fake providers to be used by Faker. Must be noted as full dotted path to the provider class.

(default: `{*()}`, empty set)

### `SCRUBBER_FAKER_LOCALE`:

Set an alternative locale for Faker used during the scrubbing process.

(default: `None`, falls back to Django's default locale)

### `SCRUBBER_MAPPING`:

Define a class and a mapper which does not have to live inside the given model. Useful, if you have no control over the
models code you'd like to scrub.

````python
SCRUBBER_MAPPING = {
    "auth.User": "my_app.scrubbers.UserScrubbers",
}
````

(default: `{}`)

### `SCRUBBER_STRICT_MODE`:

When strict mode is activated, you have to define a scrubbing policy for every field of every type defined in
`SCRUBBER_REQUIRED_FIELD_TYPES`. If you have unscrubbed fields and this flag is active, you can't run
`python manage.py scrub_data`.

(default: `False`)

### `SCRUBBER_REQUIRED_FIELD_TYPES`:

Defaults to all text-based Django model fields. Usually, privacy-relevant data is only stored in text-fields, numbers
and booleans (usually) can't contain sensitive personal data. These fields will be checked when running
`python manage.py scrub_validation`.

(default: `(models.CharField, models.TextField, models.URLField, models.JSONField, models.GenericIPAddressField,
           models.EmailField,)`)

### `SCRUBBER_REQUIRED_FIELD_MODEL_WHITELIST`:

Whitelists a list of models which will not be checked during `scrub_validation` and when 
activating the strict mode. Defaults to the non-privacy-related Django base models.
Items can either be full model names (e.g. `auth.Group`) or regular expression patterns matching
against the full model name (e.g. `re.compile(auth.*)` to whitelist all auth models).

(default: `('auth.Group', 'auth.Permission', 'contenttypes.ContentType', 'sessions.Session', 'sites.Site', 
'django_scrubber.FakeData', 'db.TestModel',)`)

(default: {})

## Logging

Scrubber uses the default django logger. The logger name is ``django_scrubber.scrubbers``.
So if you want to log - for example - to the console, you could set up the logger like this:

````
LOGGING['loggers']['django_scrubber'] = {
    'handlers': ['console'],
    'propagate': True,
    'level': 'DEBUG',
}
````

## Making a new release

This project makes use of [RegioHelden's reusable GitHub workflows](https://github.com/RegioHelden/github-reusable-workflows). \
Make a new release by manually triggering the `Open release PR` workflow.
