from datetime import timedelta
from logging import ERROR, WARNING

from mock import patch
from pytest import raises
from django.test import override_settings
from django.test.testcases import TestCase
from django.utils import timezone
from locking.models import NonBlockingLock

from djtriggers.exceptions import ProcessLaterError
from djtriggers.loggers.base import TriggerLogger
from djtriggers.models import Trigger
from djtriggers.tests.factories.triggers import DummyTriggerFactory


class TriggerTest(TestCase):
    def test_handle_execution_success(self):
        trigger = DummyTriggerFactory()
        trigger._handle_execution_success()

        assert trigger.date_processed

    @patch('django_statsd.clients.statsd')
    def test_handle_execution_success_use_statsd(self, mock_statsd):
        trigger = DummyTriggerFactory(process_after=timezone.now())
        trigger._handle_execution_success(use_statsd=True)

        assert trigger.date_processed
        mock_statsd.incr.assert_called_with(
            'triggers.{trigger_type}.processed'.format(trigger_type=trigger.trigger_type))
        mock_statsd.timing.assert_called_with(
            'triggers.{trigger_type}.process_delay_seconds'.format(trigger_type=trigger.trigger_type),
            (trigger.date_processed - trigger.process_after).total_seconds())

    def test_handle_execution_failure(self):
        trigger = DummyTriggerFactory()
        original_tries = trigger.number_of_tries
        trigger._handle_execution_failure(Exception())

        assert trigger.number_of_tries == original_tries + 1

    @override_settings(DJTRIGGERS_TRIES_BEFORE_WARNING=3)
    @patch.object(TriggerLogger, 'log_message')
    def test_handle_execution_failure_dont_raise_when_under_max_retries(self, mock_logger):
        exception = Exception()
        trigger = DummyTriggerFactory(number_of_tries=2)
        original_tries = trigger.number_of_tries
        trigger._handle_execution_failure(exception)

        assert trigger.number_of_tries == original_tries + 1
        assert not mock_logger.called

    @override_settings(DJTRIGGERS_TRIES_BEFORE_WARNING=3)
    @patch.object(TriggerLogger, 'log_message')
    def test_handle_execution_failure_tries_exceeded(self, mock_logger):
        exception = Exception()
        trigger = DummyTriggerFactory(number_of_tries=3)
        original_tries = trigger.number_of_tries
        trigger._handle_execution_failure(exception)

        assert trigger.number_of_tries == original_tries + 1
        message = ('Processing of {trigger_type} {trigger_key} '
                   'raised a {exception_type} (try nr. {try_count})').format(trigger_type=trigger.trigger_type,
                                                                             trigger_key=trigger.pk,
                                                                             exception_type=type(exception).__name__,
                                                                             try_count=original_tries+1)
        mock_logger.assert_called_with(trigger, message, level=WARNING)

    @override_settings(DJTRIGGERS_TRIES_BEFORE_WARNING=3)
    @override_settings(DJTRIGGERS_TRIES_BEFORE_ERROR=5)
    @patch.object(TriggerLogger, 'log_message')
    def test_handle_execution_failure_tries_limit(self, mock_logger):
        exception = Exception()
        trigger = DummyTriggerFactory(number_of_tries=3)
        original_tries = trigger.number_of_tries
        trigger._handle_execution_failure(exception)

        assert trigger.number_of_tries == original_tries + 1
        message = ('Processing of {trigger_type} {trigger_key} '
                   'raised a {exception_type} (try nr. {try_count})').format(trigger_type=trigger.trigger_type,
                                                                             trigger_key=trigger.pk,
                                                                             exception_type=type(exception).__name__,
                                                                             try_count=original_tries + 1)
        mock_logger.assert_called_with(trigger, message, level=WARNING)

        # do an extra retry
        trigger._handle_execution_failure(exception)

        assert trigger.number_of_tries == original_tries + 2
        message = ('Processing of {trigger_type} {trigger_key} '
                   'raised a {exception_type} (try nr. {try_count})').format(trigger_type=trigger.trigger_type,
                                                                             trigger_key=trigger.pk,
                                                                             exception_type=type(exception).__name__,
                                                                             try_count=original_tries + 2)
        mock_logger.assert_called_with(trigger, message, level=ERROR)

    @patch('django_statsd.clients.statsd')
    def test_handle_execution_failure_use_statsd(self, mock_statsd):
        exception = Exception()
        trigger = DummyTriggerFactory()
        original_tries = trigger.number_of_tries
        trigger._handle_execution_failure(exception, use_statsd=True)

        assert trigger.number_of_tries == original_tries + 1
        mock_statsd.incr.assert_called_with('triggers.{trigger_type}.failed'.format(trigger_type=trigger.trigger_type))

    @patch.object(TriggerLogger, 'log_result')
    def test_process(self, mock_logger):
        trigger = DummyTriggerFactory()
        trigger.process()

        mock_logger.assert_called_with(trigger, trigger._process({}))

    @patch.object(TriggerLogger, 'log_result')
    def test_process_already_processed(self, mock_logger):
        '''Reprocessing already processed triggers should just do nothing.'''
        trigger = DummyTriggerFactory(date_processed=timezone.now())
        assert trigger.date_processed is not None
        assert not mock_logger.called

    def test_process_process_later(self):
        trigger = DummyTriggerFactory(process_after=timezone.now() + timedelta(minutes=1))
        with raises(ProcessLaterError):
            trigger.process()

    @patch.object(Trigger, '_handle_execution_failure')
    def test_process_exception_during_execution(self, mock_fail):
        trigger = DummyTriggerFactory()
        with patch.object(trigger, '_process', side_effect=Exception), raises(Exception):
            trigger.process()
        assert mock_fail.called

    @patch.object(TriggerLogger, 'log_result')
    def test_process_locked(self, mock_logger):
        trigger = DummyTriggerFactory()
        with NonBlockingLock.objects.acquire_lock(trigger):
            trigger.process()

        assert not mock_logger.called
