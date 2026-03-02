from django.conf import settings
from django.core.cache import cache

from .tasks import (
    get_cached_or_live_reminder_counts,
    refresh_reminder_counts_cache_async,
)


def reminder_navigation(request):
    if not request.user.is_authenticated:
        return {"reminder_nav_count": 0}

    counts = get_cached_or_live_reminder_counts(request.user)
    lock_key = f"seed_reminder_refresh_lock:{request.user.id}"

    try:
        # Avoid enqueueing on every request while still keeping cache warm.
        if settings.ENABLE_DJANGO_HUEY and cache.add(lock_key, "1", 60):
            refresh_reminder_counts_cache_async(request.user.id)
    except Exception:
        # If Redis/worker is unavailable, navigation can still use live count.
        pass

    return {"reminder_nav_count": counts["total_reminders"]}
