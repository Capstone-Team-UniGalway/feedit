"""
Django settings for app project.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/

Quick-start development settings - unsuitable for production
See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/
"""

import os
from pathlib import Path
import environ

# Initialize environ first
env = environ.Env(DEBUG=(bool, False))

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env in development, otherwise use system environment variables
ENVIRONMENT = env("DJANGO_ENV", default="development")

# Loads from .env file on development
if ENVIRONMENT == "development":
    environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Security & Debug
SECRET_KEY = env("SECRET_KEY", default="super-secret-key")
DEBUG = env.bool("DEBUG", default=False)
# Allowed Hosts
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])


# Database Configuration
if ENVIRONMENT == "development":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
    # Email settings for development
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    # SMTP settings for production (these will be used when DJANGO_ENV is not 'development')
    EMAIL_HOST = "smtp.mailersend.net"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = "MS_psx0J8@feedit.online"
    EMAIL_HOST_PASSWORD = "mssp.ceCiaq5.pr9084z608mlw63d.fZT2kLf"
    DEFAULT_FROM_EMAIL = "noreply@feedit.online"
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT"),
        }
    }
    # Email settings for production
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST", default="smtp.mailersend.net")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="MS_psx0J8@feedit.online")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="mssp.ceCiaq5.pr9084z608mlw63d.fZT2kLf")
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@feedit.online")

    # Security settings for production
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# Application definition
SITE_ID = 1
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # installed
    "django_extensions",
    "allauth",
    "allauth.account",
    "allauth.mfa",
    "django_cotton",
    "django_ckeditor_5",
    "widget_tweaks",
    # created
    "accounts",
    "companies",
    "threads",
    "reviews",
    "requests",
    "notifications",
    "secure_files",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.tz",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "builtins": [
                "django_cotton.templatetags.cotton",
                "app.templatetags.cotton_fixes",
            ],
        },
    },
]
COTTON_DIR = "components"

WSGI_APPLICATION = "app.wsgi.application"


SESSION_SERIALIZER = "app.serializers.SafeEnumJSONSerializer"

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTHENTICATION_BACKENDS = [
    # Custom soft-delete aware logic extending on allauth logic
    "accounts.backends.SoftDeleteAwareBackend",
]

# Use email as the sole login identifier
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
# Auth method and fields
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = [
    "first_name",
    "last_name",
    "email*",
    "password1*",
    "password2*",
    "type",
]

# Email confirmation flow
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_URL = "account_confirm_email"  # name of the path in urls.py
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/dashboard"
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/account/confirm-email/success/"

# Password reset
ACCOUNT_PASSWORD_RESET_REDIRECT_URL = "/account/auth"
ACCOUNT_ADAPTER = "accounts.adapter.CustomAccountAdapter"

# MFA
ACCOUNT_MFA_ENABLED = True
ACCOUNT_MFA_ENFORCE_AFTER_LOGIN = True
MFA_ADAPTER = "allauth.mfa.adapter.DefaultMFAAdapter"

# Redirect after login/logout
LOGIN_REDIRECT_URL = "/dashboard"
LOGOUT_REDIRECT_URL = "/account/auth"
LOGIN_URL = "/account/auth"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",  # noqa: E501
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/assets/"
# Run collectstatic to gather all static files into STATIC_ROOT
# python manage.py collectstatic

# Use WhiteNoise for static file handling in production
# without the need of a separate server (apache/nginx)
if ENVIRONMENT == "production":
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

# CKEditor 5 Configuration
customColorPalette = [
    {"color": "hsl(4, 90%, 58%)", "label": "Red"},
    {"color": "hsl(340, 82%, 52%)", "label": "Pink"},
    {"color": "hsl(291, 64%, 42%)", "label": "Purple"},
    {"color": "hsl(262, 52%, 47%)", "label": "Deep Purple"},
    {"color": "hsl(231, 48%, 48%)", "label": "Indigo"},
    {"color": "hsl(207, 90%, 54%)", "label": "Blue"},
    {"color": "hsl(199, 98%, 48%)", "label": "Light Blue"},
    {"color": "hsl(187, 100%, 42%)", "label": "Cyan"},
    {"color": "hsl(174, 100%, 29%)", "label": "Teal"},
    {"color": "hsl(122, 39%, 49%)", "label": "Green"},
    {"color": "hsl(88, 50%, 53%)", "label": "Light Green"},
    {"color": "hsl(66, 70%, 54%)", "label": "Lime"},
    {"color": "hsl(49, 98%, 60%)", "label": "Yellow"},
    {"color": "hsl(45, 100%, 51%)", "label": "Amber"},
    {"color": "hsl(36, 100%, 50%)", "label": "Orange"},
    {"color": "hsl(14, 100%, 57%)", "label": "Deep Orange"},
    {"color": "hsl(15, 75%, 43%)", "label": "Brown"},
    {"color": "hsl(0, 0%, 62%)", "label": "Grey"},
    {"color": "hsl(200, 18%, 46%)", "label": "Blue Grey"},
    {"color": "hsl(200, 18%, 26%)", "label": "Dark Grey"},
]

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "link",
            "bulletedList",
            "numberedList",
            "|",
            "outdent",
            "indent",
            "|",
            "blockQuote",
            "insertTable",
            "|",
            "undo",
            "redo",
        ],
    },
    "extends": {
        "blockToolbar": [
            "paragraph",
            "heading1",
            "heading2",
            "heading3",
            "|",
            "bulletedList",
            "numberedList",
            "|",
            "blockQuote",
        ],
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "strikethrough",
            "underline",
            "code",
            "subscript",
            "superscript",
            "highlight",
            "|",
            "bulletedList",
            "numberedList",
            "todoList",
            "|",
            "outdent",
            "indent",
            "|",
            "link",
            "blockQuote",
            "insertTable",
            "mediaEmbed",
            "codeBlock",
            "|",
            "horizontalLine",
            "pageBreak",
            "|",
            "sourceEditing",
        ],
        "image": {
            "toolbar": [
                "imageTextAlternative",
                "imageTitle",
                "|",
                "imageStyle:inline",
                "imageStyle:block",
                "imageStyle:side",
                "|",
                "linkImage",
            ],
            "styles": [
                "full",
                "side",
                "alignLeft",
                "alignRight",
                "alignCenter",
                "alignBlockLeft",
                "alignBlockRight",
                "block",
                "inline",
            ],
        },
        "table": {
            "contentToolbar": [
                "tableColumn",
                "tableRow",
                "mergeTableCells",
                "tableProperties",
                "tableCellProperties",
            ],
            "tableProperties": {
                "borderColors": customColorPalette,
                "backgroundColors": customColorPalette,
            },
            "tableCellProperties": {
                "borderColors": customColorPalette,
                "backgroundColors": customColorPalette,
            },
        },
        "heading": {
            "options": [
                {
                    "model": "paragraph",
                    "title": "Paragraph",
                    "class": "ck-heading_paragraph",
                },
                {
                    "model": "heading1",
                    "view": "h1",
                    "title": "Heading 1",
                    "class": "ck-heading_heading1",
                },
                {
                    "model": "heading2",
                    "view": "h2",
                    "title": "Heading 2",
                    "class": "ck-heading_heading2",
                },
                {
                    "model": "heading3",
                    "view": "h3",
                    "title": "Heading 3",
                    "class": "ck-heading_heading3",
                },
            ]
        },
    },
    "list": {
        "properties": {
            "styles": "true",
            "startIndex": "true",
            "reversed": "true",
        }
    },
}

# Media files configuration for CKEditor uploads
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
# Use default storage instead of DummyStorage which doesn't exist in this version
# CKEDITOR_5_FILE_STORAGE = "django_ckeditor_5.storages.DummyStorage"
CKEDITOR_5_UPLOAD_PATH = "uploads/"
