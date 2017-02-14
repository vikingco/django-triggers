from logging import getLogger

from django.core.management.base import NoArgsCommand

from djtriggers.logic import clean_triggers


logger = getLogger(__name__)


class Command(NoArgsCommand):
    help = clean_triggers.__doc__.strip()

    def handle_noargs(self, **options):
        nr_deleted = clean_triggers()
        logger.info('Cleaned up %s expired triggers', nr_deleted)
