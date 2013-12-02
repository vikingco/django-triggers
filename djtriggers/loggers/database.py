from djtriggers.loggers.base import TriggerLogger

class DatabaseLogger(TriggerLogger):
    def log_result(self, trigger, message):
        from djtriggers.models import TriggerResult
        TriggerResult.objects.create(trigger=trigger, message=message)
