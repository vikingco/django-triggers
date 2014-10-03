__doc__ = """
Process all triggers that are ready for processing.

The command takes a FileLock when running, to prevent triggers being processed multiple times.
"""

import datetime
from lockfile import FileLock, AlreadyLocked, LockTimeout
import inspect
from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.db.models import Q
from django.db.models.loading import get_models

from djtriggers.exceptions import ProcessError, ProcessLaterError
from djtriggers.models import Trigger

from logging import getLogger
logger = getLogger(__name__)


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--use-statsd', dest='use_statsd', action='store_true', default=False,
            help='Send stats about processing to Statsd'),
    )

    def handle_noargs(self, **options):
        """
        Process all triggers in order of trigger type. This blocks while
        processing the triggers.
        """
        # Take a lock to prevent multiple processing threads
        lock = FileLock('process_triggers')
        try:
            lock.acquire(-1)
        except (AlreadyLocked, LockTimeout):
            return

        # Get statsd if necessary
        if options['use_statsd']:
            from django_statsd.clients import statsd

        now = datetime.datetime.now()
        logger.info('Processing all triggers from %s' % now)
        try:
            # Get all database models
            for trigger_model in get_models():
                # Check whether it's a trigger
                if not issubclass(trigger_model, Trigger) or getattr(trigger_model, 'typed', None) is None or \
                        inspect.isabstract(trigger_model):
                    continue

                # Get all triggers of this type that need to be processed
                triggers = trigger_model.objects.filter(
                        Q(process_after__isnull=True) | Q(process_after__lt=now), date_processed__isnull=True)
                logger.info('Start processing %d triggers of type %s', triggers.count(), trigger_model.typed)
                count_done, count_error, count_exception = 0, 0, 0

                # Process each trigger
                for trigger in triggers:
                    try:
                        trigger.process()

                        # Send stats to statsd if necessary
                        if options['use_statsd']:
                            statsd.incr('triggers.%s.processed' % trigger.trigger_type)
                            if trigger.date_processed and trigger.process_after:
                                statsd.timing('triggers.%s.process_delay_seconds' % trigger.trigger_type,
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
                        logger.exception('Processing of %s %s raised a %%s' % (trigger_model.typed, trigger.pk),
                                type(e).__name__)
                    # The trigger was successfully processed
                    else:
                        count_done += 1

                logger.info('success: %s, error: %s, exception: %s' % (count_done, count_error, count_exception))
        finally:
            lock.release()
