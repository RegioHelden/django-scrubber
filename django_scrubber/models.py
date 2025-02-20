from typing import ClassVar

from django.db.models import CharField, Count, Index, Manager, Model, PositiveSmallIntegerField


class FakeDataManager(Manager):
    def provider_count(self, provider):
        return self.filter(provider=provider).values("provider").annotate(count=Count("provider")).values("count")


class FakeData(Model):
    provider = CharField(max_length=255, verbose_name="Faker provider", db_index=True)
    provider_offset = PositiveSmallIntegerField()
    content = CharField(max_length=255, verbose_name="Fake content")

    objects = FakeDataManager()

    class Meta:
        indexes: ClassVar[list[Index]] = [
            Index(fields=["provider", "provider_offset"]),
        ]
        unique_together = (("provider", "provider_offset"),)

    def __str__(self):
        return f"{self.provider}: '{self.content}'"
