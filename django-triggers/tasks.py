from celery import shared_task
from celery.utils.log import get_task_logger

from django.apps import apps

from .models import Trigger


logger = get_task_logger(__name__)


@shared_task
def process_triggers():
    from .logic import process_triggers as process
    process()


@shared_task
def clean_triggers():
    from .logic import clean_triggers as clean
    clean()


@shared_task
def process_trigger(trigger_id, trigger_app_label, trigger_class, *args, **kwargs):
    try:
        apps.get_model(trigger_app_label, trigger_class).objects.get(id=trigger_id).process(*args, **kwargs)
    except Trigger.DoesNotExist:
        pass
