from config.feature_flags import FEATURES


def global_flags(request):
    """Expose feature flags and user branding to every template."""
    return {
        'FEATURES': FEATURES,
        'user_theme': getattr(getattr(request.user, 'profile', None), 'theme', 'dark'),
        'user_accent': getattr(getattr(request.user, 'profile', None), 'accent_color', '#3B82F6'),
        'user_logo': getattr(getattr(request.user, 'profile', None), 'logo_url', ''),
    }
