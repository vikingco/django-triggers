from django.db import models

class TriggerManager(models.Manager):
    def __init__(self, trigger_type):
        super(TriggerManager, self).__init__()
        self.trigger_type = trigger_type

    def get_query_set(self):
        qs = super(TriggerManager, self).get_query_set()
        if self.trigger_type:
            qs = qs.filter(trigger_type=self.trigger_type)
        return qs


