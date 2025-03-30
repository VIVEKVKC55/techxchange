import os

# Define log directory
LOG_DIR = "/tmp/logs"  # ✅ Use /tmp since Vercel allows writing here

# Ensure the directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# Define logging settings
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s"
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "django.log"),  # ✅ Use writable location
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "DEBUG",
    },
}
