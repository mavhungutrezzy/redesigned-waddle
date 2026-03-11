import re

from seeds.models import SeedBatch

BATCH_NUMBER_REGEX = r"[A-Za-z]-\d{4}-\d{4}"


def build_batch_prefix(category: str, year: int, month: int | None = None) -> str:
    category_letter = (category or "x")[0].upper()
    return f"{category_letter}-{year:04d}"


def _extract_sequence(batch_number: str, prefix: str) -> int:
    pattern = rf"^{re.escape(prefix)}-(\d{{4}})$"
    match = re.match(pattern, batch_number or "")
    return int(match.group(1)) if match else 0


def generate_next_batch_number(
    category: str, year: int, month: int | None = None
) -> str:
    prefix = build_batch_prefix(category=category, year=year, month=month)
    latest_sequence = 0
    existing_batches = SeedBatch.objects.filter(
        batch_number__startswith=prefix
    ).values_list("batch_number", flat=True)
    for batch in existing_batches:
        latest_sequence = max(latest_sequence, _extract_sequence(batch, prefix))
    return f"{prefix}-{latest_sequence + 1:04d}"
