"""
Management command to clean up old PDF files and cache entries.
Run with: python manage.py cleanup
"""
import os
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from apps.reports.models import GeneratedReport
from apps.research.models import ResearchQuery
from apps.utils.search_cache import SearchCache

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old PDF files, expired cache entries, and stale data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--pdf-days',
            type=int,
            default=30,
            help='Delete PDFs older than this many days (default: 30)',
        )
        parser.add_argument(
            '--cache-days',
            type=int,
            default=7,
            help='Delete cache entries older than this many days (default: 7)',
        )
        parser.add_argument(
            '--failed-days',
            type=int,
            default=7,
            help='Delete failed queries older than this many days (default: 7)',
        )
        parser.add_argument(
            '--force-cache',
            action='store_true',
            help='Force clear ALL cache entries, not just expired',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        pdf_days = options['pdf_days']
        cache_days = options['cache_days']
        failed_days = options['failed_days']
        force_cache = options['force_cache']
        
        self.stdout.write(self.style.NOTICE(f"Starting cleanup (dry-run: {dry_run})"))
        
        # 1. Clean old PDF files
        self._cleanup_pdfs(pdf_days, dry_run)
        
        # 2. Clean expired cache
        self._cleanup_cache(cache_days, dry_run, force_cache)
        
        # 3. Clean old failed queries
        self._cleanup_failed_queries(failed_days, dry_run)
        
        self.stdout.write(self.style.SUCCESS("Cleanup complete!"))
    
    def _cleanup_pdfs(self, days: int, dry_run: bool):
        """Remove PDF files older than specified days."""
        cutoff = timezone.now() - timedelta(days=days)
        old_reports = GeneratedReport.objects.filter(created_at__lt=cutoff)
        
        count = 0
        for report in old_reports:
            if report.pdf_file_path and os.path.exists(report.pdf_file_path):
                if not dry_run:
                    try:
                        os.remove(report.pdf_file_path)
                        logger.info(f"Deleted PDF: {report.pdf_file_path}")
                    except OSError as e:
                        logger.error(f"Failed to delete PDF: {e}")
                        continue
                count += 1
        
        if not dry_run:
            old_reports.delete()
        
        self.stdout.write(f"PDFs {'would be' if dry_run else ''} deleted: {count}")
    
    def _cleanup_cache(self, days: int, dry_run: bool, force: bool = False):
        """Clear expired search cache entries."""
        cache = SearchCache()
        if not dry_run:
            # FIXED: Use force parameter to clear all if requested
            cleared = cache.clear(force=force)
            self.stdout.write(f"Cache entries cleared: {cleared}")
        else:
            stats = cache.get_stats()
            self.stdout.write(f"Cache entries (would clear expired): {stats['expired_entries']}")
    
    def _cleanup_failed_queries(self, days: int, dry_run: bool):
        """Remove old failed research queries."""
        cutoff = timezone.now() - timedelta(days=days)
        old_failed = ResearchQuery.objects.filter(
            status='failed',
            created_at__lt=cutoff
        )
        
        count = old_failed.count()
        if not dry_run:
            old_failed.delete()
        
        self.stdout.write(f"Failed queries {'would be' if dry_run else ''} deleted: {count}")