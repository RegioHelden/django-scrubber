from django.db import models

from factory.django import DjangoModelFactory


class DataToBeScrubbed(models.Model):
    first_name = models.CharField(max_length=8)
    description = models.TextField()


class DataFactory(DjangoModelFactory):
    class Meta:
        model = DataToBeScrubbed
