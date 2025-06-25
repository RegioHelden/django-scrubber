# Changelog

## [v5.2.0](https://github.com/RegioHelden/django-scrubber/tree/v5.2.0) (2025-06-25)

[Full Changelog](https://github.com/RegioHelden/django-scrubber/compare/v5.1.0...v5.2.0)

**Implemented enhancements:**

- Update github-reusable-workflows to 2.2.3, fix changelog generation [\#109](https://github.com/RegioHelden/django-scrubber/pull/109) (@lociii)
- Add support for non-integer primary keys [\#106](https://github.com/RegioHelden/django-scrubber/pull/106) (@lociii)
- Drop SQLite MD5 workaround [\#105](https://github.com/RegioHelden/django-scrubber/pull/105) (@lociii)

**Merged pull requests:**

- Update uv to 0.7.14 [\#114](https://github.com/RegioHelden/django-scrubber/pull/114) (@regiohelden-dev)
- Update ruff VSCode integration to 2025.24.0 [\#107](https://github.com/RegioHelden/django-scrubber/pull/107) (@regiohelden-dev)
- Update uv to 0.7.13 [\#103](https://github.com/RegioHelden/django-scrubber/pull/103) (@regiohelden-dev)

## [v5.1.0](https://github.com/RegioHelden/django-scrubber/tree/v5.1.0) (2025-06-11)

[Full Changelog](https://github.com/RegioHelden/django-scrubber/compare/v5.0.0...v5.1.0)

**Implemented enhancements:**

- Remove ambiguity around callables and a logical operator [\#101](https://github.com/RegioHelden/django-scrubber/pull/101) (@lociii)
-  Commands should use stdout instead of logging [\#98](https://github.com/RegioHelden/django-scrubber/pull/98) (@lociii)
- Bump django in test dependencies from 5.2 to 5.2.2 [\#95](https://github.com/RegioHelden/django-scrubber/pull/95) (@lociii)

**Fixed bugs:**

- Fix strict mode test [\#100](https://github.com/RegioHelden/django-scrubber/pull/100) (@lociii)

**Merged pull requests:**

- Fix documentation comments on some tests [\#99](https://github.com/RegioHelden/django-scrubber/pull/99) (@lociii)
- Update uv to 0.7.12 [\#96](https://github.com/RegioHelden/django-scrubber/pull/96) (@regiohelden-dev)
- Update uv to 0.7.11 [\#94](https://github.com/RegioHelden/django-scrubber/pull/94) (@regiohelden-dev)

## [v5.0.0](https://github.com/RegioHelden/django-scrubber/tree/v5.0.0) (2025-05-26)

[Full Changelog](https://github.com/RegioHelden/django-scrubber/compare/v4.2.0...v5.0.0)

**Breaking changes:**

- Only fail validation with an non-zero exit code if strict mode is active [\#88](https://github.com/RegioHelden/django-scrubber/pull/88) (@lociii)

**Merged pull requests:**

- Update uv to 0.7.8 [\#91](https://github.com/RegioHelden/django-scrubber/pull/91) (@regiohelden-dev)
- Update uv to 0.7.7 [\#90](https://github.com/RegioHelden/django-scrubber/pull/90) (@regiohelden-dev)
- Update uv to 0.7.6 [\#89](https://github.com/RegioHelden/django-scrubber/pull/89) (@regiohelden-dev)
- Update uv to 0.7.5 [\#87](https://github.com/RegioHelden/django-scrubber/pull/87) (@regiohelden-dev)
- Update uv to 0.7.4 [\#86](https://github.com/RegioHelden/django-scrubber/pull/86) (@regiohelden-dev)
- Update uv to 0.7.3 [\#85](https://github.com/RegioHelden/django-scrubber/pull/85) (@regiohelden-dev)
- Update uv to 0.7.0 [\#84](https://github.com/RegioHelden/django-scrubber/pull/84) (@regiohelden-dev)
- Update github-reusable-workflows to 2.2.1 [\#83](https://github.com/RegioHelden/django-scrubber/pull/83) (@regiohelden-dev)
- Updates from modulesync [\#82](https://github.com/RegioHelden/django-scrubber/pull/82) (@regiohelden-dev)
- Update github-reusable-workflows to 2.2.0 and uv to 0.6.17 [\#81](https://github.com/RegioHelden/django-scrubber/pull/81) (@regiohelden-dev)
- Update github-reusable-workflows to 2.1.1 [\#80](https://github.com/RegioHelden/django-scrubber/pull/80) (@regiohelden-dev)
- Update ruff VSCode integration to 2025.22.0, remove classifiers for unsupported Python versions [\#79](https://github.com/RegioHelden/django-scrubber/pull/79) (@regiohelden-dev)
- Remove dependabot integration, set Python version for GitHub actions [\#77](https://github.com/RegioHelden/django-scrubber/pull/77) (@regiohelden-dev)
- Add supported python versions to sync config [\#76](https://github.com/RegioHelden/django-scrubber/pull/76) (@lociii)
- Make dependabot set a proper label [\#75](https://github.com/RegioHelden/django-scrubber/pull/75) (@regiohelden-dev)
- Bump regiohelden/github-reusable-workflows from 2.0.0 to 2.1.0 [\#74](https://github.com/RegioHelden/django-scrubber/pull/74) (@dependabot[bot])
- Integrate with modulesync [\#73](https://github.com/RegioHelden/django-scrubber/pull/73) (@regiohelden-dev)
- Set python min version for modulesync [\#72](https://github.com/RegioHelden/django-scrubber/pull/72) (@lociii)
- Align test setup with other libraries, prepare for modulesync rollout [\#71](https://github.com/RegioHelden/django-scrubber/pull/71) (@lociii)

## [v4.2.0](https://github.com/RegioHelden/django-scrubber/tree/v4.2.0) (2025-04-11)

[Full Changelog](https://github.com/RegioHelden/django-scrubber/compare/v4.1.0...v4.2.0)

**Implemented enhancements:**

- Add support for django 5.2 [\#65](https://github.com/RegioHelden/django-scrubber/pull/65) (@lociii)
- Switch to reusable github workflows [\#63](https://github.com/RegioHelden/django-scrubber/pull/63) (@lociii)

## [4.1.0] - 2025-03-04

**Fixed bugs:**

- Restore output in `scrub_validation` command
- Move back to annotation, instead of Subquery for performance reasons

## [4.0.0] - 2025-02-19

**Breaking changes:**

- Removed support for Python 3.8

**Implemented enhancements:**

- Added support for Python 3.13 - Thanks @GitRon
- Improved documentation on concatenation of different field types
- Removed outdated sqlite workaround
- Switch linting and formatting to ruff
- Add devcontainer setup for VSCode
- Updates to GitHub actions

## [3.0.0] - 2024-09-10

**Breaking changes:**

- Removed `SCRUBBER_VALIDATION_WHITELIST` in favour of `SCRUBBER_REQUIRED_FIELD_MODEL_WHITELIST` - Thanks @GitRon

**Implemented enhancements:**

- Added Django test model `db.TestModel` to default whitelist of `SCRUBBER_REQUIRED_FIELD_MODEL_WHITELIST` - Thanks @GitRon
- Removed support for the `mock` package in unit tests
- Adjusted some default settings

## [2.1.1] - 2024-08-20

**Fixed bugs:**

- Fixed an issue where the management command `scrub_validation` could fail even though all models were skipped - Thanks @GitRon

## [2.1.0] - 2024-08-20

**Implemented enhancements:**

- Added support for `Django` version `5.1` - Thanks @GitRon
- Added `SCRUBBER_VALIDATION_WHITELIST` and excluded Django core test model - Thanks @GitRon

## [2.0.0] - 2024-06-27

**Breaking changes:**

- Remove support for `Django` below version `4.2`
- Remove support for `Python` below version `3.8`
- Minimum required `Faker` version is now `20.0.0`, released 11/2023

**Implemented enhancements:**

- Added support for `Django` version `5.0`
- Added support for `Python` version `3.12`
- Add docker compose setup to run tests

## [1.3.0] - 2024-06-05

**Implemented enhancements:**

- Add support for regular expressions in `SCRUBBER_REQUIRED_FIELD_MODEL_WHITELIST` - Thanks @fbinz

## [1.2.2] - 2023-11-04

**Implemented enhancements:**

- Set `default_auto_field` for `django-scrubber` to `django.db.models.AutoField` to prevent overrides from Django settings - Thanks @GitRon

## [1.2.1] - 2023-11-03

- Yanked

## [1.2.0] - 2023-04-01

**Implemented enhancements:**

- Added scrubber validation - Thanks @GitRon
- Added strict mode - Thanks @GitRon

## [1.1.0] - 2022-07-11

**Implemented enhancements:**

- Invalid fields on scrubbers will no longer raise exception but just trigger warnings now
- Author list completed

## [1.0.0] - 2022-07-11

**Implemented enhancements:**

- Meta data for python package improved - Thanks @GitRon

## [0.9.0] - 2022-06-27

**Implemented enhancements:**

- Add functionality to scrub third party models like the Django user model, see https://github.com/RegioHelden/django-scrubber#scrubbing-third-party-models - Thanks @GitRon
- Add tests for Python 3.10 - Thanks @costela

## [0.8.0] - 2022-05-01

**Implemented enhancements:**

- Add `keep-sessions` argument to scrub_data command. Will NOT truncate all (by definition critical) session data. Thanks @GitRon
- Add `remove-fake-data` argument to scrub_data command. Will truncate the database table storing preprocessed data for the Faker library. Thanks @GitRon
- Add Django 3.2 and 4.0 to test matrix

**Breaking changes:**

- Remove Python 3.6 from test matrix
- Remove Django 2.2 and 3.1 from test matrix

## [0.7.0] - 2022-02-24

**Implemented enhancements:**

- Remove upper boundary for Faker as they release non-breaking major upgrades way too often, please pin a working release in your own app

## [0.6.2] - 2022-02-08

**Implemented enhancements:**

- Support faker 12.x

## [0.6.1] - 2022-01-25

**Implemented enhancements:**

- Support faker 11.x

## [0.6.0] - 2021-10-18

**Implemented enhancements:**

- Add support to override Faker locale in scrubber settings
- Publish coverage only on main repository

## [0.5.6] - 2021-10-08

**Implemented enhancements:**

- Pin psycopg2 in CI to 2.8.6 as 2.9+ is incompatible with Django 2.2

## [0.5.5] - 2021-10-08

**Implemented enhancements:**

- Support faker 9.x

## [0.5.4] - 2021-04-13

**Implemented enhancements:**

- Support faker 8.x

## [0.5.3] - 2021-02-04

**Implemented enhancements:**

- Support faker 6.x

## [0.5.2] - 2021-01-12

**Implemented enhancements:**

- Add tests for Python 3.9
- Add tests for Django 3.1
- Support faker 5.x
- Update dev package requirements 

## [0.5.1] - 2020-10-16

**Implemented enhancements:**

- Fix travis setup

## [0.5.0] - 2020-10-16

**Implemented enhancements:**

- Support for django-model-utils 4.x.x

**Breaking changes:**

- Add compatibility for Faker 3.x.x, remove support for Faker < 0.8.0
- Remove support for Python 2.7 and 3.5
- Remove support for Django 1.x

## [0.4.4] - 2019-12-11

**Implemented enhancements:**

- add the same version restrictions on faker to setup.py

## [0.4.3] - 2019-12-04

**Implemented enhancements:**

- add empty and null scrubbers
- make `Lorem` scrubber lazy, matching README

**Fixed bugs:**

- set more stringent version requirements (faker >= 3 breaks builds)

## [0.4.1] - 2019-11-16

**Fixed bugs:**

- correctly clear fake data model to fix successive calls to `scrub_data` (thanks [Benedikt Bauer](https://github.com/mastacheata))

## [0.4.0] - 2019-11-13

**Implemented enhancements:**

- `Faker` scrubber now supports passing arbitrary arguments to faker providers and also non-text fields (thanks [Benedikt Bauer](https://github.com/mastacheata) and [Ronny Vedrilla](https://github.com/GitRon))

## [0.3.1] - 2018-09-10

**Fixed bugs:**

- [#9](https://github.com/RegioHelden/django-scrubber/pull/9) `Hash` scrubber choking on fields with `max_length=None` - Thanks to [Charlie Denton](https://github.com/meshy)

## [0.3.0] - 2018-09-06

**Implemented enhancements:**

- Finally added some basic tests (thanks [Marco De Felice](https://github.com/md-f))
- `Hash` scrubber can now also be used on sqlite
- Expand tests to include python 3.7 and django 2.1

**Breaking changes:**

- Scrubbers that are lazily initialized now receive `Field` instances as parameters, instead of field
  names. If you have custom scrubbers depending on the previous behavior, these should be updated. Accessing the
  field's name from the object instance is trivial: `field_instance.name`. E.g.: if you have `some_field = MyCustomScrubber`
  in any of your models' `Scrubbers`, this class must accept a `Field` instance as first parameter.
  Note that explicitly intializing any of the built-in scrubbers with field names is still supported, so if you were
  just using built-in scrubbers, you should not be affected by this change.
- related to the above, `FuncField` derived classes can now do connection-based setup by implementing the
  `connection_setup` method. This is mostly useful for doing different things based on the DB vendor, and is used to
  implement `MD5()` on sqlite (see added feature above)
- Ignore proxy models when scrubbing (thanks [Marco De Felice](https://github.com/md-f))

## [0.2.1] - 2018-08-14

**Implemented enhancements:**

- Option to scrub only one model from the management command
- Support loading additional faker providers by config setting SCRUBBER\_ADDITIONAL\_FAKER\_PROVIDERS
- Switched changelog format to the one proposed on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

## [0.2.0] - 2018-08-13

**Implemented enhancements:**

- scrubbers.Concat to make simple concatenation of scrubbers possible

## [0.1.4] - 2018-08-13

**Implemented enhancements:**

- Make our README look beautiful on PyPI

## [0.1.3] - 2018-08-13

**Fixed bugs:**

- [#1](https://github.com/RegioHelden/django-scrubber/pull/1) badly timed import - Thanks to [Charlie Denton](https://github.com/meshy)

## [0.1.2] - 2018-06-22

**Implemented enhancements:**

- Use bumpversion and travis to make new releases

**Breaking changes:**

- rename project: django\_scrubber → django-scrubber

## [0.1.0] - 2018-06-22

**Implemented enhancements:**

- Initial release


