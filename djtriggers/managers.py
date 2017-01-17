from django.db import models
from django.db.models.query import QuerySet


class SubclassingQuerySet(QuerySet):
    """
    This QuerySet uses the content_type field on Trigger to return triggers as objects of the class they were created
    as.
    """
    def __getitem__(self, k):
        result = super(SubclassingQuerySet, self).__getitem__(k)
        if isinstance(result, models.Model):
            return result.as_leaf_class()
        else:
            return result

    def __iter__(self):
        for item in super(SubclassingQuerySet, self).__iter__():
            if isinstance(item, models.Model):
                yield item.as_leaf_class()
            else:
                yield item


class TriggerManager(models.Manager):
    def __init__(self):
        super(TriggerManager, self).__init__()

    def get_queryset(self):
        qs = SubclassingQuerySet(self.model)
        return qs

    def get_unprocessed_triggers(self):
        qs = self.get_queryset()
        return qs.filter(date_processed__isnull=True)

    def get(self, **kwargs):
        no_leaf_class = kwargs.pop('no_leaf_class', False)
        item = super(TriggerManager, self).get(**kwargs)
        if isinstance(item, models.Model) and not no_leaf_class:
            return item.as_leaf_class()
        else:
            return item
