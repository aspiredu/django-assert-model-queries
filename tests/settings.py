import os

SECRET_KEY = "NOTASECRET"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    },
    "mysql": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "django_mysql",
        "USER": os.environ.get("MYSQL_USER", ""),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD", ""),
        "HOST": os.environ.get("MYSQL_HOST", ""),
        "PORT": os.environ.get("MYSQL_PORT", ""),
        "OPTIONS": {"charset": "utf8mb4"},
        "TEST": {"COLLATION": "utf8mb4_general_ci", "CHARSET": "utf8mb4"},
    }
}

TIME_ZONE = "UTC"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "tests.testapp",
]

USE_TZ = True
