from inspect import isabstract
from logging import getLogger

from dateutil.relativedelta import relativedelta

from django.apps import apps
from django.conf import settings
from django.db import connections
from django.db.models import Q
from django.utils import timezone

from .models import Trigger
from .exceptions import ProcessError, ProcessLaterError
from .tasks import process_trigger


logger = getLogger(__name__)


def process_triggers(use_statsd=False, function_logger=None):
    """
    Process all triggers that are ready for processing.

    :param bool use_statsd: whether to use_statsd
    :return: None
    """
    process_async = getattr(settings, 'DJTRIGGERS_ASYNC_HANDLING', False)

    # Get all triggers that need to be processed
    for model in apps.get_models():
        # Check whether it's a trigger
        if not issubclass(model, Trigger) or getattr(model, 'typed', None) is None or isabstract(model):
            continue

        # Get all triggers of this type that need to be processed
        triggers = model.objects.filter(Q(process_after__isnull=True) | Q(process_after__lt=timezone.now()),
                                        date_processed__isnull=True)

        # Process each trigger
        for trigger in triggers:
            try:
                # Process the trigger, either synchronously or in a Celery task
                if process_async:
                    process_trigger.apply_async((trigger.id, trigger._meta.app_label, trigger.__class__.__name__),
                                                {'use_statsd': use_statsd},
                                                max_retries=getattr(settings, 'DJTRIGGERS_CELERY_TASK_MAX_RETRIES', 0))
                else:
                    trigger.process()

                # Send stats to statsd if necessary
                if use_statsd:
                    from django_statsd.clients import statsd
                    statsd.incr('triggers.{}.processed'.format(trigger.trigger_type))
                    if trigger.date_processed and trigger.process_after:
                        statsd.timing('triggers.{}.process_delay_seconds'.format(trigger.trigger_type),
                                      (trigger.date_processed - trigger.process_after).total_seconds())
            # The trigger didn't need processing yet
            except ProcessLaterError:
                pass
            # The trigger raised an (expected) error while processing
            except ProcessError:
                pass


def clean_triggers(expiration_dt=None, type_to_table=None):
    """
    Clean old processed triggers from the database.

    Args:
        expiration_dt (optional datetime): triggers processed before this timestamp will be cleaned up.
            Defaults to 2 months before the current time.
        type_to_table (optional dict): maps trigger type to database table name.
            Defaults to DJTRIGGERS_TYPE_TO_TABLE django setting.

    `type_to_table` contains has information about which trigger has information
    in which table. This setting is a dict with the trigger types as keys and two
    options for values:

    - a string containing the table where the trigger information is stored
      (with a trigger_ptr_id to link it)
    - a tuple containing elements of two possible types:
        - a string containing the table where the trigger information is stored
          (with a trigger_ptr_id to link it)
        - a tuple containing a tablename and an id field

    Example:

    {'simple_trigger': 'simple_trigger_table',
     'complex_trigger': ('complex_trigger_table1', 'complex_trigger_table2'),
     'complexer_trigger': (('complexer_trigger_table1', 'complexer_trigger_id'), 'complexer_trigger_table2'),
    }
    """
    if expiration_dt is None:
        expiration_dt = timezone.now() - relativedelta(months=2)

    if type_to_table is None:
        type_to_table = getattr(settings, 'DJTRIGGERS_TYPE_TO_TABLE', {})

    cursor = connections['default'].cursor()
    sentinel = object()
    nr_deleted = 0

    for trigger in Trigger.objects.filter(date_processed__lt=expiration_dt):
        # Delete custom trigger information
        table = type_to_table.get(trigger.trigger_type, sentinel)
        if isinstance(table, tuple):
            for t in table:
                if isinstance(t, tuple):
                    cursor.execute('DELETE FROM {} WHERE {} = {}'.format(t[0], t[1], trigger.id))
                else:
                    cursor.execute('DELETE FROM {} WHERE trigger_ptr_id = {}'.format(t, trigger.id))
        elif table != sentinel:
            cursor.execute('DELETE FROM {} WHERE trigger_ptr_id = {}'.format(table, trigger.id))

        # Delete the trigger from the main table
        trigger.delete()
        nr_deleted += 1

    return nr_deleted
