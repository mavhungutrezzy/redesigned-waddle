from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SEED_CATEGORY(models.TextChoices):
    FRUIT = "fruit", _("Fruit")
    FLOWER = "flower", _("Flower")
    VEGETABLE = "vegetable", _("Vegetable")
    HERB = "herb", _("Herb")
    PLANT = "plant", _("Plant")
    GRAIN = "grain", _("Grain")
    OTHER = "other", _("Other")


class SEED_UNIT(models.TextChoices):
    G = "g", _("G")
    KG = "kg", _("KG")
    SEED = "seed", _("Seed")
    PACK = "pack", _("Pack")
    OTHER = "other", _("Other")


class COLLECTION_SOURCE(models.TextChoices):
    SELF = "self", _("Self")
    FRIEND = "friend", _("Friend")
    FAMILY = "family", _("Family")
    BOUGHT = "bought", _("Bought")
    GIFT = "gift", _("Gift")
    FARMERS_MARKET = "farmers_market", _("Farmers Market")
    GARDEN_CENTER = "garden_center", _("Garden Center")
    LOCAL_HARVESTERS = "local_harvesters", _("Local Harvesters")
    ONLINE_MARKET = "online_market", _("Online Market")
    OTHER_MARKET = "other_market", _("Other Market")
    HOME_HARVEST = "home_harvest", _("Home Harvest")
    OTHER = "other", _("Other")


class WISHLIST_PRIORITY(models.TextChoices):
    LOW = "low", _("Low")
    MEDIUM = "medium", _("Medium")
    HIGH = "high", _("High")


class Seed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    variety = models.CharField(max_length=255)
    category = models.CharField(max_length=255, choices=SEED_CATEGORY.choices)
    quantity = models.PositiveIntegerField()
    low_stock_threshold = models.PositiveIntegerField(default=5)
    unit = models.CharField(max_length=255, choices=SEED_UNIT.choices)
    date_collected = models.DateField()
    best_before = models.DateField()
    batch_number = models.CharField(max_length=255)
    collection_source = models.CharField(
        max_length=255, choices=COLLECTION_SOURCE.choices
    )
    supplier = models.CharField(max_length=255)
    storage_location = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    qr_code = models.FileField(upload_to="seed_qr/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "best_before"], name="seed_user_best_idx"),
            models.Index(fields=["user", "category"], name="seed_user_cat_idx"),
            models.Index(
                fields=["user", "collection_source"], name="seed_user_src_idx"
            ),
            models.Index(fields=["user", "created_at"], name="seed_user_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(best_before__gte=models.F("date_collected")),
                name="seed_best_before_gte_collected",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.batch_number})"

    def clean(self):
        if (
            self.best_before
            and self.date_collected
            and self.best_before < self.date_collected
        ):
            raise ValidationError(
                {"best_before": "Best before date must be on or after collected date."}
            )

    @property
    def label_name(self) -> str:
        variety = (self.variety or "").strip()
        if not variety:
            return self.name
        return f"{self.name} - {variety}"

    @property
    def label_best_before(self) -> str:
        return self.best_before.strftime("%Y-%m-%d")


class SeedPhoto(models.Model):
    seed = models.ForeignKey(Seed, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="seed_photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def clean(self):
        if not self.seed_id or self.pk:
            return
        if self.seed.photos.count() >= 3:
            raise ValidationError("A seed can only have up to 3 photos.")

    def __str__(self):
        return f"Photo for {self.seed.batch_number}"


class SeedWishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    acquired_seed = models.ForeignKey(
        Seed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wishlist_acquisitions",
    )
    name = models.CharField(max_length=255)
    variety = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=255, choices=SEED_CATEGORY.choices)
    preferred_source = models.CharField(
        max_length=255, choices=COLLECTION_SOURCE.choices, blank=True
    )
    desired_quantity = models.PositiveIntegerField(default=1)
    desired_unit = models.CharField(
        max_length=255, choices=SEED_UNIT.choices, default="pack"
    )
    priority = models.CharField(
        max_length=20,
        choices=WISHLIST_PRIORITY.choices,
        default=WISHLIST_PRIORITY.MEDIUM,
    )
    acquired = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["acquired", "-created_at"]
        indexes = [
            models.Index(fields=["user", "acquired"], name="wish_user_acq_idx"),
            models.Index(
                fields=["user", "follow_up_date"], name="wish_user_follow_idx"
            ),
            models.Index(fields=["user", "priority"], name="wish_user_prio_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_priority_display()})"

    def clean(self):
        if self.acquired_seed_id and not self.acquired:
            raise ValidationError(
                {
                    "acquired": "Wishlist item must be marked acquired when linked to a seed."
                }
            )
