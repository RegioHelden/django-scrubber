from django.db import models

from factory.django import DjangoModelFactory


class DataToBeScrubbed(models.Model):
    first_name = models.CharField(max_length=8)
    last_name = models.CharField(max_length=255, null=True)
    description = models.TextField()
    ean8 = models.CharField(max_length=13)
    date_past = models.DateField(null=True)
    company = models.CharField(max_length=255)


class DataFactory(DjangoModelFactory):
    class Meta:
        model = DataToBeScrubbed


class OtherDatabaseDataFactory(DjangoModelFactory):
    class Meta:
        model = DataToBeScrubbed
        database = 'other'
