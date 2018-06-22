# Django Scrubber

[![Build Status](https://travis-ci.org/RegioHelden/django-scrubber.svg?branch=master)](https://travis-ci.org/RegioHelden/django-scrubber)

`django_scrubber` is a django app meant to help you anonymize your project's database data. It destructively alters data directly on the DB and therefore **should not be used on production**.

The main use case is providing developers with realistic data to use during development, without having to distribute your customers' or users' potentially sensitive information.
To accomplish this, `django_scrubber` should be plugged in a step during the creation of your database dumps.

Simply mark the fields you want to anonymize and call the `scrub_data` management command. Data will be replaced based on different *scrubbers* (see below), which define how the anonymous content will be generated.

## Installation

Simply run:
```
pip install django-scrubber
```

And add `django_scrubber` to your django `INSTALLED_APPS`. I.e.: in `settings.py` add:
```
INSTALLED_APPS = [
  ...
  'django_scrubber',
  ...
]
```

## Selecting data to scrub

There are a few different ways to select which data should be scrubbed, namely: explicitly per model field; or globally per name or field type.

Adding scrubbers directly to model:
```python
class MyModel(Model):
    somefield = CharField()

    class Scrubbers:
      somefield = scrubbers.Hash('somefield')
```

Adding scrubber globally, either by field name or field type:

```python
# (in settings.py)

SCRUBBER_GLOBAL_SCRUBBERS = {
    'name': scrubbers.Hash,
    EmailField: scrubbers.Hash,
}
```

Model scrubbers override field-name scrubbers, which in turn override field-type scrubbers.

To disable global scrubbing in a specific model, simply set the field scrubber to `None`.

By default, `django_scrubber` will affect all registered apps. This may lead to issues with third-party apps if the global scrubbers are too general. This can be avoided with the `SCRUBBER_APPS_LIST` setting. Using this, you might for instance split your `INSTALLED_APPS` into multiple `SYSTEM_APPS` and `LOCAL_APPS`, then set `SCRUBBER_APPS_LIST = LOCAL_APPS`, to scrub only your own apps.

Finally just run `./manage.py scrub_data` to **destructively** scrub the registered fields.

## Built-In scrubbers

### Hash

Simple hashing of content:
```python
class Scrubbers:
  somefield = scrubbers.Hash  # will use the field itself as source
  someotherfield = scrubbers.Hash('somefield')  # can optionally pass a different field name as hashing source
```

Currently this uses the MD5 hash which is supported in a wide variety of DB engines. Additionally, since security is not the main objective, a shorter hash length has a lower risk of being longer than whatever field it is supposed to replace.

### Lorem

Simple scrubber meant to replace `TextField` with a static block of text. Has no options.
```python
class Scrubbers:
  somefield = scrubbers.Lorem
```

### Faker

Replaces content with the help of [faker](https://pypi.python.org/pypi/Faker).

```python
class Scrubbers:
  first_name = scrubbers.Faker('first_name')
  last_name = scrubbers.Faker('last_name')
```

The replacements are done on the database-level and should therefore be able to cope with large amounts of data with reasonable performance.

Any [faker providers](https://faker.readthedocs.io/en/latest/providers.html) are supported and you can also register your own custom providers.

#### Locales

Faker will be initialized with the current django `LANGUAGE_CODE` and will populate the DB with localized data. If you want localized scrubbing, simply set it to some other value.

#### Idempotency

By default, the faker instance used to populate the DB uses a fixed random seed, in order to ensure different scrubbings of the same data generate the same output. This is particularly useful if the scrubbed data is imported as a dump by developers, since changing data during troubleshooting would otherwise be confusing.

This behaviour can be changed by setting `SCRUBBER_RANDOM_SEED=None`, which ensures every scrubbing will generate random source data.

#### Limitations

Scrubbing unique fields may lead to `IntegrityError`s, since there is no guarantee that the random content will not be repeated. Playing with different settings for `SCRUBBER_RANDOM_SEED` and `SCRUBBER_ENTRIES_PER_PROVIDER` may alleviate the problem.
Unfortunately, for performance reasons, the source data for scrubbing with faker is added to the database, and arbitrarily increasing `SCRUBBER_ENTRIES_PER_PROVIDER` will significantly slow down scrubbing (besides still not guaranteeing uniqueness).

## Settings

### `SCRUBBER_GLOBAL_SCRUBBERS`:
Dictionary of global scrubbers. Keys should be either field names as strings or field type classes. Values should be one of the scrubbers provided in `django_scrubber.scrubbers`. 

Alternatively, values may be anything that can be used as a value in a `QuerySet.update()` call (like a `Func`), or a `callable` that returns such an object when called with a field name as argument.

Example:
```python
SCRUBBER_GLOBAL_SCRUBBERS = {
    'name': scrubbers.Hash,
    EmailField: scrubbers.Hash,
}
```

### `SCRUBBER_RANDOM_SEED`:
The seed used when generating random content by the Faker scrubber. Setting this to `None` means each scrubbing will generate different data.

(default: 42)

### `SCRUBBER_ENTRIES_PER_PROVIDER`:
Number of entries to use as source for Faker scrubber. Increasing this value will increase the randomness of generated data, but decrease performance. 

(default: 1000)

### `SCRUBBER_SKIP_UNMANAGED`:
Do not attempt to scrub models which are not managed by the ORM.

(default: True)

### `SCRUBBER_APPS_LIST`:
Only scrub models belonging to these specific django apps. If unset, will scrub all installed apps.

(default: None)
