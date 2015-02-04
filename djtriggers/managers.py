from django.db import models

class TriggerManager(models.Manager):
    def __init__(self, trigger_type):
        super(TriggerManager, self).__init__()
        self.trigger_type = trigger_type

    def get_queryset(self):
        qs = super(TriggerManager, self).get_queryset()
        if self.trigger_type:
            qs = qs.filter(trigger_type=self.trigger_type)
        return qs

    def get_unprocessed_triggers(self):
        qs = self.get_queryset()
        return qs.filter(date_processed__isnull=True)

