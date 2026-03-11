from datetime import date
from typing import Any

from django.db import transaction

from seeds.models import Seed, SeedBatch

from .batch import generate_next_batch_number
from .qr import generate_batch_qr


def _batch_defaults_from_batch_data(batch_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "quantity": batch_data["quantity"],
        "date_collected": batch_data["date_collected"],
        "best_before": batch_data["best_before"],
        "collection_source": batch_data["collection_source"],
        "supplier": batch_data["supplier"],
        "storage_location": batch_data["storage_location"],
        "notes": batch_data.get("notes", ""),
    }


def _resolve_initial_batch_data(
    seed_data: dict[str, Any], initial_batch_data: dict[str, Any] | None
) -> dict[str, Any]:
    if initial_batch_data:
        return initial_batch_data
    raise ValueError("initial_batch_data is required to create a seed.")


@transaction.atomic
def create_seed(
    seed_data: dict[str, Any], user, initial_batch_data: dict[str, Any] | None = None
) -> Seed:
    batch_data = _resolve_initial_batch_data(seed_data, initial_batch_data)
    collected_date = batch_data.get("date_collected", date.today())
    batch_number = batch_data.get("batch_number") or generate_next_batch_number(
        category=seed_data["category"],
        year=collected_date.year,
        month=collected_date.month,
    )
    seed = Seed(user=user, **seed_data)
    seed.full_clean()
    seed.save()
    batch = SeedBatch.objects.create(
        seed=seed,
        batch_number=batch_number,
        **_batch_defaults_from_batch_data(batch_data),
    )
    generate_batch_qr(seed, batch)
    return seed


@transaction.atomic
def update_seed(seed: Seed, seed_data: dict[str, Any]) -> Seed:
    for field, value in seed_data.items():
        setattr(seed, field, value)
    seed.full_clean()
    seed.save()
    latest_batch = seed.latest_batch
    if latest_batch:
        generate_batch_qr(seed, latest_batch)
    return seed


def build_seed_label_data(seed: Seed) -> dict[str, Any]:
    latest_batch = seed.latest_batch
    if latest_batch and not latest_batch.qr_code:
        generate_batch_qr(seed, latest_batch)

    return {
        "seed_name": seed.name,
        "variety": seed.variety,
        "batch_number": (latest_batch.batch_number if latest_batch else "-"),
        "best_before": (
            latest_batch.best_before.isoformat()
            if latest_batch
            else "-"
        ),
        "qr_code": latest_batch.qr_code if latest_batch else None,
    }
