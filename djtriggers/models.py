from datetime import datetime

from django.db import models
from django.db.models.base import ModelBase
from django.utils import timezone

from .managers import TriggerManager
from .exceptions import AlreadyProcessedError, ProcessLaterError
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
    the trigger. Subclasses should alse implement '_process()'.

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
    source = models.CharField(max_length=250, null=True, blank=True, db_index=True)
    date_received = models.DateTimeField(default=datetime.now)
    date_processed = models.DateTimeField(null=True, blank=True, db_index=True)
    process_after = models.DateTimeField(null=True, blank=True, db_index=True)

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

    def process(self, force=False, logger=None, dictionary={}):
        if logger:
            self.logger = get_logger(logger)
        now = timezone.now()
        if not force and self.date_processed is not None:
            raise AlreadyProcessedError()
        if not force and self.process_after and self.process_after >= now:
            raise ProcessLaterError(self.process_after)

        try:
            self.logger.log_result(self, self._process(dictionary))
        except ProcessLaterError as e:
            self.process_after = e.process_after
            self.save()
            raise
        if self.date_processed is None:
            self.date_processed = now
        self.save()

    def _process(self, dictionary):
        raise NotImplementedError()

    def __repr__(self):
        return 'Trigger %s of type %s (%sprocessed)' % (self.id, self.trigger_type,
                                                        '' if self.date_processed else 'not ')


class TriggerResult(models.Model):
    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE)
    result = models.TextField()

    def __repr__(self):
        return self.result
