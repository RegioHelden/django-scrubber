from __future__ import absolute_import

import factory

from django.contrib.auth.models import User


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'user{0}'.format(n))
    first_name = factory.Sequence(lambda n: 'John {0}'.format(n))
    last_name = factory.Sequence(lambda n: 'Doe {0}'.format(n))
    email = factory.Sequence(lambda n: 'user{0}@example.com'.format(n))
    password = factory.PostGenerationMethodCall('set_password', 'asdf1234')

    class Meta:
        model = User
        abstract = False
