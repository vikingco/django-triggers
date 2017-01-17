SECRET_KEY = 'fake-key'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'djtriggers',
    'locking'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
