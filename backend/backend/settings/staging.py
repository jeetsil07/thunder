from .base import *
from decouple import Config, RepositoryEnv

def get_config():
    # This function should return the config loaded in manage.py
    environment = os.getenv('DJANGO_ENV', 'local')  # Default to 'local'
    env_file = f'.env.{environment}'
    return Config(RepositoryEnv(env_file))

config = get_config()  # Load the configuration

print("staging_NAME (from settings):", config('STAGING_NAME', default='Not Found')) 

DEBUG = config('DEBUG', default=False)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
SECRET_KEY = config('THUNDER_SECRET_KEY', default='local-secret-key')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('STAGING_DB_NAME'),
        'USER': config('STAGING_DB_USER'),
        'PASSWORD': config('STAGING_DB_PASSWORD'),
        'HOST': config('STAGING_DB_HOST'),
        'PORT': config('STAGING_DB_PORT'),
    }
}
