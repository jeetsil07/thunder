from .base import *
from decouple import Config, RepositoryEnv

def get_config():
    # This function should return the config loaded in manage.py
    environment = os.getenv('DJANGO_ENV', 'local')  # Default to 'local'
    env_file = f'.env.{environment}'
    return Config(RepositoryEnv(env_file))

config = get_config()  # Load the configuration

print("production_NAME (from settings):", config('PRODUCTION_NAME', default='Not Found')) 

DEBUG = config('DEBUG', default=False)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
SECRET_KEY = config('THUNDER_SECRET_KEY', default='local-secret-key')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('PRODUCTION_DB_NAME'),
        'USER': config('PRODUCTION_DB_USER'),
        'PASSWORD': config('PRODUCTION_DB_PASSWORD'),
        'HOST': config('PRODUCTION_DB_HOST'),
        'PORT': config('PRODUCTION_DB_PORT'),
    }
}
