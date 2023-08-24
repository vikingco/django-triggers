from django-triggers.models import Trigger


class DummyTrigger(Trigger):
    class Meta:
        proxy = True

    typed = 'dummy_trigger'

    def _process(self, dictionary):
        pass
