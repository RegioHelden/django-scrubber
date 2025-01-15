#!/usr/bin/env python
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version(*file_paths):
    """Retrieves the version from django_scrubber/__init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


version = get_version("django_scrubber", "__init__.py")


if sys.argv[-1] == 'publish':
    try:
        import wheel
        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.md').read()
history = open('CHANGELOG.md').read()

setup(
    name='django-scrubber',
    version=version,
    description="""Data Anonymizer for Django""",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown',
    author='RegioHelden GmbH',
    author_email='entwicklung@regiohelden.de',
    url='https://github.com/regiohelden/django-scrubber',
    project_urls={
        'Documentation': 'https://github.com/RegioHelden/django-scrubber/blob/master/README.md',
        'Maintained by': 'https://github.com/RegioHelden/django-scrubber/blob/master/AUTHORS.md',
        'Bugtracker': 'https://github.com/RegioHelden/django-scrubber/issues',
        'Changelog': 'https://github.com/RegioHelden/django-scrubber/blob/master/CHANGELOG.md',
    },
    packages=[
        'django_scrubber',
    ],
    include_package_data=True,
    install_requires=[
        "faker>=20.0.0",
    ],
    license="BSD",
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Framework :: Django :: 5.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Security',
        'Topic :: Software Development',
    ],
)
