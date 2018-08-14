# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Nothing

## [0.2.1] - 2018-08-14
### Added
- Option to scrub only one model from the management command
- Support loading additional faker providers by config setting SCRUBBER_ADDITIONAL_FAKER_PROVIDERS

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
