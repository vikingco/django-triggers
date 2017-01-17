from django.utils import timezone
from factory import DjangoModelFactory

from djtriggers.tests.models import NormalDummyTrigger


class NormalDummyTriggerFactory(DjangoModelFactory):
    class Meta:
        model = NormalDummyTrigger

    trigger_type = 'normal_trigger_test'
    source = 'tests'
    date_received = timezone.now()
    date_processed = None
    process_after = None
    number_of_tries = 0
