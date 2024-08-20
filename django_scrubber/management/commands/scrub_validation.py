import sys

from django.core.management.base import BaseCommand

from django_scrubber import settings_with_fallback
from django_scrubber.services.validator import ScrubberValidatorService


class Command(BaseCommand):

    def handle(self, *args, **options):
        service = ScrubberValidatorService()
        non_scrubbed_field_list = service.process()

        found_models = 0
        found_fields = 0

        whitelisted_models = settings_with_fallback('SCRUBBER_VALIDATION_WHITELIST')

        if len(non_scrubbed_field_list):
            for model_path, affected_field_list in non_scrubbed_field_list.items():

                if model_path in whitelisted_models:
                    print(f'Model {model_path!r} was excluded via \'SCRUBBER_VALIDATION_WHITELIST\' and will '
                          'not be validated.')
                    continue

                print(f'Model {model_path!r}:')
                found_models += 1
                for field in affected_field_list:
                    print(f"- {field}")
                    found_fields += 1

            print(f'{found_models} model(s) having {found_fields} unscrubbed field(s) detected.')
            sys.exit(1)

        print('No unscrubbed fields detected. Yeah!')
