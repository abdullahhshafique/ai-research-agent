"""
Celery application (opt-in, Phase 3).

Active only when `CELERY_BROKER_URL` is set in the environment.
When unset the project falls back to the in-process ThreadPool queue.
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Import guard: celery is an optional dependency.
try:
    from celery import Celery
except ImportError:  # pragma: no cover
    app = None
else:
    app = Celery('ai_research_agent')
    app.config_from_object('django.conf:settings', namespace='CELERY')
    app.autodiscover_tasks()
