from typing import TypedDict

from django.db.models import Count, F, OuterRef, Q, QuerySet, Subquery
from django.utils import timezone

from seeds.domain.reminders import get_reminder_counts_for_user
from seeds.models import Seed, SeedBatch, SeedWishlist


class SeedFilters(TypedDict):
    q: str
    category: str
    source: str


class WishlistFilters(TypedDict):
    q: str
    priority: str
    status: str


def get_user_seed_queryset(user) -> QuerySet[Seed]:
    latest_batch = SeedBatch.objects.filter(seed=OuterRef("pk")).order_by(
        "-date_collected", "-created_at"
    )
    return Seed.objects.filter(user=user).annotate(
        latest_batch_id=Subquery(latest_batch.values("id")[:1]),
        latest_batch_number=Subquery(latest_batch.values("batch_number")[:1]),
        latest_batch_quantity=Subquery(latest_batch.values("quantity")[:1]),
        latest_batch_unit=F("unit"),
        latest_batch_best_before=Subquery(latest_batch.values("best_before")[:1]),
    )


def get_user_wishlist_queryset(user) -> QuerySet[SeedWishlist]:
    return SeedWishlist.objects.filter(user=user)


def get_seed_filters(params) -> SeedFilters:
    return {
        "q": params.get("q", "").strip(),
        "category": params.get("category", "").strip(),
        "source": params.get("source", "").strip(),
    }


def apply_seed_filters(
    queryset: QuerySet[Seed], filters: SeedFilters
) -> QuerySet[Seed]:
    query = filters["q"]
    category = filters["category"]
    source = filters["source"]

    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(variety__icontains=query)
            | Q(batches__batch_number__icontains=query)
        )
    if category:
        queryset = queryset.filter(category=category)
    if source:
        queryset = queryset.filter(batches__collection_source=source)
    return queryset.distinct()


def get_seed_filter_context(filters: SeedFilters) -> dict:
    return {
        "q": filters["q"],
        "selected_category": filters["category"],
        "selected_source": filters["source"],
        "category_choices": Seed._meta.get_field("category").choices,
        "source_choices": SeedBatch._meta.get_field("collection_source").choices,
    }


def get_wishlist_filters(params) -> WishlistFilters:
    return {
        "q": params.get("q", "").strip(),
        "priority": params.get("priority", "").strip(),
        "status": params.get("status", "").strip(),
    }


def apply_wishlist_filters(
    queryset: QuerySet[SeedWishlist], filters: WishlistFilters
) -> QuerySet[SeedWishlist]:
    query = filters["q"]
    priority = filters["priority"]
    status = filters["status"]

    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(variety__icontains=query)
        )
    if priority:
        queryset = queryset.filter(priority=priority)
    if status == "pending":
        queryset = queryset.filter(acquired=False)
    elif status == "acquired":
        queryset = queryset.filter(acquired=True)
    return queryset


def get_wishlist_filter_context(filters: WishlistFilters) -> dict:
    return {
        "q": filters["q"],
        "selected_priority": filters["priority"],
        "selected_status": filters["status"],
        "priority_choices": SeedWishlist._meta.get_field("priority").choices,
    }


def get_seed_dashboard_context(user) -> dict:
    seeds = get_user_seed_queryset(user)
    batches = SeedBatch.objects.filter(seed__user=user)
    today = timezone.localdate()
    expiring_30_days = today + timezone.timedelta(days=30)
    reminder_counts = get_reminder_counts_for_user(user)

    return {
        "total_seeds": seeds.count(),
        "total_categories": seeds.values("category").distinct().count(),
        "expiring_soon": batches.filter(
            best_before__gte=today,
            best_before__lte=expiring_30_days,
        ).count(),
        "expired_count": batches.filter(best_before__lt=today).count(),
        "low_stock_count": reminder_counts["low_stock_count"],
        "wishlist_pending_count": get_user_wishlist_queryset(user)
        .filter(acquired=False)
        .count(),
        "wishlist_follow_up_count": reminder_counts["wishlist_follow_up_count"],
        "recent_seeds": seeds.order_by("-created_at")[:6],
        "category_breakdown": (
            seeds.values("category")
            .annotate(total=Count("id"))
            .order_by("-total", "category")
        ),
    }
