from django.conf import settings
from django.core.urlresolvers import get_mod_func

REGISTRY = {}

loggers = getattr(settings, 'DJTRIGGERS_LOGGERS', ())

for entry in loggers:
    module_name, class_name = get_mod_func(entry)
    logger_class = getattr(__import__(module_name, {}, {}, ['']), class_name)
    instance = logger_class()
    REGISTRY[class_name] = instance

def get_logger(slug):
    return REGISTRY.get(slug, None)
