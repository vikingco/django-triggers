SECRET_KEY = 'fake-key'

DJTRIGGERS_REDIS_URL = 'redis://localhost:6379/0'

INSTALLED_APPS = [
    'djtriggers',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
