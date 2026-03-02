from django.contrib.auth import get_user_model
from django.core.cache import cache
from django_huey import db_task

from .reminders import get_reminder_counts_for_user

REMINDER_COUNTS_CACHE_KEY = "seed_reminder_counts:{user_id}"
REMINDER_COUNTS_CACHE_TTL = 300


def _cache_key(user_id: int) -> str:
    return REMINDER_COUNTS_CACHE_KEY.format(user_id=user_id)


def refresh_reminder_counts_cache(user_id: int):
    user = get_user_model().objects.filter(pk=user_id).first()
    if not user:
        return None
    counts = get_reminder_counts_for_user(user)
    cache.set(_cache_key(user_id), counts, REMINDER_COUNTS_CACHE_TTL)
    return counts


@db_task()
def refresh_reminder_counts_cache_async(user_id: int):
    return refresh_reminder_counts_cache(user_id)


def get_cached_or_live_reminder_counts(user):
    counts = cache.get(_cache_key(user.id))
    if counts is not None:
        return counts
    counts = get_reminder_counts_for_user(user)
    cache.set(_cache_key(user.id), counts, REMINDER_COUNTS_CACHE_TTL)
    return counts
