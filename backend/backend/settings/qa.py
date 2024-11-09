from .base import *
from decouple import Config, RepositoryEnv

def get_config():
    # This function should return the config loaded in manage.py
    # environment = os.getenv('DJANGO_ENV', 'local')  # Default to 'local'
    # env_file = f'.env.{environment}'
    env_file = f'.env.qa'
    return Config(RepositoryEnv(env_file))

config = get_config()  # Load the configuration

print("QA_DB_NAME (from settings):", config('QA_NAME', default='Not Found')) 
print("DEBUG (from settings):", config('THUNDER_DEBUG')) 

CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
SECRET_KEY = config('THUNDER_SECRET_KEY', default='local-secret-key')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('QA_DB_NAME'),
        'USER': config('QA_DB_USER'),
        'PASSWORD': config('QA_DB_PASSWORD'),
        'HOST': config('QA_DB_HOST'),
        'PORT': config('QA_DB_PORT'),
    }
}

SECRET_KEY = config('THUNDER_SECRET_KEY')

STATIC_URL = 'static/'
STATIC_ROOT = '/var/www/backendproject/backendqa/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/backendproject/backendqa/media/'

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