import re
from datetime import date, timedelta
from io import BytesIO
from typing import Any

import qrcode
import qrcode.image.svg
from django.core.files.base import ContentFile
from django.db import transaction

from seeds.models import Seed, SeedWishlist


def build_batch_prefix(category: str, year: int, month: int) -> str:
    category_letter = (category or "x")[0].upper()
    return f"{category_letter}-{year:04d}{month:02d}"


def _extract_sequence(batch_number: str, prefix: str) -> int:
    pattern = rf"^{re.escape(prefix)}-(\d{{4}})$"
    match = re.match(pattern, batch_number or "")
    return int(match.group(1)) if match else 0


def generate_next_batch_number(category: str, year: int, month: int) -> str:
    prefix = build_batch_prefix(category=category, year=year, month=month)
    latest_sequence = 0
    existing_batches = Seed.objects.filter(batch_number__startswith=prefix).values_list(
        "batch_number", flat=True
    )
    for batch in existing_batches:
        latest_sequence = max(latest_sequence, _extract_sequence(batch, prefix))
    return f"{prefix}-{latest_sequence + 1:04d}"


def _build_seed_qr_payload(seed: Seed) -> str:
    return "\n".join(
        [
            f"Batch: {seed.batch_number}",
            f"Name: {seed.name}",
            f"Variety: {seed.variety}",
            f"Category: {seed.get_category_display()}",
            f"Collected: {seed.date_collected.isoformat()}",
        ]
    )


def generate_seed_qr(seed: Seed) -> None:
    payload = _build_seed_qr_payload(seed)
    image = qrcode.make(payload, image_factory=qrcode.image.svg.SvgImage)
    output = BytesIO()
    image.save(output)
    filename = f"{seed.batch_number}.svg".replace("/", "_")
    seed.qr_code.save(filename, ContentFile(output.getvalue()), save=False)
    seed.save(update_fields=["qr_code", "updated_at"])


@transaction.atomic
def create_seed(seed_data: dict[str, Any], user) -> Seed:
    collected_date = seed_data.get("date_collected", date.today())
    seed_data["batch_number"] = generate_next_batch_number(
        category=seed_data["category"],
        year=collected_date.year,
        month=collected_date.month,
    )
    seed_data["user"] = user
    seed = Seed(**seed_data)
    seed.full_clean()
    seed.save()
    generate_seed_qr(seed)
    return seed


@transaction.atomic
def update_seed(seed: Seed, seed_data: dict[str, Any]) -> Seed:
    old_prefix = build_batch_prefix(
        seed.category, seed.date_collected.year, seed.date_collected.month
    )
    new_date = seed_data.get("date_collected", seed.date_collected)
    new_year = new_date.year
    new_month = new_date.month
    new_category = seed_data.get("category", seed.category)
    new_prefix = build_batch_prefix(new_category, new_year, new_month)

    if not seed.batch_number.startswith(old_prefix) or old_prefix != new_prefix:
        seed.batch_number = generate_next_batch_number(
            category=new_category, year=new_year, month=new_month
        )

    for field, value in seed_data.items():
        setattr(seed, field, value)
    seed.full_clean()
    seed.save()
    generate_seed_qr(seed)
    return seed


def build_seed_label_data(seed: Seed) -> dict[str, Any]:
    if not seed.qr_code:
        generate_seed_qr(seed)

    return {
        "seed_name": seed.name,
        "variety": seed.variety,
        "batch_number": seed.batch_number,
        "best_before": seed.label_best_before,
        "qr_code": seed.qr_code,
    }


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
        "quantity": wishlist_item.desired_quantity,
        "unit": wishlist_item.desired_unit,
        "date_collected": today,
        "best_before": default_best_before,
        "collection_source": source,
        "supplier": "Wishlist acquisition",
        "storage_location": "To be assigned",
        "notes": notes,
    }
    seed = create_seed(seed_data, user=wishlist_item.user)

    wishlist_item.acquired = True
    wishlist_item.acquired_seed = seed
    wishlist_item.save(update_fields=["acquired", "acquired_seed", "updated_at"])
    return seed
