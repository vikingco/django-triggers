from celery import shared_task

from . import logic


@shared_task
def process_triggers():
    logic.process_triggers()


@shared_task
def clean_triggers():
    logic.clean_triggers()
