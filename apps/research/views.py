"""
Research app views.
"""
import json
import time
import logging
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.db import transaction

from .models import ResearchQuery, Source
from .services.search import SearchAgent
from .services.chunker import TextChunker
from .services.summarizer import Summarizer
from .services.pipeline import execute_research_pipeline
from .services.job_queue import get_job_queue, JobStatus
from apps.utils.validators import validate_query

logger = logging.getLogger(__name__)


@login_required
def research_submit(request):
    """Research submission form."""
    if request.method == 'POST':
        query_text = request.POST.get('query', '').strip()
        search_depth = request.POST.get('search_depth', 'advanced')
        max_results = int(request.POST.get('max_results', 5))
        llm_model = request.POST.get('llm_model', 'groq')
        version_of = request.POST.get('version_of', '')

        is_valid, error_msg = validate_query(query_text, settings.MAX_QUERY_LENGTH)
        if not is_valid:
            messages.error(request, error_msg)
            return redirect('research:research_submit')

        if not request.user.profile.has_quota():
            messages.error(request, 'You have exceeded your hourly quota. Upgrade to Premium for more.')
            return redirect('research:research_submit')

        # Check if this is a new version of existing query
        if version_of:
            try:
                parent = ResearchQuery.objects.get(pk=version_of, user=request.user)
                research = parent.create_new_version()
                research.search_depth = search_depth
                research.max_results = max_results
                research.llm_model = llm_model
                research.save()
                messages.success(request, f'New version {research.version} created! Processing...')
            except ResearchQuery.DoesNotExist:
                messages.error(request, 'Original query not found.')
                return redirect('research:research_submit')
        else:
            research = ResearchQuery.objects.create(
                user=request.user,
                query_text=query_text,
                search_depth=search_depth,
                max_results=max_results,
                llm_model=llm_model,
                status='pending'
            )
            messages.success(request, 'Research query submitted! Processing...')

        # Increment quota
        request.user.profile.increment_quota()

        # Submit to job queue for async processing
        queue = get_job_queue()
        job = queue.submit(
            query_id=research.id,
            func=execute_research_pipeline,
            query=research,
            user=request.user
        )

        # Store job ID on the research query for tracking
        research.status = 'processing'
        research.started_at = timezone.now()
        research.save(update_fields=['status', 'started_at'])

        return redirect('research:research_status', pk=research.id)

    # Check for template parameter
    template_id = request.GET.get('template', '')
    initial_query = ''
    if template_id:
        from apps.templates_app.models import ResearchTemplate
        try:
            template = ResearchTemplate.objects.get(pk=template_id)
            if template.is_public or template.user == request.user:
                initial_query = template.query_pattern
        except ResearchTemplate.DoesNotExist:
            pass

    return render(request, 'pages/research/submit.html', {
        'max_query_length': settings.MAX_QUERY_LENGTH,
        'default_max_results': settings.MAX_RESULTS,
        'initial_query': initial_query,
    })


@login_required
def research_status(request, pk):
    """View research status and results."""
    research = get_object_or_404(ResearchQuery, pk=pk, user=request.user)

    # Get version history
    version_history = research.get_version_history() if research.parent_query or research.versions.exists() else [research]

    # Get job info if processing
    job_info = None
    if research.status == 'processing':
        queue = get_job_queue()
        job = queue.get_job_by_query(research.id)
        if job:
            job_info = job.to_dict()

    context = {
        'research': research,
        'sources': [],
        'version_history': version_history,
        'job_info': job_info,
    }

    if research.raw_sources:
        try:
            sources_data = research.raw_sources if isinstance(research.raw_sources, (list, dict)) else json.loads(research.raw_sources)
            context['sources'] = sources_data
        except (json.JSONDecodeError, TypeError):
            pass

    return render(request, 'pages/research/status.html', context)


@login_required
def research_stream(request, pk):
    """
    SSE stream for research progress via job queue.
    FIXED: Removed Connection: keep-alive header to prevent wsgiref AssertionError.
    """
    try:
        research = ResearchQuery.objects.get(pk=pk, user=request.user)
    except ResearchQuery.DoesNotExist:
        def error_stream():
            yield "event: error\ndata: " + json.dumps({"message": "Research not found or access denied"}) + "\n\n"
        return StreamingHttpResponse(
            error_stream(),
            content_type='text/event-stream'
        )

    queue = get_job_queue()
    job = queue.get_job_by_query(pk)

    if not job:
        # Job not found in queue - may have completed or failed
        if research.status == 'completed':
            def complete_stream():
                yield _sse_event('complete', {
                    'redirect': f'/research/{pk}/',
                    'message': 'Research already completed.'
                })
            return StreamingHttpResponse(complete_stream(), content_type='text/event-stream')
        elif research.status == 'failed':
            def fail_stream():
                yield _sse_event('error', {'message': research.error_message or 'Research failed.'})
            return StreamingHttpResponse(fail_stream(), content_type='text/event-stream')
        else:
            def pending_stream():
                yield _sse_event('status', {
                    'stage': 'pending',
                    'progress': 0,
                    'message': 'Waiting in queue...'
                })
            return StreamingHttpResponse(pending_stream(), content_type='text/event-stream')

    def event_stream():
        """Stream job progress updates."""
        last_progress = -1
        last_message = ''

        while True:
            job.refresh_from_queue()
            current = job.to_dict()

            # Only send if progress changed
            if current['progress'] != last_progress or current['message'] != last_message:
                yield _sse_event('status', {
                    'stage': current['stage'],
                    'progress': current['progress'],
                    'message': current['message'],
                    'status': current['status']
                })
                last_progress = current['progress']
                last_message = current['message']

            # Check completion
            if current['status'] in ('completed', 'failed', 'cancelled'):
                if current['status'] == 'completed':
                    yield _sse_event('complete', {
                        'redirect': f'/research/{pk}/',
                        'message': 'Research complete!'
                    })
                else:
                    yield _sse_event('error', {
                        'message': current.get('error', 'Research failed.')
                    })
                break

            time.sleep(0.5)

    # FIX: Removed Connection: keep-alive header to fix AssertionError
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    # DO NOT add Connection: keep-alive header - it causes AssertionError in wsgiref
    # response['Connection'] = 'keep-alive'  # <-- REMOVED

    return response


def _sse_event(event_type: str, data: dict) -> str:
    """Helper to format SSE events with proper JSON serialization."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@login_required
@require_http_methods(['POST'])
def research_retry(request, pk):
    """Retry a failed research query - creates new version."""
    research = get_object_or_404(ResearchQuery, pk=pk, user=request.user)

    if research.status != 'failed':
        messages.warning(request, 'Only failed queries can be retried.')
        return redirect('research:research_status', pk=pk)

    new_version = research.create_new_version()
    new_version.status = 'pending'
    new_version.error_message = None
    new_version.save()

    # Submit to job queue
    queue = get_job_queue()
    queue.submit(
        query_id=new_version.id,
        func=execute_research_pipeline,
        query=new_version,
        user=request.user
    )

    new_version.status = 'processing'
    new_version.started_at = timezone.now()
    new_version.save(update_fields=['status', 'started_at'])

    messages.success(request, f'Retry queued as version {new_version.version}!')
    return redirect('research:research_status', pk=new_version.id)


@login_required
@require_http_methods(['POST'])
def create_version(request, pk):
    """Create a new version of a completed query."""
    research = get_object_or_404(ResearchQuery, pk=pk, user=request.user)

    if research.status != 'completed':
        messages.warning(request, 'Only completed queries can be versioned.')
        return redirect('research:research_status', pk=pk)

    new_version = research.create_new_version()
    messages.success(request, f'Version {new_version.version} created! You can modify settings and re-run.')
    return redirect('research:research_status', pk=new_version.id)


@login_required
@require_http_methods(['POST'])
def research_cancel(request, query_id):
    """Cancel a pending or processing research query."""
    research = get_object_or_404(ResearchQuery, pk=query_id, user=request.user)

    if research.status not in ['pending', 'processing']:
        messages.warning(request, 'Only pending or processing queries can be cancelled.')
        return redirect('research:research_status', pk=query_id)

    # Cancel job in queue if exists
    queue = get_job_queue()
    job = queue.get_job_by_query(query_id)
    if job:
        queue.cancel(job.id)

    research.status = 'failed'
    research.error_message = 'Cancelled by user.'
    research.save()

    messages.success(request, 'Research query cancelled successfully.')
    return redirect('research:research_status', pk=query_id)