"""
User account models.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """
    Custom user model with email as required field.
    """
    email = models.EmailField(unique=True, blank=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


class Profile(models.Model):
    """
    Extended user profile with preferences and quotas.
    """
    ROLE_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('admin', 'Admin'),
    ]

    THEME_CHOICES = [
        ('dark', 'Dark'),
        ('light', 'Light'),
    ]

    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='free'
    )
    quota_limit = models.IntegerField(default=10)
    used_quota = models.IntegerField(default=0)
    quota_reset_at = models.DateTimeField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    theme = models.CharField(
        max_length=10, 
        choices=THEME_CHOICES, 
        default='dark'
    )
    accent_color = models.CharField(max_length=7, default='#3B82F6')
    logo_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_profile'

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def _ensure_reset_at(self):
        """Initialize quota_reset_at if not set."""
        if not self.quota_reset_at:
            self.quota_reset_at = timezone.now() + timedelta(hours=1)
            self.save(update_fields=['quota_reset_at'])

    def reset_quota_if_needed(self):
        """Reset used quota if hour has passed."""
        self._ensure_reset_at()
        now = timezone.now()
        if now >= self.quota_reset_at:
            self.used_quota = 0
            self.quota_reset_at = now + timedelta(hours=1)
            self.save(update_fields=['used_quota', 'quota_reset_at'])

    def can_make_query(self) -> bool:
        """Check if user has remaining quota."""
        self.reset_quota_if_needed()
        return self.used_quota < self.quota_limit

    def has_quota(self):
        """Alias for can_make_query for middleware compatibility."""
        return self.can_make_query()

    def increment_quota(self):
        """Increment used quota after successful query submission."""
        self.reset_quota_if_needed()
        self.used_quota += 1
        self.save(update_fields=['used_quota'])

    def get_quota_status(self):
        """Return quota status dict for API responses."""
        self.reset_quota_if_needed()
        return {
            'used': self.used_quota,
            'limit': self.quota_limit,
            'remaining': max(0, self.quota_limit - self.used_quota),
            'resets_at': self.quota_reset_at.isoformat() if self.quota_reset_at else None,
        }