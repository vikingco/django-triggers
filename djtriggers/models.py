import datetime

from django.db import models
from django.db.models.base import ModelBase

from mvne.telco.triggers.managers import TriggerManager
from mvne.telco.triggers.exceptions import (AlreadyProcessedError,
    ProcessLaterError,
)

class TypedTriggerBase(ModelBase):
    """
    A meta class for all TypedTriggers
    """
    def __new__(cls, name, bases, attrs):
        super_new = super(TypedTriggerBase, cls).__new__
        typed = attrs.pop('typed', None)
        if not typed is None:
            attrs['objects'] = TriggerManager(typed)
        new_class = super_new(cls, name, bases, attrs)
        if typed is None:
            return new_class

        new_class.typed = typed
        return new_class

class TypedTrigger(models.Model):
    """
    A TypedTrigger is a Trigger of a particular type.

    All classes using TypedTrigger should set the attribute `typed` to
    a valid trigger type. It will then not have to worry about this
    anymore.
    """
    __metaclass__ = TypedTriggerBase
    class Meta:
        # Setting abstract to false means this will generate multiple tables
        # with one-to-one relations but that would have happened anyway. Each
        # trigger needs its own trigger specific data.
        # This also makes it possible to query triggers in bulk:
        #   - How many processed?
        #   - How many scheduled?
        abstract = False

    # Set typed in a subclass to make it a typed trigger.
    typed = None

    trigger_type = models.CharField(max_length=50, db_index=True)
    source = models.CharField(max_length=250, null=True, blank=True, unique=True)
    date_received = models.DateTimeField()
    date_processed = models.DateTimeField(null=True, blank=True, db_index=True)
    process_after = models.DateTimeField(null=True, blank=True, db_index=True)

    def __init__(self, *args, **kwargs):
        super(TypedTrigger, self).__init__(*args, **kwargs)
        if hasattr(self, 'typed'):
            self.trigger_type = self.typed

    def set_source(self, *args):
        args = [str(arg) for arg in args]
        self.source = '$'.join(args)

    def get_source(self):
        return tuple(x for x in self.source.split('$') if x != '')

    def process(self, force=False):
        now = datetime.datetime.now()
        if not force and not self.date_processed is None:
            raise AlreadyProcessedError()
        if not force and self.process_after and self.process_after >= now:
            raise ProcessLaterError(self.process_after)

        try:
            self._process()
            self.date_processed = datetime.datetime.now()
        except ProcessLaterError as e:
            self.process_after = e.process_after
            self.save()
            raise
        else:
            self.process_after = None
        if self.date_processed is None:
            self.date_processed = datetime.datetime.now()
        self.save()

    def _process(self):
        raise NotImplementedError()
