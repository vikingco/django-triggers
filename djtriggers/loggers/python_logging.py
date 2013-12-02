from djtriggers.loggers.base import TriggerLogger

import logging

class PythonLogger(TriggerLogger):
    """
    Logger using the default python logger.
    """
    def log_result(self, trigger, message, level=None):
        if level:
            logging.log(level, message)
        else:
            logging.info(message)

    def log_message(self, trigger, message, level=None):
        if level:
            logging.log(level, message)
        else:
            logging.info(message)
