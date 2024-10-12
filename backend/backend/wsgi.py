"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from decouple import Config, RepositoryEnv
from django.core.wsgi import get_wsgi_application

def get_settings_module():
    environment = os.getenv('DJANGO_ENV', 'local')  # Default to 'local'
    return f'backend.settings.{environment}'

# Set the default settings module based on DJANGO_ENV
os.environ.setdefault('DJANGO_SETTINGS_MODULE', get_settings_module())

# Get the WSGI application
application = get_wsgi_application()
