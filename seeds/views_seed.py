from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import SeedForm, SeedPhotoFormSet
from .models import Seed
from .queries import (
    apply_seed_filters,
    get_seed_dashboard_context,
    get_seed_filter_context,
    get_seed_filters,
    get_user_seed_queryset,
)
from .services import build_seed_label_data, create_seed, update_seed


class UserSeedQuerysetMixin:
    def get_queryset(self):
        return get_user_seed_queryset(self.request.user)


class SeedListView(LoginRequiredMixin, UserSeedQuerysetMixin, ListView):
    model = Seed
    template_name = "seeds/seed_list.html"
    context_object_name = "seeds"

    def get_queryset(self):
        self.seed_filters = get_seed_filters(self.request.GET)
        return apply_seed_filters(super().get_queryset(), self.seed_filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_seed_filter_context(self.seed_filters))
        context["result_count"] = context["seeds"].count()
        return context


class SeedDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "seeds/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_seed_dashboard_context(self.request.user))
        return context


class SeedDetailView(LoginRequiredMixin, UserSeedQuerysetMixin, DetailView):
    model = Seed
    template_name = "seeds/seed_detail.html"
    context_object_name = "seed"


class SeedLabelPrintView(LoginRequiredMixin, UserSeedQuerysetMixin, DetailView):
    model = Seed
    template_name = "seeds/seed_label_print.html"
    context_object_name = "seed"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["label"] = build_seed_label_data(self.object)
        return context


class SeedLabelSheetSelectView(LoginRequiredMixin, UserSeedQuerysetMixin, ListView):
    model = Seed
    template_name = "seeds/seed_label_sheet_select.html"
    context_object_name = "seeds"

    def get_queryset(self):
        self.seed_filters = get_seed_filters(self.request.GET)
        return apply_seed_filters(super().get_queryset(), self.seed_filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_seed_filter_context(self.seed_filters))
        context["result_count"] = context["seeds"].count()
        return context


class SeedLabelSheetPrintView(LoginRequiredMixin, View):
    template_name = "seeds/seed_label_sheet_print.html"
    labels_per_page = 24

    def post(self, request):
        seed_ids = request.POST.getlist("seed_ids")
        if not seed_ids:
            return HttpResponseRedirect(reverse_lazy("seed_label_sheet_select"))

        seeds = Seed.objects.filter(user=request.user, id__in=seed_ids).order_by("name")
        labels = [build_seed_label_data(seed) for seed in seeds]
        if not labels:
            return HttpResponseRedirect(reverse_lazy("seed_label_sheet_select"))

        pages = []
        for index in range(0, len(labels), self.labels_per_page):
            page = labels[index : index + self.labels_per_page]
            if len(page) < self.labels_per_page:
                page.extend([None] * (self.labels_per_page - len(page)))
            pages.append(page)

        context = {
            "pages": pages,
            "selected_count": len(labels),
            "labels_per_page": self.labels_per_page,
        }
        return render(request, self.template_name, context)


class SeedCreateView(LoginRequiredMixin, CreateView):
    model = Seed
    form_class = SeedForm
    template_name = "seeds/seed_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "photo_formset" not in context:
            context["photo_formset"] = SeedPhotoFormSet(
                self.request.POST or None,
                self.request.FILES or None,
                prefix="photos",
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        photo_formset = context["photo_formset"]
        if not photo_formset.is_valid():
            return self.render_to_response(context)
        try:
            self.object = create_seed(form.cleaned_data, user=self.request.user)
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for field, messages in exc.message_dict.items():
                    for message in messages:
                        form.add_error(field if field in form.fields else None, message)
            else:
                form.add_error(None, str(exc))
            return self.render_to_response(context)
        photo_formset.instance = self.object
        photo_formset.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("seed_detail", kwargs={"pk": self.object.pk})


class SeedUpdateView(LoginRequiredMixin, UserSeedQuerysetMixin, UpdateView):
    model = Seed
    form_class = SeedForm
    template_name = "seeds/seed_form.html"
    context_object_name = "seed"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "photo_formset" not in context:
            context["photo_formset"] = SeedPhotoFormSet(
                self.request.POST or None,
                self.request.FILES or None,
                instance=self.object,
                prefix="photos",
            )
        return context

    def form_valid(self, form):
        self.object = self.get_object()
        context = self.get_context_data(form=form)
        photo_formset = context["photo_formset"]
        if not photo_formset.is_valid():
            return self.render_to_response(context)
        try:
            self.object = update_seed(self.object, form.cleaned_data)
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for field, messages in exc.message_dict.items():
                    for message in messages:
                        form.add_error(field if field in form.fields else None, message)
            else:
                form.add_error(None, str(exc))
            return self.render_to_response(context)
        photo_formset.instance = self.object
        photo_formset.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("seed_detail", kwargs={"pk": self.object.pk})


class SeedDeleteView(LoginRequiredMixin, UserSeedQuerysetMixin, DeleteView):
    model = Seed
    template_name = "seeds/seed_confirm_delete.html"
    success_url = reverse_lazy("seed_list")
