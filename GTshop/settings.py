from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-1234567890abcdef1234567890abcdef'

DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    'carts',
    'django_bootstrap5',
    'accounts',
    'blog',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'GTshop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'GTshop.context_processors.cart_count',
                'GTshop.context_processors.lang_list',
            ],
        },
    },
]

WSGI_APPLICATION = 'GTshop.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Ngôn ngữ ─────────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'vi'

LANGUAGES = [
    ('vi',      _('Tiếng Việt')),
    ('en',      _('English')),
    ('zh-hans', _('中文')),
    ('ja',      _('日本語')),
    ('ru',      _('Русский')),
    ('km',      _('ភាសាខ្មែរ')),
]

USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'Asia/Ho_Chi_Minh'

LOCALE_PATHS = [BASE_DIR / 'locale']

# ── Language cookie: LocaleMiddleware đọc cookie thay vì URL prefix ──
LANGUAGE_COOKIE_NAME     = 'django_language'
LANGUAGE_COOKIE_AGE      = 365 * 24 * 60 * 60   # 1 năm
LANGUAGE_COOKIE_HTTPONLY = False
LANGUAGE_COOKIE_SAMESITE = 'Lax'

# Cookie ngôn ngữ
LANGUAGE_COOKIE_NAME = 'django_language'
LANGUAGE_COOKIE_AGE = 365 * 24 * 60 * 60  # 1 năm
LANGUAGE_COOKIE_SAMESITE = 'Lax'

# ─── Static & Media ───────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ─── Auth ─────────────────────────────────────────────────────────────────────
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'store:home'
LOGOUT_REDIRECT_URL = 'store:home'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
