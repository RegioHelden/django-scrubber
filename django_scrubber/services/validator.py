import re
from typing import Union

from django.apps import apps

from django_scrubber import settings_with_fallback


class ScrubberValidatorService:
    """
    Service to validate if all text-based fields are being scrubbed within your project and dependencies.
    """

    @staticmethod
    def check_pattern(pattern: Union[str, re.Pattern], value):
        if isinstance(pattern, str):
            return pattern == value
        if isinstance(pattern, re.Pattern):
            return pattern.fullmatch(value)
        raise ValueError("Invalid pattern type")

    def process(self) -> dict:
        from django_scrubber.management.commands.scrub_data import _get_model_scrubbers

        scrubber_required_field_types = settings_with_fallback("SCRUBBER_REQUIRED_FIELD_TYPES")
        model_whitelist = settings_with_fallback("SCRUBBER_REQUIRED_FIELD_MODEL_WHITELIST")

        # Get a list of all registered models in your Django application
        model_list = apps.get_models()

        # Create a dictionary to store the fields of each model
        non_scrubbed_field_list = {}

        # Iterate over each model in the list
        for model in model_list:
            # Check if model is whitelisted
            if any(self.check_pattern(pattern, model._meta.label) for pattern in model_whitelist):
                continue

            fields_need_scrubbing = []
            # Get the model's name and fields
            fields = model._meta.get_fields()

            # Gather list of all fields of the given model that require scrubbing
            for field in fields:
                if type(field) in scrubber_required_field_types:
                    fields_need_scrubbing.append(field.name)

            # Get scrubber class
            scrubber_class = _get_model_scrubbers(model)

            # If we did find a scrubber class...
            if scrubber_class:
                # We check for every scrubbing requiring field, if it's set to be scrubbed
                for scrubbed_field in scrubber_class:
                    if scrubbed_field.name in fields_need_scrubbing:
                        fields_need_scrubbing.remove(scrubbed_field.name)

            # Store per model all non-scrubbed but scrubbing requiring fields
            if len(fields_need_scrubbing) > 0:
                non_scrubbed_field_list[model._meta.label] = fields_need_scrubbing

        return non_scrubbed_field_list
