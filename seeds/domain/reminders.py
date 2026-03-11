from datetime import date
from typing import Any, Callable, TypedDict

from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.utils import timezone

from seeds.models import SeedBatch, SeedWishlist


class ReminderQuerysets(TypedDict):
    today: date
    expiring_seeds: QuerySet[SeedBatch]
    low_stock_seeds: QuerySet[SeedBatch]
    wishlist_follow_ups: QuerySet[SeedWishlist]


class ReminderCounts(TypedDict):
    expiring_count: int
    low_stock_count: int
    wishlist_follow_up_count: int
    total_reminders: int


class ReminderRow(TypedDict):
    type: str
    type_label: str
    name: str
    subtitle: str
    value: Any
    action_url: str
    action_label: str


def get_reminder_querysets_for_user(user) -> ReminderQuerysets:
    today = timezone.localdate()
    expiring_30_days = today + timezone.timedelta(days=30)
    user_batches = SeedBatch.objects.filter(seed__user=user).select_related("seed")

    expiring_seeds = user_batches.filter(
        best_before__gte=today,
        best_before__lte=expiring_30_days,
    ).order_by("best_before", "seed__name")
    low_stock_seeds = SeedBatch.objects.none()
    wishlist_follow_ups = SeedWishlist.objects.filter(
        user=user,
        acquired=False,
        follow_up_date__isnull=False,
        follow_up_date__lte=today,
    ).order_by("follow_up_date", "priority")

    return {
        "today": today,
        "expiring_seeds": expiring_seeds,
        "low_stock_seeds": low_stock_seeds,
        "wishlist_follow_ups": wishlist_follow_ups,
    }


def get_reminder_counts_for_user(user) -> ReminderCounts:
    querysets = get_reminder_querysets_for_user(user)
    expiring_count = querysets["expiring_seeds"].count()
    low_stock_count = querysets["low_stock_seeds"].count()
    wishlist_follow_up_count = querysets["wishlist_follow_ups"].count()
    return {
        "expiring_count": expiring_count,
        "low_stock_count": low_stock_count,
        "wishlist_follow_up_count": wishlist_follow_up_count,
        "total_reminders": expiring_count + low_stock_count + wishlist_follow_up_count,
    }


def build_reminder_rows(
    expiring_seeds: QuerySet[SeedBatch],
    low_stock_seeds: QuerySet[SeedBatch],
    wishlist_follow_ups: QuerySet[SeedWishlist],
    reverse: Callable[..., str] = reverse_lazy,
) -> list[ReminderRow]:
    reminder_rows: list[ReminderRow] = []
    for batch in expiring_seeds:
        reminder_rows.append(
            {
                "type": "best_before",
                "type_label": "Best Before",
                "name": batch.seed.name,
                "subtitle": batch.batch_number,
                "value": batch.best_before,
                "action_url": reverse("seed_detail", kwargs={"pk": batch.seed.pk}),
                "action_label": "View Seed",
            }
        )
    for batch in low_stock_seeds:
        reminder_rows.append(
            {
                "type": "low_stock",
                "type_label": "Low Stock",
                "name": batch.seed.name,
                "subtitle": f"{batch.quantity} {batch.get_unit_display()}",
                "value": "Stock needs review",
                "action_url": reverse("seed_detail", kwargs={"pk": batch.seed.pk}),
                "action_label": "Update Stock",
            }
        )
    for item in wishlist_follow_ups:
        reminder_rows.append(
            {
                "type": "wishlist_follow_up",
                "type_label": "Wishlist Follow-up",
                "name": item.name,
                "subtitle": item.variety or "-",
                "value": item.follow_up_date,
                "action_url": reverse("wishlist_update", kwargs={"pk": item.pk}),
                "action_label": "Open Wishlist",
            }
        )
    return reminder_rows
