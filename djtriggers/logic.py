from inspect import isabstract
from logging import getLogger

from datetime import datetime
from dateutil.relativedelta import relativedelta

from locking.models import NonBlockingLock

from django.db import connections
from django.db.models import Q
from django.apps import apps
from django.conf import settings

from djtriggers.models import Trigger
from djtriggers.exceptions import ProcessError, ProcessLaterError


logger = getLogger(__name__)


def process_triggers(use_statsd=False, function_logger=None):
    """
    Process all triggers that are ready for processing.

    This function takes a Database Lock when running, to prevent
    triggers being processed multiple times.
    """
    # Override logger with function_logger (celery wants a different logger)
    if not function_logger:
        function_logger = logger

    # Take a lock to prevent multiple processing threads
    with NonBlockingLock.objects.acquire_lock(lock_name='djtriggers-process-triggers'):
        # Get statsd if necessary
        if use_statsd:
            from django_statsd.clients import statsd

        now = datetime.now()
        function_logger.info('Processing all triggers from {}'.format(now))

        # Get all database models
        for trigger_model in apps.get_models():
            # Check whether it's a trigger
            if (not issubclass(trigger_model, Trigger) or
               getattr(trigger_model, 'typed', None) is None or
               isabstract(trigger_model)):
                continue

            # Get all triggers of this type that need to be processed
            triggers = trigger_model.objects.filter(Q(process_after__isnull=True) |
                                                    Q(process_after__lt=now),
                                                    date_processed__isnull=True)

            function_logger.info('Start processing %d triggers of type %s', triggers.count(), trigger_model.typed)
            count_done, count_error, count_exception = 0, 0, 0

            # Process each trigger
            for trigger in triggers:
                try:
                    trigger.process()

                    # Send stats to statsd if necessary
                    if use_statsd:
                        statsd.incr('triggers.{}.processed'.format(trigger.trigger_type))
                        if trigger.date_processed and trigger.process_after:
                            statsd.timing('triggers.{}.process_delay_seconds'.format(trigger.trigger_type),
                                          (trigger.date_processed - trigger.process_after).total_seconds())
                # The trigger didn't need processing yet
                except ProcessLaterError:
                    pass
                # The trigger raised an (expected) error while processing
                except ProcessError:
                    count_error += 1
                # A general exception occurred
                except Exception, e:
                    count_exception += 1
                    message = 'Processing of %s %s raised a %s'
                    function_logger.exception(message, trigger_model.typed, trigger.pk, type(e).__name__)
                # The trigger was successfully processed
                else:
                    count_done += 1

            function_logger.info('success: {}, error: {}, exception: {}'.format(count_done,
                                                                                count_error, count_exception))


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
        expiration_dt = datetime.now() - relativedelta(months=2)

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
