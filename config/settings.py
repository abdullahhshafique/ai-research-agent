"""
Django settings for AI Research Agent project - Render Ready.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env", override=True)

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
# Add Render domain automatically
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# CSRF trusted origins - required for HTTPS form submissions (login, research, etc.)
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin
]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.research',
    'apps.reports',
    'apps.history',
    'apps.collaboration',
    'apps.templates_app',
    'apps.dashboard',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.utils.middleware.ContentSecurityPolicyMiddleware',
    'apps.utils.middleware.QuotaMiddleware',
    'apps.utils.middleware.RequestTimingMiddleware',
    'apps.utils.rate_limit.RateLimitMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.utils.context_processors.global_flags',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database - PostgreSQL on Render via DATABASE_URL, SQLite locally
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise static file serving (Django 5.x STORAGES API)
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Authentication URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Email settings
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@airesearchagent.com')

# Optional real SMTP (Phase 3) — set EMAIL_BACKEND + EMAIL_HOST/... to activate
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')

# --- Phase 3 opt-ins ---
USE_CELERY = bool(os.getenv('CELERY_BROKER_URL', ''))
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', '')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)

# Optional R2/S3 persistent media
USE_S3_MEDIA = os.getenv('USE_S3_MEDIA', 'False').lower() in ('1', 'true', 'yes')
if USE_S3_MEDIA:
    AWS_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', '')
    AWS_STORAGE_BUCKET_NAME = os.getenv('R2_BUCKET', '')
    AWS_S3_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL', '')
    AWS_S3_REGION_NAME = os.getenv('R2_REGION', 'auto')
    AWS_DEFAULT_ACL = 'private'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# API Keys
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

# Research settings
MAX_RESULTS = int(os.getenv('MAX_RESULTS', '5'))
SEARCH_DEPTH = os.getenv('SEARCH_DEPTH', 'advanced')
QUOTA_FREE = int(os.getenv('QUOTA_FREE', '10'))
QUOTA_PREMIUM = int(os.getenv('QUOTA_PREMIUM', '100'))
PDF_RETENTION_DAYS = int(os.getenv('PDF_RETENTION_DAYS', '30'))
MAX_QUERY_LENGTH = int(os.getenv('MAX_QUERY_LENGTH', '500'))

# CSP Settings
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com"]
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com"]
CSP_IMG_SRC = ["'self'", "data:", "https:"]
CSP_FONT_SRC = ["'self'"]
CSP_CONNECT_SRC = ["'self'"]
CSP_FRAME_ANCESTORS = ["'none'"]

# Rate Limiting Settings
RATE_LIMIT_ANONYMOUS = int(os.getenv('RATE_LIMIT_ANONYMOUS', '60'))
RATE_LIMIT_AUTHENTICATED = int(os.getenv('RATE_LIMIT_AUTHENTICATED', '300'))

# Logging - console only in production (Render filesystem is ephemeral)
_LOG_HANDLERS = ['console'] if not DEBUG else ['file', 'console']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Only create a file handler / logs directory for local development
if DEBUG:
    LOGS_DIR = BASE_DIR / 'logs'
    LOGS_DIR.mkdir(exist_ok=True)
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': LOGS_DIR / 'django.log',
        'formatter': 'verbose',
    }

# Sentry (Phase 3) — opt-in via SENTRY_DSN
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if SENTRY_DSN and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_RATE', '0.1')),
        profiles_sample_rate=0.0,
        send_default_pii=False,
    )

# Security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
