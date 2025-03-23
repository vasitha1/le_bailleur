"""
Django settings for le_bailleur_project project.

Generated by 'django-admin startproject' using Django 4.2.20.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from celery import Celery  
from celery.schedules import crontab
import dj_database_url
import os


# Initialize the Celery application  
app = Celery('le_bailleur_project')  
app.config_from_object('django.conf:settings', namespace='CELERY')  
app.autodiscover_tasks()  

# Add this to your settings.py to schedule the task  
CELERY_BEAT_SCHEDULE = {  
    'check-due-rent-every-day': {  
        'task': 'properties.tasks.check_due_rent_and_notify',  
        'schedule': crontab(hour=14, minute=0),  # Runs every at 2 pm
    },  
}  

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'jdhk34y28idej,kled09325`\k;JHKTEDKEDKEK2DJTUIO`973561476YEJMNZcsgmdgjksddr21764012\'d][;@@$%!@&@^#gdkdaFGDIIDHDGDDKJJAGDJKRGDSHJ2I4732689^#*973]'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "Le-bailleur.onrender.com",
]

PORT = os.getenv('PORT', '10000') 


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #ADDED APPLICATIONS
    'properties', 
    'rest_framework', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'le_bailleur_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'le_bailleur_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Douala'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR,'static')]
STATIC_ROOT = os.path.join(BASE_DIR,'staticfiles')

MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = '/uploads/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Use Whitenoise for serving static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Database Configuration for Render
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

LOGIN_REDIRECT_URL = 'dashboard'
LOGIN_URL = 'login'

WHATSAPP_URL = 'https://graph.facebook.com/v22.0/591778180688038/'
WHATSAPP_TOKEN = 'Bearer EAAULwmnApM0BO32b2w0ZBaZAsPGgo42keG4ZCHQZBOfm2GhfLL7UpdfDgdBAsq1Jfb2BZCct6MZA5sID0ZBZBPiITnjMw0mZCOYZBNBJgHpGMqwKXPyWyq2dEuVHueX1O5lpCICXXvyJmweHAVib7bdd0tZCoLJObFHMNjzC20DOrsDucrvdrJUscqMC4B8wShyx7a7ctTF5eD7LYoqOyfy1ZBlE9xQg24QsFZBkW7j3pvkhfmpAZD'
WHATSAPP_BUSINESS_ACCOUNT_ID = '678297307994040'
WHATSAPP_APP_ID = '1420304509347021'
WHATSAPP_SECRET_KEY = os.getenv('WHATSAPP_SECRET_KEY', '7e5de035-f7ed-4737-b2bf-fc71b9cb1e63')
WHATSAPP_VERIFY_TOKEN = '7e5de035-f7ed-4737-b2bf-fc71b9cb1e63'