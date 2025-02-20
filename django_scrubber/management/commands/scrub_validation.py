import sys

from django.core.management.base import BaseCommand

from django_scrubber.services.validator import ScrubberValidatorService


class Command(BaseCommand):
    def handle(self, *args, **options):
        service = ScrubberValidatorService()
        non_scrubbed_field_list = service.process()

        found_models = 0
        found_fields = 0

        if len(non_scrubbed_field_list):
            for model_path, affected_field_list in non_scrubbed_field_list.items():
                found_models += 1
                for _field in affected_field_list:
                    found_fields += 1

            if found_models > 0:
                sys.exit(1)
