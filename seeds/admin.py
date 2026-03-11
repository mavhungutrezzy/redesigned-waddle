from django.contrib import admin

from .models import Seed, SeedBatch, SeedPhoto, SeedWishlist


class SeedPhotoInline(admin.TabularInline):
    model = SeedPhoto
    extra = 0
    max_num = 3


class SeedBatchInline(admin.TabularInline):
    model = SeedBatch
    extra = 0
    fields = (
        "batch_number",
        "quantity",
        "date_collected",
        "best_before",
        "collection_source",
        "supplier",
        "storage_location",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(Seed)
class SeedAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "user",
        "created_at",
        "updated_at",
    )
    list_filter = ("category", "unit")
    search_fields = ("name", "variety", "user__email")
    ordering = ("-created_at",)
    list_select_related = ("user",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("user",)
    inlines = (SeedPhotoInline, SeedBatchInline)


@admin.register(SeedBatch)
class SeedBatchAdmin(admin.ModelAdmin):
    list_display = (
        "seed",
        "batch_number",
        "quantity",
        "date_collected",
        "best_before",
    )
    list_filter = ("collection_source",)
    search_fields = ("seed__name", "seed__variety", "batch_number", "supplier")
    list_select_related = ("seed",)
    ordering = ("-created_at",)


@admin.register(SeedWishlist)
class SeedWishlistAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "priority",
        "acquired",
        "acquired_seed",
        "desired_quantity",
        "desired_unit",
        "user",
    )
    list_filter = ("priority", "acquired", "category")
    search_fields = ("name", "variety", "notes", "user__email")
    ordering = ("acquired", "-created_at")
    list_select_related = ("user", "acquired_seed")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("user", "acquired_seed")
