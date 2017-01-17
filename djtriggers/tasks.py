from celery import shared_task

from .models import Trigger


@shared_task
def process_triggers():
    from . import logic
    logic.process_triggers()


@shared_task
def clean_triggers():
    from . import logic
    logic.clean_triggers()


@shared_task
def process_trigger(trigger_id, *args, **kwargs):
    return Trigger.objects.get(id=trigger_id).process(*args, **kwargs)
