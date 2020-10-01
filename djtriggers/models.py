from logging import ERROR, WARNING
from redis.exceptions import LockError

from django.conf import settings
from django.db import models
from django.db.models.base import ModelBase
from django.utils import timezone

from .managers import TriggerManager
from .exceptions import ProcessLaterError
from .locking import redis_lock
from .loggers import get_logger
from .loggers.base import TriggerLogger


class TriggerBase(ModelBase):
    """
    A meta class for all Triggers. Adds a default manager that filters
    on type.
    """
    def __new__(cls, name, bases, attrs):
        super_new = super(TriggerBase, cls).__new__
        typed = attrs.pop('typed', None)
        if typed is not None:
            attrs['objects'] = TriggerManager(typed)
        new_class = super_new(cls, name, bases, attrs)
        if typed is None:
            return new_class

        new_class.typed = typed
        return new_class


class Trigger(models.Model):
    """
    A persistent Trigger that needs processing.

    Triggers are created when a certain state is reached internally
    or externally. Triggers are persistent and need processing after
    a certain point in time.

    To create a trigger start by subclassing Trigger and setting the
    'typed' attribute. 'typed' should be a unique slug that identifies
    the trigger. Subclasses should also implement '_process()'.

    Subclasses can be proxy models when no extra data needs to be
    stored. Otherwise use regular subclassing. This will create an
    additional table with trigger specific data and a one-to-one
    relation to the triggers table.

    'source' is a free-form field that can be used to uniquely determine
    the source of the trigger.

    There is a logging framework included. If passed a logger argument in the
    __init__, that logger will be used, otherwise the class' _logger_class
    determines the logger (if any). Default is no logging.
    """
    __metaclass__ = TriggerBase

    # Set typed in a subclass to make it a typed trigger.
    typed = None

    trigger_type = models.CharField(max_length=50, db_index=True)
    source = models.CharField(max_length=150, null=True, blank=True, db_index=True)
    date_received = models.DateTimeField(default=timezone.now)
    date_processed = models.DateTimeField(null=True, blank=True, db_index=True)
    process_after = models.DateTimeField(null=True, blank=True, db_index=True)
    number_of_tries = models.IntegerField(default=0)
    successful = models.BooleanField(default=None, null=True)

    _logger_class = None

    def __init__(self, *args, **kwargs):
        super(Trigger, self).__init__(*args, **kwargs)
        if hasattr(self, 'typed'):
            self.trigger_type = self.typed

        if self._logger_class:
            self.logger = get_logger(self._logger_class)
        else:
            self.logger = TriggerLogger()

    def set_source(self, *args):
        args = [str(arg) for arg in args]
        self.source = '$'.join(args)

    def get_source(self):
        return tuple(x for x in self.source.split('$') if x != '')

    def process(self, force=False, logger=None, dictionary=None, use_statsd=False):
        """
        Executes the Trigger
        :param bool force: force the execution
        :param string logger: slug of preferred logger
        :param dict dictionary: dictionary needed by trigger to execute
        :param bool use_statsd: whether to use statsd
        :return: None
        """
        dictionary = {} if dictionary is None else {}

        # The task gets locked because multiple tasks in the queue can process the same trigger.
        # The lock assures no two tasks can process a trigger simultaneously.
        # The check for date_processed assures a trigger is not executed multiple times.
        try:
            with redis_lock('djtriggers-' + str(self.id), blocking_timeout=0):
                if logger:
                    self.logger = get_logger(logger)
                now = timezone.now()
                if not force and self.date_processed is not None:
                    # trigger has already been processed. So everything is fine
                    return
                if not force and self.process_after and self.process_after >= now:
                    raise ProcessLaterError(self.process_after)

                try:
                    # execute trigger
                    self.logger.log_result(self, self._process(dictionary))
                    self._handle_execution_success(use_statsd)
                except ProcessLaterError as e:
                    self.process_after = e.process_after
                    self.save()
                except Exception as e:
                    self._handle_execution_failure(e, use_statsd)
                    raise
        except LockError:
            pass

    def _process(self, dictionary):
        raise NotImplementedError()

    def _handle_execution_failure(self, exception, use_statsd=False):
        """
        Handle execution failure of the trigger
        :param Exception exception: the exception raised during failure
        :param bool use_statsd: whether to use statsd
        :return: None
        """
        self.number_of_tries += 1
        # Log message if starts retrying too much
        if self.number_of_tries > getattr(settings, 'DJTRIGGERS_TRIES_BEFORE_WARNING', 3):
            # Set a limit for retries
            if self.number_of_tries >= getattr(settings, 'DJTRIGGERS_TRIES_BEFORE_ERROR', 5):
                # Set date_processed so it doesn't retry anymore
                self.date_processed = timezone.now()
                self.successful = False
                level = ERROR
            else:
                level = WARNING

            message = 'Processing of {trigger_type} {trigger_key} raised a {exception_type} (try nr. {try_count})'.\
                format(trigger_type=self.trigger_type, trigger_key=self.pk, exception_type=type(exception).__name__,
                       try_count=self.number_of_tries)
            self.logger.log_message(self, message, level=level)

        # Send stats to statsd if necessary
        if use_statsd:
            from django_statsd.clients import statsd
            statsd.incr('triggers.{trigger_type}.failed'.format(trigger_type=self.trigger_type))

        self.save()

    def _handle_execution_success(self, use_statsd=False):
        """
        Handle execution success of the trigger
        :param bool use_statsd: whether to use statsd
        :return: None
        """
        if self.date_processed is None:
            now = timezone.now()
            self.date_processed = now

        # Send stats to statsd if necessary
        if use_statsd:
            from django_statsd.clients import statsd
            statsd.incr('triggers.{trigger_type}.processed'.format(trigger_type=self.trigger_type))
            if self.date_processed and self.process_after:
                statsd.timing('triggers.{trigger_type}.process_delay_seconds'.format(trigger_type=self.trigger_type),
                              (self.date_processed - self.process_after).total_seconds())

        self.successful = True
        self.save()

    def __repr__(self):
        return 'Trigger {trigger_id} of type {trigger_type} ({is_processed}processed)'.format(
            trigger_id=self.id, trigger_type=self.trigger_type, is_processed='' if self.date_processed else 'not ')


class TriggerResult(models.Model):
    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE)
    result = models.TextField()

    def __repr__(self):
        return self.result
