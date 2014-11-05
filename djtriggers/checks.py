import logging

logger = logging.getLogger(__name__)

def run_checks(checks):
    """
    Run a number of checks.

    :param tuple checks: a tuple of tuples, with check name and parameters dict.

    :returns: whether all checks succeeded, and the results of each check
    :rtype: tuple of (bool, dict)
    """
    results = {}
    all_succeeded = True
    for check, kwargs in checks:
        succeeded = check(**kwargs).succeeded
        if isinstance(succeeded, bool):
            if not succeeded:
                all_succeeded = False
            results[check.__name__] = succeeded
        elif isinstance(succeeded, tuple):
            if not succeeded[0]:
                all_succeeded = False
            results[check.__name__] = succeeded
    return (all_succeeded, results)


class Check(object):
    def run(self):
        logger.debug('Running check: %s' % self.__class__.__name__)
        self._result = self._run()
        return self._result

    def _run(self):
        raise NotImplementedError()

    @property
    def result(self):
        if not self.has_run:
            return self.run()
        return self._result

    @property
    def has_run(self):
        return hasattr(self, '_result')

    @property
    def succeeded(self):
        return bool(self.result)

    def __nonzero__(self):
        return self.succeeded
