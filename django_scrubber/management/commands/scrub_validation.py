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

        if len(non_scrubbed_field_list):
            for model_path, affected_field_list in non_scrubbed_field_list.items():
                self.stdout.write(f"Model {model_path!r}:")

                found_models += 1
                for _field in affected_field_list:
                    self.stdout.write(f"- {_field}")
                    found_fields += 1

            self.stdout.write("")

            if found_models > 0:
                self.stdout.write(f"{found_models} model(s) having {found_fields} unscrubbed field(s) detected.")

                # strict mode should fail with a non-zero exit code
                if settings_with_fallback("SCRUBBER_STRICT_MODE"):
                    sys.exit(1)

                self.stdout.write("However strict mode is deactivated and scrubbing is not enforced.")
                sys.exit(0)

        self.stdout.write("No unscrubbed fields detected. Yeah!")
