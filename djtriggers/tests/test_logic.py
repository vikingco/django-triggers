from datetime import timedelta
from mock import patch

from django.test import override_settings
from django.test.testcases import TestCase
from django.utils import timezone

from djtriggers.logic import process_triggers
from djtriggers.tests.factories.triggers import DummyTriggerFactory


class SynchronousExecutionTest(TestCase):
    def setUp(self):
        self.now = timezone.now()

    def test_process_after_now(self):
        trigger = DummyTriggerFactory()
        with patch('djtriggers.models.Lock'):
            process_triggers()
        trigger.refresh_from_db()
        assert trigger.date_processed is not None

    def test_process_after_yesterday(self):
        trigger = DummyTriggerFactory(process_after=self.now - timedelta(days=1))
        with patch('djtriggers.models.Lock'):
            process_triggers()
        trigger.refresh_from_db()
        assert trigger.date_processed is not None

    def test_process_after_tomorrow(self):
        trigger = DummyTriggerFactory(process_after=self.now + timedelta(days=1))
        process_triggers()
        trigger.refresh_from_db()
        assert trigger.date_processed is None

    def test_already_processed(self):
        trigger = DummyTriggerFactory(date_processed=self.now)
        process_triggers()
        trigger.refresh_from_db()
        assert trigger.date_processed == self.now


class AsynchronousExecutionTest(TestCase):
    def setUp(self):
        self.now = timezone.now()

    @override_settings(DJTRIGGERS_ASYNC_HANDLING=True)
    def test_process_after_now(self):
        trigger = DummyTriggerFactory()
        with patch('djtriggers.logic.process_trigger.apply_async') as process_trigger_patch:
            process_triggers()
            process_trigger_patch.assert_called_once_with((trigger.id, 'djtriggers', 'DummyTrigger'),
                                                          {'use_statsd': False}, max_retries=0)

    @override_settings(DJTRIGGERS_ASYNC_HANDLING=True)
    def test_process_after_yesterday(self):
        trigger = DummyTriggerFactory(process_after=self.now - timedelta(days=1))
        with patch('djtriggers.logic.process_trigger.apply_async') as process_trigger_patch:
            process_triggers()
            process_trigger_patch.assert_called_once_with((trigger.id, 'djtriggers', 'DummyTrigger'),
                                                          {'use_statsd': False}, max_retries=0)

    @override_settings(DJTRIGGERS_ASYNC_HANDLING=True)
    def test_process_after_tomorrow(self):
        DummyTriggerFactory(process_after=self.now + timedelta(days=1))
        with patch('djtriggers.logic.process_trigger.apply_async') as process_trigger_patch:
            process_triggers()
            assert not process_trigger_patch.called

    @override_settings(DJTRIGGERS_ASYNC_HANDLING=True)
    def test_already_processed(self):
        DummyTriggerFactory(date_processed=self.now)
        with patch('djtriggers.logic.process_trigger.apply_async') as process_trigger_patch:
            process_triggers()
            assert not process_trigger_patch.called
