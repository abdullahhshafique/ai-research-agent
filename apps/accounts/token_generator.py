"""
Tokens for email verification (Phase 3).
"""
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash(self, user, timestamp):
        # include email + verification state so links invalidate after use
        profile = getattr(user, 'profile', None)
        verified = getattr(profile, 'email_verified', False)
        return f"{user.pk}:{user.email}:{verified}:{timestamp}"


email_verification_token = EmailVerificationTokenGenerator()
