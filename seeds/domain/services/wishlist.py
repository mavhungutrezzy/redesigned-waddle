from datetime import date, timedelta

from django.db import transaction

from seeds.models import Seed, SeedWishlist

from .seed import create_seed


@transaction.atomic
def acquire_wishlist_item(wishlist_item: SeedWishlist) -> Seed:
    if wishlist_item.acquired_seed_id:
        return wishlist_item.acquired_seed

    today = date.today()
    default_best_before = today + timedelta(days=365)
    source = wishlist_item.preferred_source or "bought"
    wishlist_note = (wishlist_item.notes or "").strip()
    notes = "Converted from wishlist item."
    if wishlist_note:
        notes = f"{notes}\n\nWishlist notes:\n{wishlist_note}"

    seed_data = {
        "name": wishlist_item.name,
        "variety": wishlist_item.variety or wishlist_item.name,
        "category": wishlist_item.category,
        "unit": wishlist_item.desired_unit,
    }
    batch_data = {
        "quantity": wishlist_item.desired_quantity,
        "date_collected": today,
        "best_before": default_best_before,
        "collection_source": source,
        "supplier": "Wishlist acquisition",
        "storage_location": "To be assigned",
        "notes": notes,
    }
    seed = create_seed(seed_data, user=wishlist_item.user, initial_batch_data=batch_data)

    wishlist_item.acquired = True
    wishlist_item.acquired_seed = seed
    wishlist_item.save(update_fields=["acquired", "acquired_seed", "updated_at"])
    return seed
