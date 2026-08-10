"""
Dashboard app views.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import time

from apps.accounts.models import User
from apps.research.models import ResearchQuery
from apps.reports.models import GeneratedReport
from apps.collaboration.models import SharedLink
from apps.research.services.job_queue import get_job_queue
from .log_viewer import get_log_viewer


@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard with system statistics."""
    total_users = User.objects.filter(is_active=True).count()
    total_queries = ResearchQuery.objects.count()
    total_reports = GeneratedReport.objects.count()
    total_shares = SharedLink.objects.count()

    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)

    queries_today = ResearchQuery.objects.filter(created_at__date=today).count()
    queries_week = ResearchQuery.objects.filter(created_at__date__gte=last_7_days).count()
    queries_month = ResearchQuery.objects.filter(created_at__date__gte=last_30_days).count()

    success_rate = 0
    completed = ResearchQuery.objects.filter(status='completed').count()
    failed = ResearchQuery.objects.filter(status='failed').count()
    total_done = completed + failed
    if total_done > 0:
        success_rate = round((completed / total_done) * 100, 1)

    avg_processing = ResearchQuery.objects.filter(
        processing_time_ms__isnull=False
    ).aggregate(avg=Avg('processing_time_ms'))['avg']

    top_users = User.objects.annotate(
        query_count=Count('research_queries')
    ).order_by('-query_count')[:10]

    recent_queries = ResearchQuery.objects.select_related('user').order_by('-created_at')[:20]

    daily_stats = list(ResearchQuery.objects.filter(
        created_at__date__gte=last_7_days
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        failed=Count('id', filter=Q(status='failed'))
    ).order_by('date'))

    # Format dates for JSON
    for stat in daily_stats:
        stat['date'] = stat['date'].strftime('%Y-%m-%d')

    # Queue status
    queue = get_job_queue()
    queue_status = queue.get_queue_status()

    context = {
        'total_users': total_users,
        'total_queries': total_queries,
        'total_reports': total_reports,
        'total_shares': total_shares,
        'queries_today': queries_today,
        'queries_week': queries_week,
        'queries_month': queries_month,
        'success_rate': success_rate,
        'avg_processing': round(avg_processing / 1000, 2) if avg_processing else 0,
        'top_users': top_users,
        'recent_queries': recent_queries,
        'daily_stats': daily_stats,
        'queue_status': queue_status,
    }

    return render(request, 'pages/dashboard/admin.html', context)


@staff_member_required
def user_management(request):
    """Admin user management page."""
    users = User.objects.select_related('profile').annotate(
        query_count=Count('research_queries')
    ).order_by('-date_joined')

    return render(request, 'pages/dashboard/users.html', {
        'users': users,
        'roles': ['free', 'premium', 'admin'],
    })


@staff_member_required
def error_logs(request):
    """View structured error logs."""
    viewer = get_log_viewer()

    level = request.GET.get('level', '')
    module = request.GET.get('module', '')
    search = request.GET.get('q', '')
    hours = int(request.GET.get('hours', 24))

    entries = viewer.get_entries(
        level=level or None,
        module=module or None,
        search=search or None,
        hours=hours
    )

    stats = viewer.get_stats(hours=hours)

    return render(request, 'pages/dashboard/error_logs.html', {
        'entries': [e.to_dict() for e in entries],
        'stats': stats,
        'level': level,
        'module': module,
        'search': search,
        'hours': hours,
        'levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    })


@staff_member_required
def log_stats_api(request):
    """AJAX endpoint for real-time log stats."""
    hours = int(request.GET.get('hours', 24))
    viewer = get_log_viewer()
    return JsonResponse(viewer.get_stats(hours=hours))


@staff_member_required
def queue_monitor(request):
    """Job queue monitor page."""
    queue = get_job_queue()
    queue_status = queue.get_queue_status()
    jobs = queue.get_all_jobs()

    # Calculate runtime for each job
    for job in jobs:
        if job['started_at'] and not job['completed_at']:
            job['runtime'] = round(time.time() - job['started_at'], 1)
        elif job['started_at'] and job['completed_at']:
            job['runtime'] = round(job['completed_at'] - job['started_at'], 1)
        else:
            job['runtime'] = 0

    return render(request, 'pages/dashboard/queue_monitor.html', {
        'queue_status': queue_status,
        'jobs': jobs,
    })


@staff_member_required
def queue_api(request):
    """AJAX endpoint for queue status."""
    queue = get_job_queue()
    return JsonResponse(queue.get_queue_status())


# User management API endpoints (moved from accounts/views.py to avoid duplication)
@staff_member_required
@require_POST
def toggle_user_active(request, user_id):
    """Ban/unban a user."""
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return JsonResponse({"status": "error", "message": "Cannot modify yourself"})
    
    target_user.is_active = not target_user.is_active
    target_user.save()
    
    action = "activated" if target_user.is_active else "banned"
    
    return JsonResponse({
        "status": "success",
        "is_active": target_user.is_active,
        "message": f"User {action}"
    })


@staff_member_required
@require_POST
def update_user_role(request, user_id):
    """Promote/demote user role."""
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return JsonResponse({"status": "error", "message": "Cannot modify yourself"})
    
    new_role = request.POST.get('role', 'free')
    if new_role not in ['free', 'premium', 'admin']:
        return JsonResponse({"status": "error", "message": "Invalid role"})
    
    target_user.profile.role = new_role
    target_user.profile.save()
    
    target_user.is_staff = (new_role == 'admin')
    target_user.save()
    
    return JsonResponse({
        "status": "success",
        "role": new_role
    })


@staff_member_required
@require_POST
def update_user_quota(request, user_id):
    """Adjust user quota limits."""
    target_user = get_object_or_404(User, id=user_id)
    
    quota_limit = request.POST.get('quota_limit', type=int)
    if quota_limit and quota_limit > 0:
        target_user.profile.quota_limit = quota_limit
        target_user.profile.save()
        return JsonResponse({"status": "success", "quota_limit": quota_limit})
    
    return JsonResponse({"status": "error", "message": "Invalid quota"})