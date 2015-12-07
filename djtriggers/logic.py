from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.db import connections
from django.conf import settings

from djtriggers.models import Trigger


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

    XXX: why do we need to pass this in? Should be available via the trigger IMHO.
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
                    cursor.execute('DELETE FROM %s WHERE %s = %s' % (t[0], t[1], trigger.id))
                else:
                    cursor.execute('DELETE FROM %s WHERE trigger_ptr_id = %s' % (t, trigger.id))
        elif table != sentinel:
            cursor.execute('DELETE FROM %s WHERE trigger_ptr_id = %s' % (table, trigger.id))

        # Delete the trigger from the main table
        trigger.delete()
        nr_deleted += 1

    return nr_deleted
