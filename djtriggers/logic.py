from logging import getLogger

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import connections
from django.db.models import Q
from django.utils import timezone

from .exceptions import ProcessError, ProcessLaterError, AlreadyProcessedError
from .models import Trigger
from .tasks import process_trigger

logger = getLogger(__name__)


def process_triggers(use_statsd=False):
    """
    Process all triggers that are ready for processing.
    :param bool use_statsd: whether to use_statsd
    :return: None
    """
    now = timezone.now()
    logger.info('Processing all triggers from {}'.format(now))

    # Get all triggers that need to be processed
    triggers = Trigger.objects.filter(Q(process_after__isnull=True) | Q(process_after__lt=now),
                                      date_processed__isnull=True)
    if getattr(settings, 'DJTRIGGERS_ASYNC_HANDLING', False):
        _process_async(triggers, use_statsd)
    else:
        _process_sync(triggers, use_statsd)


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

    # Get triggers to be deleted
    to_delete = Trigger.objects.filter(date_processed__lt=expiration_dt)
    for trigger in to_delete:
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


def _process_async(triggers, use_statsd):
    """
    Process given triggers asynchronously
    :param django.db.models.query.QuerySet triggers: triggers to be processed
    :param bool use_statsd: whether to use statsd
    :return: None
    """
    for trigger in triggers:
        process_trigger.apply_async((trigger.id,), {'use_statsd': use_statsd},
                                    max_retries=getattr(settings, 'DJTRIGGERS_CELERY_TASK_MAX_RETRIES', 0))


def _process_sync(triggers, use_statsd):
    """
    Process given triggers synchronously
    :param django.db.models.query.QuerySet triggers: triggers to be processed
    :param bool use_statsd: whether to use statsd
    :return: None
    """
    logger.info('Start processing %d triggers of type %s synchronously', triggers.count(), triggers[0].trigger_type)

    count_done, count_error, count_exception = 0, 0, 0

    # Process each trigger
    for trigger in triggers:
        try:
            trigger.process()
        # The trigger didn't need processing yet
        except (ProcessLaterError, AlreadyProcessedError):
            pass
        # The trigger raised an (expected) error while processing
        except ProcessError:
            count_error += 1
        # A general exception occurred
        except Exception, e:
            logger.exception(e)
            count_exception += 1
        # The trigger was successfully processed
        else:
            count_done += 1

    logger.info('success: {success_count}, error: {error_count}, exception: {exception_count}'.format(
        success_count=count_done, error_count=count_error, exception_count=count_exception))
