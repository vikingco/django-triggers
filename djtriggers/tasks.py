from celery import shared_task
from celery.utils.log import get_task_logger

from . import logic


logger = get_task_logger(__name__)


@shared_task
def process_triggers():
    logic.process_triggers(use_statd=True, function_logger=logger)


@shared_task
def clean_triggers():
    logic.clean_triggers()
