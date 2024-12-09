from .base import *
from decouple import Config, RepositoryEnv

def get_config():
    # This function should return the config loaded in manage.py
    # environment = os.getenv('DJANGO_ENV', 'local')  # Default to 'local'
    # env_file = f'.env.{environment}'
    env_file = f'.env.staging'
    return Config(RepositoryEnv(env_file))

config = get_config()  # Load the configuration

print("staging_NAME (from settings):", config('STAGING_NAME', default='Not Found')) 

DEBUG = config('THUNDER_DEBUG', default=False)
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)
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

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL'),  # Default Redis port is 6379 and 1 is the Redis DB number
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer'
        }
    }
}

STATIC_URL = 'static/'
STATIC_ROOT = '/var/www/backendproject/backendstag/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/backendproject/backendstag/media/'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),  # Adjusted for a shorter session
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # A longer refresh token lifetime
    'ROTATE_REFRESH_TOKENS': True,  # Enable refresh token rotation for added security
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist old refresh tokens after rotation
    'ALGORITHM': 'HS256',  # Default algorithm
    'SIGNING_KEY': config('JWT_SIGINING_KEY'),  # You should set this to a secure key
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),  # The token type is Bearer
    'USER_ID_FIELD': 'user_id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=30),
}

# to be continue 
