from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from ..forms_seed import SeedForm
from ..models import Seed, SeedBatch, SeedWishlist
from ..queries import (
    apply_seed_filters,
    apply_wishlist_filters,
    get_seed_dashboard_context,
    get_seed_filters,
    get_user_seed_queryset,
    get_user_wishlist_queryset,
    get_wishlist_filters,
)
from ..reminders import get_reminder_counts_for_user
from ..services import create_seed


class SeedQueryTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="test-pass-123",
        )
        self.other_user = user_model.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="test-pass-123",
        )
        today = timezone.localdate()

        self.seed_a = Seed.objects.create(
            user=self.user,
            name="Tomato",
            variety="Roma",
            category="vegetable",
            unit="pack",
        )
        self.seed_b = Seed.objects.create(
            user=self.user,
            name="Rose",
            variety="Red",
            category="flower",
            unit="pack",
        )
        other_seed = Seed.objects.create(
            user=self.other_user,
            name="Other Seed",
            variety="Hidden",
            category="other",
            unit="pack",
        )

        SeedBatch.objects.create(
            seed=self.seed_a,
            quantity=3,
            date_collected=today,
            best_before=today + timedelta(days=10),
            batch_number="V-202603-0001",
            collection_source="bought",
            supplier="Supplier A",
            storage_location="Shelf A",
        )
        SeedBatch.objects.create(
            seed=self.seed_b,
            quantity=10,
            date_collected=today,
            best_before=today + timedelta(days=120),
            batch_number="F-202603-0001",
            collection_source="gift",
            supplier="Supplier B",
            storage_location="Shelf B",
        )
        SeedBatch.objects.create(
            seed=other_seed,
            quantity=1,
            date_collected=today,
            best_before=today + timedelta(days=5),
            batch_number="O-202603-0001",
            collection_source="bought",
            supplier="Supplier C",
            storage_location="Shelf C",
        )

        self.wishlist_pending = SeedWishlist.objects.create(
            user=self.user,
            name="Basil",
            variety="Genovese",
            category="herb",
            priority="high",
            acquired=False,
            follow_up_date=today,
        )
        self.wishlist_acquired = SeedWishlist.objects.create(
            user=self.user,
            name="Mint",
            variety="Peppermint",
            category="herb",
            priority="low",
            acquired=True,
        )
        SeedWishlist.objects.create(
            user=self.other_user,
            name="Other Wish",
            variety="Other",
            category="herb",
            priority="medium",
            acquired=False,
            follow_up_date=today,
        )

    def test_seed_filtering_applies_all_filters(self):
        filters = get_seed_filters(
            {"q": "tom", "category": "vegetable", "source": "bought"}
        )
        queryset = apply_seed_filters(get_user_seed_queryset(self.user), filters)
        self.assertQuerySetEqual(queryset, [self.seed_a], ordered=False)

    def test_wishlist_filtering_by_status(self):
        filters = get_wishlist_filters({"status": "pending"})
        queryset = apply_wishlist_filters(
            get_user_wishlist_queryset(self.user), filters
        )
        self.assertQuerySetEqual(queryset, [self.wishlist_pending], ordered=False)

    def test_reminder_counts_only_for_current_user(self):
        counts = get_reminder_counts_for_user(self.user)
        self.assertEqual(counts["expiring_count"], 1)
        self.assertEqual(counts["low_stock_count"], 0)
        self.assertEqual(counts["wishlist_follow_up_count"], 1)
        self.assertEqual(counts["total_reminders"], 2)

    def test_dashboard_context_uses_same_reminder_counts(self):
        context = get_seed_dashboard_context(self.user)
        self.assertEqual(context["total_seeds"], 2)
        self.assertEqual(context["low_stock_count"], 0)
        self.assertEqual(context["wishlist_follow_up_count"], 1)
        self.assertEqual(context["wishlist_pending_count"], 1)


class SeedModelValidationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="validator",
            email="validator@example.com",
            password="test-pass-123",
        )
        self.today = timezone.localdate()

    def test_batch_best_before_cannot_be_before_collected_date(self):
        seed = Seed.objects.create(
            user=self.user,
            name="Carrot",
            variety="Nantes",
            category="vegetable",
            unit="pack",
        )
        batch = SeedBatch(
            seed=seed,
            quantity=5,
            date_collected=self.today,
            best_before=self.today - timedelta(days=1),
            batch_number="V-202603-9999",
            collection_source="bought",
            supplier="Supplier",
            storage_location="Shelf",
        )
        with self.assertRaises(ValidationError):
            batch.full_clean()

    def test_wishlist_cannot_link_seed_if_not_acquired(self):
        seed = Seed.objects.create(
            user=self.user,
            name="Pepper",
            variety="Cayenne",
            category="vegetable",
            unit="pack",
        )
        item = SeedWishlist(
            user=self.user,
            name="Pepper",
            variety="Cayenne",
            category="vegetable",
            acquired=False,
            acquired_seed=seed,
        )
        with self.assertRaises(ValidationError):
            item.full_clean()


class SeedFormValidationTests(TestCase):
    def test_seed_form_accepts_identity_fields(self):
        form = SeedForm(
            data={
                "name": "Spinach",
                "variety": "Bloomsdale",
                "category": "vegetable",
                "unit": "pack",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


class SeedBatchFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="batchuser",
            email="batchuser@example.com",
            password="test-pass-123",
        )
        self.client.login(username="batchuser", password="test-pass-123")
        today = timezone.localdate()
        self.seed = Seed.objects.create(
            user=self.user,
            name="Tomato",
            variety="Roma",
            category="vegetable",
            unit="pack",
        )
        self.batch = SeedBatch.objects.create(
            seed=self.seed,
            quantity=10,
            date_collected=today,
            best_before=today + timedelta(days=180),
            batch_number="V-202603-0100",
            collection_source="bought",
            supplier="Supplier A",
            storage_location="Shelf A",
            notes="first",
        )

    def test_quick_batch_lookup_uses_seed_batch(self):
        response = self.client.post(
            "/seeds/lookup/batch/",
            data={"batch_number": self.batch.batch_number},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/seeds/{self.seed.pk}/", response.url)

    def test_seed_batch_create_view_creates_batch(self):
        today = timezone.localdate()
        response = self.client.post(
            f"/seeds/{self.seed.pk}/batches/new/",
            data={
                "batch_number": "V-202603-0101",
                "quantity": 8,
                "date_collected": today.isoformat(),
                "best_before": (today + timedelta(days=90)).isoformat(),
                "collection_source": "gift",
                "supplier": "Supplier B",
                "storage_location": "Shelf B",
                "notes": "second",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SeedBatch.objects.filter(seed=self.seed, batch_number="V-202603-0101").exists()
        )

    def test_create_seed_service_creates_seed_and_initial_batch(self):
        today = timezone.localdate()
        seed = create_seed(
            {
                "name": "Cucumber",
                "variety": "Marketmore",
                "category": "vegetable",
                "unit": "pack",
            },
            user=self.user,
            initial_batch_data={
                "batch_number": "",
                "quantity": 12,
                "date_collected": today,
                "best_before": today + timedelta(days=180),
                "collection_source": "bought",
                "supplier": "Supplier Z",
                "storage_location": "Shelf C",
                "notes": "",
            },
        )
        self.assertEqual(seed.name, "Cucumber")
        self.assertTrue(SeedBatch.objects.filter(seed=seed).exists())
