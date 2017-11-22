from django.dispatch import receiver
from django.core.signals import got_request_exception
import logging


logger = logging.getLogger(__name__)


@receiver(got_request_exception)
def got_request_exception_signal(sender, **kwargs):
    logger.error(sender)
    logger.error(kwargs)
