from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoScrubberConfig(AppConfig):
    name = "django_scrubber"
    verbose_name = _("Django Scrubber")
    default_auto_field = "django.db.models.AutoField"
