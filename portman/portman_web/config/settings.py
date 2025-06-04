# -*- coding: utf-8 -*-
import os
from datetime import timedelta
import posixpath
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend'
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: Keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

PORTMAN_ENV = os.environ.get('PORTMAN_ENV', 'prod')
if PORTMAN_ENV not in ['prod', 'stage', 'dev']:
    raise ValueError("Invalid environment: PORTMAN_ENV must be one of ['prod', 'stage', 'dev']")

DEBUG = PORTMAN_ENV != 'prod'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')

INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'django_extensions',
    'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'rest_framework_swagger',
    'architect',
    'compressor',
    'compress',
    'adminplus',
    'corsheaders',
    'users',
    'dslam',
    'router',
    'switch',
    'radio',
    'contact',
    'olt.apps.OltConfig',
    'cloud',
    'filemanager',
    'zabbix',
    'lte',
    'cartable.apps.CartableConfig',
    'knowledge_graph',
    'sky_node',
    'ngn',
    'django_celery_beat'
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.locale.LocaleMiddleware'
)

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'accept-language',
    'origin',
    'authorization',
    'x-csrftoken',
)
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'config.urls'

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

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'PAGINATE_BY_PARAM': 'page_size',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

JWT_AUTH = {
    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_ALGORITHM': 'HS256',
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': timedelta(days=2),
    'JWT_ALLOW_REFRESH': True,
    'JWT_AUTH_HEADER_PREFIX': 'Token',
}

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = "users.User"
AUTH_GROUP_MODEL = 'users.GroupInfo'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

LOGIN_REDIRECT_URL = '/index/'

LANGUAGES = [
    ('fa', _('Farsi')),
    ('en', _('English')),
]
LANGUAGE_CODE = 'en-us'
LOCALE_PATHS = [os.path.join(BASE_DIR, "config/translations/locale")]

TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_L10N = True
USE_TZ = False

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
ADMIN_TOOLS_MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, "admin/")
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'media'),)

COMPRESS_ENABLED = os.environ.get('COMPRESS_ENABLED', False)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': True,
    'DOC_EXPANSION': 'list',
    'APIS_SORTER': 'alpha'
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'nfo': {
            'level': 'INFO',
            'class': 'logging.StreamHandler'
        },
        'applogfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'portmanLog.log'),
            'maxBytes': 15 * 1024 * 1024,  # 15MB
            'backupCount': 10
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['applogfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

EMAIL_USE_TLS = False
