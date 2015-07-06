__doc__ = """
Clean old processed triggers from the database.

This uses the DJTRIGGERS_TYPE_TO_TABLE setting, which has information about which trigger has information in which
table. This setting is a dict with the trigger types as keys and two options for values:
    - a string containing the table where the trigger information is stored (with a trigger_ptr_id to link it)
    - a tuple containing elements of two possible types:
        - a string containing the table where the trigger information is stored (with a trigger_ptr_id to link it)
        - a tuple containing a tablename and an id field

An example:
DJTRIGGERS_TYPE_TO_TABLE = {
    'simple_trigger': 'simple_trigger_table',
    'complex_trigger': ('complex_trigger_table1', 'complex_trigger_table2'),
    'complexer_trigger': (('complexer_trigger_table1', 'complexer_trigger_id'), 'complexer_trigger_table2'),
}
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.db import connections

from djtriggers.models import Trigger

from logging import getLogger
logger = getLogger(__name__)


class Command(NoArgsCommand):
    help = __doc__.strip()

    def handle_noargs(self, **options):
        cursor = connections['default'].cursor()

        # Get triggers to be deleted
        to_be_deleted = Trigger.objects.filter(date_processed__lte=datetime.now() - relativedelta(months=2))
        logger.info('Deleting %s records' % to_be_deleted.count())

        # Delete each trigger
        for trigger in to_be_deleted:
            # Delete the specific trigger information
            table = getattr(settings.DJTRIGGERS_TYPE_TO_TABLE, trigger.trigger_type, None)
            if table is None:
                continue
            if isinstance(table, tuple):
                for t in table:
                    if isinstance(t, tuple):
                        cursor.execute('DELETE FROM %s WHERE %s = %s' % (t[0], t[1], trigger.id))
                    else:
                        cursor.execute('DELETE FROM %s WHERE trigger_ptr_id = %s' % (t, trigger.id))
            else:
                cursor.execute('DELETE FROM %s WHERE trigger_ptr_id = %s' % (table, trigger.id))

            # Delete the trigger from the main table
            trigger.delete()
