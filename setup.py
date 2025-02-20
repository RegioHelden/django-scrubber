#!/usr/bin/env python
import re
from pathlib import Path

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version():
    """Retrieves the version from django_scrubber/__init__.py"""
    with Path("django_scrubber/__init__.py").open("r") as f:
        version_file = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


version = get_version()

with Path("README.md").open(mode="r") as f:
    readme = f.read()
with Path("CHANGELOG.md").open(mode="r") as f:
    changelog = f.read()

setup(
    name="django-scrubber",
    version=version,
    description="""Data Anonymizer for Django""",
    long_description=readme + "\n\n" + changelog,
    long_description_content_type="text/markdown",
    author="RegioHelden GmbH",
    author_email="entwicklung@regiohelden.de",
    url="https://github.com/regiohelden/django-scrubber",
    project_urls={
        "Documentation": "https://github.com/RegioHelden/django-scrubber/blob/master/README.md",
        "Maintained by": "https://github.com/RegioHelden/django-scrubber/blob/master/AUTHORS.md",
        "Bugtracker": "https://github.com/RegioHelden/django-scrubber/issues",
        "Changelog": "https://github.com/RegioHelden/django-scrubber/blob/master/CHANGELOG.md",
    },
    packages=[
        "django_scrubber",
    ],
    include_package_data=True,
    install_requires=[
        "faker>=20.0.0",
    ],
    license="BSD",
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Security",
        "Topic :: Software Development",
    ],
)
