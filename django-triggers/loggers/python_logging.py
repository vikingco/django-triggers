from django-triggers.loggers.base import TriggerLogger

from logging import log, info


class PythonLogger(TriggerLogger):
    """
    Logger using the default python logger.
    """
    def log_result(self, trigger, message, level=None):
        if level:
            log(level, message)
        else:
            info(message)

    def log_message(self, trigger, message, level=None):
        if level:
            log(level, message)
        else:
            info(message)
