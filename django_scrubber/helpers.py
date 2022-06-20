from django_scrubber.management.commands.scrub_data import _handle_model_scrubbing


def scrub_model_with_scrubber(model, scrubber_cls) -> None:
    """
    Tries to scrub the given class with the given scrubber.
    Useful, if you don't have access to the models code and therefore can't add a scrubber class.
    :param model: Django Model class
    :param scrubber_cls: Scrubber meta class
    :return: None
    """
    _handle_model_scrubbing(model=model, scrubbers=dict(), scrubber_cls=scrubber_cls)
