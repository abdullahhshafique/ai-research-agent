"""
Reports app views.
Handles PDF generation, preview, download, streaming, sharing, and regeneration.
"""
import os
import re
import logging
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib import messages
from django.urls import reverse

from apps.research.models import ResearchQuery
from .services.report_builder import ReportBuilder
from .services.pdf_engine import PDFExporter

logger = logging.getLogger(__name__)


def _get_user_branding(request):
    """Extract accent color and logo from user profile."""
    accent_color = "#2563EB"
    logo_url = None
    if hasattr(request.user, "profile"):
        if request.user.profile.accent_color:
            accent_color = request.user.profile.accent_color
        if request.user.profile.logo_url:
            logo_url = request.user.profile.logo_url
    return accent_color, logo_url


def _build_safe_filename(research_query_text, suffix=""):
    """Create a filesystem-safe filename from query text."""
    safe_query = re.sub(r"[^\w\s-]", "", research_query_text[:40]).strip()
    safe_query = re.sub(r"[-\s]+", "-", safe_query)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if suffix:
        return f"AI_Research_Report_{safe_query}_{suffix}_{timestamp}.pdf"
    return f"AI_Research_Report_{safe_query}_{timestamp}.pdf"


def _get_reports_dir():
    """Get or create the reports directory."""
    reports_dir = os.path.join(settings.MEDIA_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


def _cleanup_old_reports(research_id, exclude_path=None):
    """Remove old PDF files for a given research ID."""
    reports_dir = _get_reports_dir()
    deleted = 0
    if not os.path.exists(reports_dir):
        return deleted

    for filename in os.listdir(reports_dir):
        # Match files associated with this research
        if (filename.startswith(f"research_{research_id}_") or
            filename.startswith(f"temp_{research_id}_") or
            (filename.startswith("AI_Research_Report_") and f"_rid{research_id}_" in filename)):
            file_path = os.path.join(reports_dir, filename)
            if exclude_path and file_path == exclude_path:
                continue
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete old report {filename}: {e}")
    return deleted


@login_required
def report_preview(request, pk):
    """Show HTML preview of the research report."""
    research = get_object_or_404(ResearchQuery, pk=pk, user=request.user)
    if research.status != "completed":
        messages.warning(request, "This report is not ready yet.")
        return redirect("research:research_status", pk=pk)

    try:
        report_md = ReportBuilder.from_research_query(research)
    except Exception as e:
        logger.error(f"Failed to build report preview: {e}")
        messages.error(request, "Failed to generate report preview.")
        return redirect("research:research_status", pk=pk)

    return render(request, "pages/reports/preview.html", {
        "research": research,
        "report": report_md
    })


@login_required
def report_download(request, pk):
    """Generate and download PDF as attachment."""
    research = get_object_or_404(ResearchQuery, pk=pk, user=request.user)
    if research.status != "completed":
        messages.warning(request, "Report not ready.")
        return redirect("research:research_status", pk=pk)

    try:
        report_md = ReportBuilder.from_research_query(research)

        filename = _build_safe_filename(research.query_text, suffix=f"rid{research.id}")
        reports_dir = _get_reports_dir()
        output_path = os.path.join(reports_dir, filename)

        accent_color, logo_url = _get_user_branding(request)

        exporter = PDFExporter()
        pdf_path = exporter.export(
            markdown_content=report_md,
            research=research,
            accent_color=accent_color,
            logo_url=logo_url,
            output_path=output_path
        )

        if not pdf_path or not os.path.exists(pdf_path):
            messages.error(request, "Failed to generate PDF.")
            return redirect("research:research_status", pk=pk)

        # Clean up old reports for this research (keep only latest)
        _cleanup_old_reports(research.id, exclude_path=pdf_path)

        response = FileResponse(
            open(pdf_path, "rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=filename
        )
        response["Content-Length"] = os.path.getsize(pdf_path)
        return response

    except Exception as e:
        logger.error(f"PDF download failed: {e}", exc_info=True)
        messages.error(request, f"Failed to generate PDF: {str(e)}")
        return redirect("research:research_status", pk=pk)


@login_required
def report_stream(request, pk):
    """Generate and stream PDF inline for browser preview."""
    research = get_object_or_404(ResearchQuery, pk=pk, user=request.user)
    if research.status != "completed":
        raise Http404("Report not ready")

    try:
        report_md = ReportBuilder.from_research_query(research)

        filename = _build_safe_filename(research.query_text, suffix=f"rid{research.id}")
        reports_dir = _get_reports_dir()
        output_path = os.path.join(reports_dir, f"temp_{research.id}_{filename}")

        accent_color, logo_url = _get_user_branding(request)

        exporter = PDFExporter()
        pdf_path = exporter.export(
            markdown_content=report_md,
            research=research,
            accent_color=accent_color,
            logo_url=logo_url,
            output_path=output_path
        )

        if not pdf_path or not os.path.exists(pdf_path):
            raise Http404("PDF generation failed")

        response = FileResponse(
            open(pdf_path, "rb"),
            content_type="application/pdf"
        )
        response["Content-Disposition"] = 'inline; filename="' + filename + '"'
        response["Content-Length"] = os.path.getsize(pdf_path)
        return response

    except Exception as e:
        logger.error(f"PDF stream failed: {e}", exc_info=True)
        raise Http404("Failed to generate PDF")


@login_required
def report_delete(request, pk):
    """Delete all PDF files associated with a research query."""
    research = get_object_or_404(ResearchQuery, pk=pk, user=request.user)
    deleted_count = _cleanup_old_reports(research.id)

    if deleted_count > 0:
        messages.success(request, f"Deleted {deleted_count} report file(s).")
    else:
        messages.info(request, "No report files found to delete.")
    return redirect("research:research_status", pk=pk)


@login_required
@require_POST
def report_rate(request, pk):
    """Save or update a 1-5 star rating + feedback for a report (P2 feature)."""
    research = get_object_or_404(ResearchQuery, pk=pk, user=request.user)
    if research.status != "completed":
        messages.warning(request, "Reports can only be rated after completion.")
        return redirect("reports:report_preview", pk=pk)

    from config.feature_flags import is_enabled
    if not is_enabled("report_rating"):
        messages.info(request, "Report rating is not enabled.")
        return redirect("reports:report_preview", pk=pk)

    try:
        score = int(request.POST.get("score", 0))
    except (TypeError, ValueError):
        score = 0

    if score not in (1, 2, 3, 4, 5):
        messages.error(request, "Score must be between 1 and 5.")
        return redirect("reports:report_preview", pk=pk)

    from .models import ReportRating
    ReportRating.objects.update_or_create(
        query=research, user=request.user,
        defaults={"score": score, "comment": request.POST.get("comment", "").strip()},
    )
    messages.success(request, "Thanks for the feedback!")
    return redirect("reports:report_preview", pk=pk)


@login_required
def report_share(request, pk):
    """Create or retrieve a shareable link for the report."""
    research = get_object_or_404(ResearchQuery, pk=pk, user=request.user)
    if research.status != "completed":
        messages.warning(request, "Cannot share an incomplete report.")
        return redirect("research:research_status", pk=pk)

    try:
        from apps.collaboration.models import SharedLink

        if not hasattr(research, "generated_report"):
            messages.error(request, "No report exists yet to share.")
            return redirect("research:research_status", pk=pk)

        report = research.generated_report
        share_link = SharedLink.objects.filter(
            report=report, is_public=True
        ).first()

        if not share_link:
            share_link = SharedLink.objects.create(
                report=report,
                token=SharedLink.generate_token(),
                is_public=True
            )

        share_url = request.build_absolute_uri(
            reverse("collaboration:share_access", kwargs={"token": share_link.token})
        )
        messages.success(request, f"Share link created: {share_url}")
    except Exception as e:
        logger.error(f"Failed to create share link: {e}")
        messages.error(request, "Failed to create share link.")
    return redirect("research:research_status", pk=pk)


@login_required
def report_regenerate(request, pk):
    """Clear old PDFs and redirect to download to regenerate."""
    research = get_object_or_404(ResearchQuery, pk=pk, user=request.user)
    if research.status != "completed":
        messages.warning(request, "Cannot regenerate an incomplete report.")
        return redirect("research:research_status", pk=pk)

    _cleanup_old_reports(research.id)
    messages.info(request, "Regenerating your report...")
    return redirect("reports:report_download", pk=pk)