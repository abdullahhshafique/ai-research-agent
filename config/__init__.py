# Django configuration package

# Expose the Celery app when celery is installed so `celery -A config` discovers it.
try:
    from .celery import app as celery_app
except Exception:  # celery not installed or broker misconfigured
    celery_app = None

__all__ = ('celery_app',)
