[![Coverage Status](https://coveralls.io/repos/github/vikingco/django-triggers/badge.svg)](https://coveralls.io/github/vikingco/django-triggers)
[![CI Status](https://travis-ci.org/vikingco/django-triggers.svg?branch=master)](https://travis-ci.org/vikingco/django-triggers)

About
-----

Django Triggers is a light-weight framework for having one part of an
application generate a trigger while another part responds to to it.
Triggers are persistent and can be scheduled to be processed at a later
time.

Usage
-----

Triggers are defined by subclassing the `Trigger` model. `Trigger` defines
common data structures and logic for all child triggers. The only thing a
child should have to do is override the `_process` method and set `typed` to
a unique slug.

Settings
--------

The following settings are used:
- `DJTRIGGERS_TRIES_BEFORE_WARNING`: the number of times a task can be retried before a warning is logged. Defaults to 3.
- `DJTRIGGERS_TRIES_BEFORE_ERROR`: the number of times a task can be retried before an error is raised. Defaults to 5.
- `DJTRIGGERS_ASYNC_HANDLING`: whether processing should be asynchronous (using Celery) or not. Default to False.
- `DJTRIGGERS_CELERY_TASK_MAX_RETRIES`: the number of times the Celery task for a trigger should be retried. Defaults to 0.
- `DJTRIGGERS_TYPE_TO_TABLE`: mapping of trigger types to database tables. Used for the cleanup script. Defaults to `{}`.
- `DJTRIGGERS_REDIS_URL`: the URL of the Redis instance used for locks.
- `DJTRIGGERS_LOGGERS`: separate logging config for django-triggers. Defaults to `()`.


Examples
--------

General use
===========

```python

from django-triggers.models import Trigger

class BreakfastTrigger(Trigger):
    class Meta:
        # There is no trigger specific data so make a proxy model.
        # This ensures no additional db table is created.
        proxy = True
    typed = 'breakfast'

    def _process(self, dictionary={}):
        prepare_toast()
        prepare_juice()
        eat()

```

Trigger specific data
=====================

```python

from django-triggers.models import Trigger

class PayBill(Trigger):
    class Meta:
        # We need a regular model as the trigger specific data needs a
        # place to live in the db.
        proxy = False

    amount = models.IntegerField()
    recipient = models.ForeignKey(User)

    def _process(self, dictionary={}):
        amount = self.amount
        recipient = self.recipient
        check_balance()
        pay_bill(amount, recipient)

```

Trigger processing
==================

```python

from .models import BreakfastTrigger
from .exceptions import ProcessError

trigger = BreakfastTrigger.objects.get(pk=1)
try:
    trigger.process()
except ProcessError as e:
    report_error(e)

```

Delayed processing
==================

```python

from .models import BreakfastTrigger

trigger = BreakfastTrigger()
# Process 8 hours later (this can be any datetime)
trigger.process_after = now() + timedelta(hour=8)

```
