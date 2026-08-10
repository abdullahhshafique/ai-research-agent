"""
Phase-4 feature flags (P2 features default OFF; P1 core features default ON).
Toggle via env vars, e.g. FEATURE_REPORT_RATING=False.
"""
import os


def _flag(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes')


FEATURES = {
    'report_rating': _flag('FEATURE_REPORT_RATING', 'True'),
    'public_share': _flag('FEATURE_PUBLIC_SHARE', 'True'),
    'llm_toggle': _flag('FEATURE_LLM_TOGGLE', 'True'),
    'search_depth_toggle': _flag('FEATURE_DEPTH_TOGGLE', 'True'),
    'collaboration_v2': _flag('FEATURE_COLLAB_V2', 'False'),
    'admin_analytics_api': _flag('FEATURE_ADMIN_API', 'False'),
}


def is_enabled(name: str) -> bool:
    return FEATURES.get(name, False)
