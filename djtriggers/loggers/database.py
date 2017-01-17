from logging import log, info

from djtriggers.loggers.base import TriggerLogger


class DatabaseLogger(TriggerLogger):
    def log_result(self, trigger, message, level=None):
        from djtriggers.models import TriggerResult
        TriggerResult.objects.create(trigger=trigger, result=message)

    def log_message(self, trigger, message, level=None):
        if level:
            log(level, message)
        else:
            info(message)


def _prettify(results):
    try:
        return '\n'.join([str(r) for r in results])
    except TypeError:
        return str(results)


class DatabaseSerializeLogger(DatabaseLogger):
    def log_result(self, trigger, results, level=None):
        if results is None:
            return

        from djtriggers.models import TriggerResult
        TriggerResult.objects.create(trigger=trigger, result=_prettify(results))
