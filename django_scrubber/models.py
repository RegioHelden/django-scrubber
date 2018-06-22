from django.db.models import Model, CharField, PositiveSmallIntegerField, Index, Manager, Count


class FakeDataManager(Manager):
    def provider_count(self, provider):
        return self.filter(provider=provider).values('provider').annotate(count=Count('provider')).values('count')


class FakeData(Model):
    objects = FakeDataManager()

    provider = CharField(max_length=255, verbose_name="Faker provider", db_index=True)
    provider_offset = PositiveSmallIntegerField()
    content = CharField(max_length=255, verbose_name="Fake content")

    class Meta(object):
        indexes = [
            Index(fields=['provider', 'provider_offset']),
        ]
        unique_together = (('provider', 'provider_offset'),)

    def __str__(self):
        return u"{0}: '{1}'".format(self.provider, self.content)
