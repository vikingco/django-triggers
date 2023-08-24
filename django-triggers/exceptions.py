class AlreadyProcessedError(Exception):
    pass


class ProcessError(Exception):
    pass


class ProcessLaterError(ProcessError):
    def __init__(self, process_after, *args):
        super(ProcessLaterError, self).__init__(*args)
        self.process_after = process_after
