from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import SeedWishlistForm
from .models import SeedWishlist
from .queries import (
    apply_wishlist_filters,
    get_user_wishlist_queryset,
    get_wishlist_filter_context,
    get_wishlist_filters,
)
from .services import acquire_wishlist_item


class UserWishlistQuerysetMixin:
    def get_queryset(self):
        return get_user_wishlist_queryset(self.request.user)


class WishlistListView(LoginRequiredMixin, UserWishlistQuerysetMixin, ListView):
    model = SeedWishlist
    template_name = "seeds/wishlist_list.html"
    context_object_name = "wishlist_items"

    def get_queryset(self):
        self.wishlist_filters = get_wishlist_filters(self.request.GET)
        return apply_wishlist_filters(super().get_queryset(), self.wishlist_filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context.update(get_wishlist_filter_context(self.wishlist_filters))
        context["pending_count"] = queryset.filter(acquired=False).count()
        context["acquired_count"] = queryset.filter(acquired=True).count()
        context["result_count"] = queryset.count()
        return context


class WishlistCreateView(LoginRequiredMixin, CreateView):
    model = SeedWishlist
    form_class = SeedWishlistForm
    template_name = "seeds/wishlist_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("wishlist_list")


class WishlistUpdateView(LoginRequiredMixin, UserWishlistQuerysetMixin, UpdateView):
    model = SeedWishlist
    form_class = SeedWishlistForm
    template_name = "seeds/wishlist_form.html"
    context_object_name = "wishlist_item"

    def get_success_url(self):
        return reverse_lazy("wishlist_list")


class WishlistDeleteView(LoginRequiredMixin, UserWishlistQuerysetMixin, DeleteView):
    model = SeedWishlist
    success_url = reverse_lazy("wishlist_list")
    template_name = "seeds/wishlist_confirm_delete.html"


class WishlistToggleAcquiredView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(SeedWishlist, pk=pk, user=request.user)
        item.acquired = not item.acquired
        if not item.acquired:
            item.acquired_seed = None
        item.save(update_fields=["acquired", "acquired_seed", "updated_at"])
        return HttpResponseRedirect(reverse_lazy("wishlist_list"))


class WishlistAcquireView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(SeedWishlist, pk=pk, user=request.user)
        seed = acquire_wishlist_item(item)
        return HttpResponseRedirect(reverse_lazy("seed_detail", kwargs={"pk": seed.pk}))
