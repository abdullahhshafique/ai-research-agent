"""
Reports app models.
"""
import os
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.research.models import ResearchQuery


class GeneratedReport(models.Model):
    """
    Stores generated PDF reports.
    """
    query = models.OneToOneField(
        ResearchQuery,
        on_delete=models.CASCADE,
        related_name='generated_report'
    )
    pdf_file_path = models.CharField(max_length=500)
    file_size_bytes = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    cover_title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'generated_report'
    
    def __str__(self):
        return f"Report for {self.query.query_text[:30]}..."
    
    def get_filename(self):
        """Get just the filename from path."""
        return os.path.basename(self.pdf_file_path)
    
    def increment_download(self):
        """Increment download counter."""
        self.download_count += 1
        self.save(update_fields=['download_count'])


class ReportRating(models.Model):
    """User rating & feedback for a generated report (P2 feature)."""
    query = models.OneToOneField(ResearchQuery, on_delete=models.CASCADE, related_name='rating')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='report_ratings')
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])  # 1..5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'report_rating'

    def __str__(self):
        return f"Rating {self.score}/5 on query #{self.query_id}"