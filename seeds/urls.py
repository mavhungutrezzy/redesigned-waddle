from django.urls import path

from .views import (
    QuickBatchSearchView,
    QuickQRSearchView,
    ReminderCenterView,
    SeedCreateView,
    SeedDashboardView,
    SeedDeleteView,
    SeedDetailView,
    SeedLabelPrintView,
    SeedLabelSheetPrintView,
    SeedLabelSheetSelectView,
    SeedListView,
    SeedUpdateView,
    WishlistAcquireView,
    WishlistCreateView,
    WishlistDeleteView,
    WishlistListView,
    WishlistToggleAcquiredView,
    WishlistUpdateView,
)

urlpatterns = [
    path("dashboard/", SeedDashboardView.as_view(), name="seed_dashboard"),
    path("reminders/", ReminderCenterView.as_view(), name="seed_reminders"),
    path("", SeedListView.as_view(), name="seed_list"),
    path("lookup/batch/", QuickBatchSearchView.as_view(), name="quick_batch_search"),
    path("lookup/qr/", QuickQRSearchView.as_view(), name="quick_qr_search"),
    path(
        "labels/sheet/",
        SeedLabelSheetSelectView.as_view(),
        name="seed_label_sheet_select",
    ),
    path(
        "labels/sheet/print/",
        SeedLabelSheetPrintView.as_view(),
        name="seed_label_sheet_print",
    ),
    path("wishlist/", WishlistListView.as_view(), name="wishlist_list"),
    path("wishlist/new/", WishlistCreateView.as_view(), name="wishlist_create"),
    path(
        "wishlist/<int:pk>/edit/", WishlistUpdateView.as_view(), name="wishlist_update"
    ),
    path(
        "wishlist/<int:pk>/delete/",
        WishlistDeleteView.as_view(),
        name="wishlist_delete",
    ),
    path(
        "wishlist/<int:pk>/toggle-acquired/",
        WishlistToggleAcquiredView.as_view(),
        name="wishlist_toggle_acquired",
    ),
    path(
        "wishlist/<int:pk>/acquire/",
        WishlistAcquireView.as_view(),
        name="wishlist_acquire",
    ),
    path("new/", SeedCreateView.as_view(), name="seed_create"),
    path("<int:pk>/", SeedDetailView.as_view(), name="seed_detail"),
    path(
        "<int:pk>/print-label/", SeedLabelPrintView.as_view(), name="seed_print_label"
    ),
    path(
        "<int:pk>/label-image/", SeedLabelPrintView.as_view(), name="seed_label_image"
    ),
    path("<int:pk>/edit/", SeedUpdateView.as_view(), name="seed_update"),
    path("<int:pk>/delete/", SeedDeleteView.as_view(), name="seed_delete"),
]
