from datetime import timedelta

from mock import patch
from django.test import override_settings
from django.test.testcases import TestCase
from django.utils import timezone

from djtriggers.logic import process_triggers
from djtriggers.tests.factories.triggers import NormalDummyTriggerFactory


class LogicTest(TestCase):

    def populate_db(self, factory, quantity=1, **kwargs):
        return [factory(**kwargs) for _ in xrange(quantity)]

    @override_settings(DJTRIGGERS_ASYNC_HANDLING=False)
    @patch('djtriggers.logic._process_sync')
    def test_process_triggers_sync(self, mock_process_sync):
        now = timezone.now()
        normal_triggers_due1 = self.populate_db(NormalDummyTriggerFactory, quantity=3)
        normal_triggers_due2 = self.populate_db(NormalDummyTriggerFactory, quantity=7,
                                                process_after=now - timedelta(days=1))
        self.populate_db(NormalDummyTriggerFactory, quantity=11, process_after=now + timedelta(days=1))
        self.populate_db(NormalDummyTriggerFactory, quantity=13, date_processed=now)
        process_triggers()

        normal_triggers_due = normal_triggers_due1 + normal_triggers_due2
        triggers_fetched = mock_process_sync.call_args[0][0]
        assert set(triggers_fetched) == set(normal_triggers_due)

    @override_settings(DJTRIGGERS_ASYNC_HANDLING=True)
    @patch('djtriggers.logic._process_async')
    def test_process_triggers_async(self, mock_process_async):
        now = timezone.now()
        normal_triggers_due1 = self.populate_db(NormalDummyTriggerFactory, quantity=3)
        normal_triggers_due2 = self.populate_db(NormalDummyTriggerFactory, quantity=7,
                                                process_after=now - timedelta(days=1))
        self.populate_db(NormalDummyTriggerFactory, quantity=11, process_after=now + timedelta(days=1))
        self.populate_db(NormalDummyTriggerFactory, quantity=13, date_processed=now)
        process_triggers()

        normal_triggers_due = normal_triggers_due1 + normal_triggers_due2
        triggers_fetched = mock_process_async.call_args[0][0]
        assert set(triggers_fetched) == set(normal_triggers_due)
