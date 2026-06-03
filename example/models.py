from django.db import connection, models
from factory.django import DjangoModelFactory


class DataToBeScrubbed(models.Model):
    first_name = models.CharField(max_length=8)
    last_name = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(null=True)  # noqa: DJ001
    ean8 = models.CharField(max_length=13)
    date_past = models.DateField(null=True)
    company = models.CharField(max_length=255)

    if connection.vendor == "postgresql":
        from django.contrib.postgres.fields import ArrayField  # noqa: PLC0415

        tags = ArrayField(models.CharField(max_length=100), null=True, blank=True)
        int_tags = ArrayField(models.IntegerField(), null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class DataFactory(DjangoModelFactory):
    class Meta:
        model = DataToBeScrubbed
