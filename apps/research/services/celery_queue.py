"""
Optional Celery-backed job queue (Phase 3).

Used only when `USE_CELERY` is True in settings. The in-process
`ResearchJobQueue` remains the fallback and keeps the app free-tier friendly.
"""
import logging
from .job_queue import get_job_queue  # fallback
from .pipeline import execute_research_pipeline

logger = logging.getLogger(__name__)

USE_CELERY = False
try:
    from django.conf import settings
    USE_CELERY = getattr(settings, 'USE_CELERY', False)
except Exception:  # pragma: no cover
    pass


if USE_CELERY:
    from celery import shared_task  # noqa: E402

    @shared_task(bind=True)
    def run_research_task(self, query_id: int, user_id: int):
        """Celery task wrapper around the pipeline."""
        from apps.research.models import ResearchQuery
        from apps.accounts.models import User
        query = ResearchQuery.objects.get(id=query_id)
        user = User.objects.get(id=user_id)
        return execute_research_pipeline(query, user)


def submit_query(query_id: int, user_id: int):
    """Submit a research query to Celery if enabled, else to the local queue."""
    if USE_CELERY:
        return run_research_task.delay(query_id, user_id)
    # fallback: reuse the existing thread-pool interface via a thin wrapper
    from apps.research.models import ResearchQuery
    from apps.accounts.models import User
    q = ResearchQuery.objects.get(id=query_id)
    u = User.objects.get(id=user_id)
    queue = get_job_queue()
    return queue.submit(query_id, execute_research_pipeline, q, u)
