from pathlib import Path
from decouple import config, Csv
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_celery_beat",
    "django_celery_results",
    "drf_spectacular",
    "django_cleanup.apps.CleanupConfig",

    # Local apps
    "accounts",
    "shared",
    "social",
    "posts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ===========================
# REST FRAMEWORK CONFIGURATION
# ===========================
REST_FRAMEWORK = {
    # Default schema class for API documentation
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema', 

    # Default throttle classes (global)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    
    # Default throttle rates (can be overridden per view)
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',           # Anonymous users: 100 req/hour
        'user': '1000/hour',          # Authenticated users: 1000 req/hour
        
        # Custom scopes (per endpoint)
        'register': '3/hour',         # Registration
        'verify': '5/hour',           # Code verification
        'resend': '3/hour',           # Resend code
        'login': '5/min',            # Login attempts
        'forgot_password': '3/hour',  # Password reset request
        'reset_password': '5/hour',   # Password reset execution
        
        # General protection
        'burst': '10/min',            # Burst protection
        'sustained': '1000/day',      # Daily limit
        'authenticated': '100/hour',  # Authenticated endpoints
    },
    
    # Other DRF settings
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # Pagination (optional - for future use)
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,

    # Custom exception handler for throttling
    'EXCEPTION_HANDLER': 'accounts.views.custom_exception_handler',
}

# Simple JWT konfiguratsiyasi
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),      # access token muddati
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),         # refresh token muddati
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# URL Configuration
ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": config("DATABASE_NAME"),
        "USER": config("DATABASE_USER"),
        "PASSWORD": config("DATABASE_PASSWORD"),
        "HOST": config("DATABASE_HOST", default="localhost"),
        "PORT": config("DATABASE_PORT", cast=int),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR/'media/'

# Static files storage (for production)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = 'accounts.User'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ===========================
# CELERY CONFIGURATION
# ===========================

# Redis as message broker
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

# Serialization
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tashkent'

# Task settings
CELERY_RESULT_EXTENDED = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit

# Beat scheduler (for periodic tasks)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Task routing (optional - for multiple queues)
CELERY_TASK_ROUTES = {
    'accounts.tasks.send_*': {'queue': 'emails'},
    'posts.tasks.*': {'queue': 'posts'},
}

# ===========================
# EMAIL CONFIGURATION
# ===========================

# Development - Console backend (kodlarni console'da ko'rish)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Production - SMTP (Gmail example - commented)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')  # your-email@gmail.com
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')  # app password
# DEFAULT_FROM_EMAIL = 'Instagram Clone <noreply@instagram-clone.com>'


# ===========================
# INSTALLED APPS UPDATE
# ===========================

# ===========================
# FRONTEND URL (for password reset links)
# ===========================

FRONTEND_URL = 'http://localhost:3000'  # Development
# FRONTEND_URL = 'https://yourapp.com'  # Production

# ===========================
# SPECTACULAR (API DOCS)
# ===========================
SPECTACULAR_SETTINGS = {
    'TITLE': 'Instagram Clone API',
    'DESCRIPTION': '''
Instagram Clone — REST API dokumentatsiyasi.

**Autentifikatsiya:** `Bearer <access_token>`

Token olish uchun `/api/auth/login/` ga murojaat qiling.
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,   # Token saqlanib qoladi
        'deepLinking': True,
    },
    'TAGS': [
        {'name': 'auth',    'description': '🔐 Register, Login, Logout, Token'},
        {'name': 'users',   'description': '👤 Profile, Avatar, Password'},
        {'name': 'posts',   'description': '📷 Post CRUD, Feed'},
        {'name': 'social',  'description': '👥 Follow, Like, Comment'},
    ],
}
