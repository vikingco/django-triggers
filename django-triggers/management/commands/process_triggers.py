from django.core.management.base import NoArgsCommand

from optparse import make_option

from django-triggers import logic


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
        logic.process_triggers(use_statsd=options['use_statsd'])
