import re
from io import BytesIO

import qrcode
from django.core.files.base import ContentFile

from seeds.models import Seed, SeedBatch

from .batch import BATCH_NUMBER_REGEX


def _build_seed_qr_payload(seed: Seed) -> str:
    latest_batch = seed.latest_batch
    if not latest_batch:
        return "\n".join(
            [
                "Batch: -",
                f"Name: {seed.name}",
                f"Variety: {seed.variety}",
                f"Category: {seed.get_category_display()}",
            ]
        )
    return "\n".join(
        [
            f"Batch: {latest_batch.batch_number}",
            f"Name: {seed.name}",
            f"Variety: {seed.variety}",
            f"Category: {seed.get_category_display()}",
            f"Collected: {latest_batch.date_collected.isoformat()}",
        ]
    )


def _build_batch_qr_payload(seed: Seed, batch: SeedBatch) -> str:
    return "\n".join(
        [
            f"Batch: {batch.batch_number}",
            f"Name: {seed.name}",
            f"Variety: {seed.variety}",
            f"Category: {seed.get_category_display()}",
            f"Collected: {batch.date_collected.isoformat()}",
        ]
    )


def decode_batch_number(qr_content: str) -> str | None:
    text = (qr_content or "").strip()
    if not text:
        return None
    batch_line = re.search(rf"Batch:\s*({BATCH_NUMBER_REGEX})", text, re.IGNORECASE)
    if batch_line:
        return batch_line.group(1).upper()
    full_match = re.search(rf"\b({BATCH_NUMBER_REGEX})\b", text)
    if full_match:
        return full_match.group(1).upper()
    return None


def _build_qr_png_bytes(data: str) -> bytes:
    image = qrcode.make(data)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def generate_batch_qr(seed: Seed, batch: SeedBatch) -> None:
    payload = _build_batch_qr_payload(seed, batch)
    filename = f"{batch.batch_number}.png".replace("/", "_")
    batch.qr_code.save(filename, ContentFile(_build_qr_png_bytes(payload)), save=False)
    batch.save(update_fields=["qr_code", "updated_at"])


def generate_seed_qr(seed: Seed) -> None:
    latest_batch = seed.latest_batch
    if latest_batch:
        generate_batch_qr(seed, latest_batch)
