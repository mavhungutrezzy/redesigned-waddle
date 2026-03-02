from django.contrib import admin

from .models import Seed, SeedPhoto, SeedWishlist


class SeedPhotoInline(admin.TabularInline):
    model = SeedPhoto
    extra = 0
    max_num = 3


@admin.register(Seed)
class SeedAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "batch_number",
        "quantity",
        "unit",
        "date_collected",
        "best_before",
        "user",
    )
    list_filter = ("category", "unit", "collection_source")
    search_fields = ("name", "variety", "batch_number", "supplier", "user__email")
    ordering = ("-created_at",)
    list_select_related = ("user",)
    readonly_fields = ("batch_number", "qr_code", "created_at", "updated_at")
    autocomplete_fields = ("user",)
    inlines = (SeedPhotoInline,)


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
