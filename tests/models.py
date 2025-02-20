from django.db import models
from factory.django import DjangoModelFactory


class DataToBeScrubbed(models.Model):
    first_name = models.CharField(max_length=8)
    last_name = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField()
    ean8 = models.CharField(max_length=13)
    date_past = models.DateField(null=True)
    company = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class DataFactory(DjangoModelFactory):
    class Meta:
        model = DataToBeScrubbed
