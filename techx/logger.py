import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

LOG_DIR = os.path.join(BASE_DIR, "logging")
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%Y/%m/%d %H:%M:%S",
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": [
                "require_debug_false",
            ],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
        "default": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "techx.log"),
            "formatter": "standard",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 10,
            "delay": True,
        },
        "request_handler": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "request.log"),
            "formatter": "standard",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 10,  # Keep 10 backup files
            "delay": True,
        },
    },
    "loggers": {
        "": {
            "handlers": ["default", "mail_admins"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["request_handler"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
