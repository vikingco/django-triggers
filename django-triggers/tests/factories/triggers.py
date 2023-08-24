from django.utils import timezone
from factory import DjangoModelFactory

from django-triggers.tests.models import DummyTrigger


class DummyTriggerFactory(DjangoModelFactory):
    class Meta:
        model = DummyTrigger

    trigger_type = 'dummy_trigger_test'
    source = 'tests'
    date_received = timezone.now()
    date_processed = None
    process_after = None
    number_of_tries = 0
