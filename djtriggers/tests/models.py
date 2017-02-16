from djtriggers.models import Trigger


class NormalDummyTrigger(Trigger):
    class Meta:
        proxy = True

    typed = 'normal_trigger'

    def _process(self, dictionary):
        pass
