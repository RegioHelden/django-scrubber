# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!--
## [Unreleased]
### Breaking
- Nothing
### Changed
- Nothing
-->

## [4.1.0] - 2025-03-04
### Changed
- Restore output in `scrub_validation` command
- Move back to annotation, instead of Subquery for performance reasons

## [4.0.0] - 2025-02-19
### Breaking
- Removed support for Python 3.8
### Changed
- Added support for Python 3.13 - Thanks @GitRon
- Improved documentation on concatenation of different field types
- Removed outdated sqlite workaround
### Organizational changes
- Switch linting and formatting to ruff
- Add devcontainer setup for VSCode
- Updates to GitHub actions

## [3.0.0] - 2024-09-10
### Breaking
- Removed `SCRUBBER_VALIDATION_WHITELIST` in favour of `SCRUBBER_REQUIRED_FIELD_MODEL_WHITELIST` - Thanks @GitRon
### Changed
- Added Django test model `db.TestModel` to default whitelist of `SCRUBBER_REQUIRED_FIELD_MODEL_WHITELIST` - Thanks @GitRon
- Removed support for the `mock` package in unit tests
- Adjusted some default settings

## [2.1.1] - 2024-08-20
### Changed
- Fixed an issue where the management command `scrub_validation` could fail even though all models were skipped - Thanks @GitRon

## [2.1.0] - 2024-08-20
### Changed
- Added support for `Django` version `5.1` - Thanks @GitRon
- Added `SCRUBBER_VALIDATION_WHITELIST` and excluded Django core test model - Thanks @GitRon

## [2.0.0] - 2024-06-27
### Changed
- **BREAKING**: Remove support for `Django` below version `4.2`
- **BREAKING**: Remove support for `Python` below version `3.8`
- **BREAKING**: Minimum required `Faker` version is now `20.0.0`, released 11/2023
- Added support for `Django` version `5.0`
- Added support for `Python` version `3.12`
- Add docker compose setup to run tests

## [1.3.0] - 2024-06-05
### Added
- Add support for regular expressions in `SCRUBBER_REQUIRED_FIELD_MODEL_WHITELIST` - Thanks @fbinz

## [1.2.2] - 2023-11-04
### Changed
- Set `default_auto_field` for `django-scrubber` to `django.db.models.AutoField` to prevent overrides from Django settings - Thanks @GitRon

## [1.2.1] - 2023-11-03
### Invalid

## [1.2.0] - 2023-04-01
### Changed
- Added scrubber validation - Thanks @GitRon
- Added strict mode - Thanks @GitRon

## [1.1.0] - 2022-07-11
### Changed
- Invalid fields on scrubbers will no longer raise exception but just trigger warnings now
- Author list completed

## [1.0.0] - 2022-07-11
### Changed
- Meta data for python package improved - Thanks @GitRon

## [0.9.0] - 2022-06-27
### Added
- Add functionality to scrub third party models like the Django user model, see https://github.com/RegioHelden/django-scrubber#scrubbing-third-party-models - Thanks @GitRon
- Add tests for Python 3.10 - Thanks @costela

## [0.8.0] - 2022-05-01
### Added
- Add `keep-sessions` argument to scrub_data command. Will NOT truncate all (by definition critical) session data. Thanks @GitRon
- Add `remove-fake-data` argument to scrub_data command. Will truncate the database table storing preprocessed data for the Faker library. Thanks @GitRon
- Add Django 3.2 and 4.0 to test matrix
### Changed
- Remove Python 3.6 from test matrix
- Remove Django 2.2 and 3.1 from test matrix

## [0.7.0] - 2022-02-24
### Changed
- Remove upper boundary for Faker as they release non-breaking major upgrades way too often, please pin a working release in your own app

## [0.6.2] - 2022-02-08
### Changed
- Support faker 12.x

## [0.6.1] - 2022-01-25
### Changed
- Support faker 11.x

## [0.6.0] - 2021-10-18
### Added
- Add support to override Faker locale in scrubber settings
### Changed
- Publish coverage only on main repository

## [0.5.6] - 2021-10-08
### Changed
- Pin psycopg2 in CI ti 2.8.6 as 2.9+ is incompatible with Django 2.2

## [0.5.5] - 2021-10-08
### Changed
- Support faker 9.x

## [0.5.4] - 2021-04-13
### Changed
- Support faker 8.x

## [0.5.3] - 2021-02-04
### Changed
- Support faker 6.x

## [0.5.2] - 2021-01-12
### Changed
- Add tests for Python 3.9
- Add tests for Django 3.1
- Support faker 5.x
- Update dev package requirements 

## [0.5.1] - 2020-10-16
### Changed
- Fix travis setup

## [0.5.0] - 2020-10-16
### Added
- Support for django-model-utils 4.x.x
### Changed
- Add compatibility for Faker 3.x.x, remove support for Faker < 0.8.0
- Remove support for Python 2.7 and 3.5
- Remove support for Django 1.x

## [0.4.4] - 2019-12-11
### Fixed
- add the same version restrictions on faker to setup.py

## [0.4.3] - 2019-12-04
### Added
- add empty and null scrubbers

### Changed
- make `Lorem` scrubber lazy, matching README

### Fixed
- set more stringent version requirements (faker >= 3 breaks builds)

## [0.4.1] - 2019-11-16
### Fixed
- correctly clear fake data model to fix successive calls to `scrub_data` (thanks [Benedikt Bauer](https://github.com/mastacheata))

## [0.4.0] - 2019-11-13
### Added
- `Faker` scrubber now supports passing arbitrary arguments to faker providers and also non-text fields (thanks [Benedikt Bauer](https://github.com/mastacheata) and [Ronny Vedrilla](https://github.com/GitRon))

## [0.3.1] - 2018-09-10
### Fixed
- [#9](https://github.com/RegioHelden/django-scrubber/pull/9) `Hash` scrubber choking on fields with `max_length=None` - Thanks to [Charlie Denton](https://github.com/meshy)

## [0.3.0] - 2018-09-06
### Added
- Finally added some basic tests (thanks [Marco De Felice](https://github.com/md-f))
- `Hash` scrubber can now also be used on sqlite

### Changed
- **BREAKING**: scrubbers that are lazily initialized now receive `Field` instances as parameters, instead of field
  names. If you have custom scrubbers depending on the previous behavior, these should be updated. Accessing the
  field's name from the object instance is trivial: `field_instance.name`. E.g.: if you have `some_field = MyCustomScrubber`
  in any of your models' `Scrubbers`, this class must accept a `Field` instance as first parameter.
  Note that explicitly intializing any of the built-in scrubbers with field names is still supported, so if you were
  just using built-in scrubbers, you should not be affected by this change.
- related to the above, `FuncField` derived classes can now do connection-based setup by implementing the
  `connection_setup` method. This is mostly useful for doing different things based on the DB vendor, and is used to
  implement `MD5()` on sqlite (see added feature above)
- Ignore proxy models when scrubbing (thanks [Marco De Felice](https://github.com/md-f))
- Expand tests to include python 3.7 and django 2.1

## [0.2.1] - 2018-08-14
### Added
- Option to scrub only one model from the management command
- Support loading additional faker providers by config setting SCRUBBER\_ADDITIONAL\_FAKER\_PROVIDERS

### Changed
- Switched changelog format to the one proposed on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

## [0.2.0] - 2018-08-13
### Added
- scrubbers.Concat to make simple concatenation of scrubbers possible

## [0.1.4] - 2018-08-13
### Changed
- Make our README look beautiful on PyPI

## [0.1.3] - 2018-08-13
### Fixed
- [#1](https://github.com/RegioHelden/django-scrubber/pull/1) badly timed import - Thanks to [Charlie Denton](https://github.com/meshy)

## [0.1.2] - 2018-06-22
### Changed
- Use bumpversion and travis to make new releases
- rename project: django\_scrubber → django-scrubber

## [0.1.0] - 2018-06-22
### Added
- Initial release
