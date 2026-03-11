import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import QuickBatchSearchForm, QuickQRSearchForm
from .models import SeedBatch


class QuickBatchSearchView(LoginRequiredMixin, FormView):
    form_class = QuickBatchSearchForm
    template_name = "seeds/quick_batch_search.html"

    def form_valid(self, form):
        batch_number = form.cleaned_data["batch_number"].strip()
        batch = (
            SeedBatch.objects.filter(
                seed__user=self.request.user, batch_number__iexact=batch_number
            )
            .select_related("seed")
            .first()
        )
        if not batch:
            form.add_error("batch_number", "No seed found with this batch number.")
            return self.form_invalid(form)
        return HttpResponseRedirect(
            reverse_lazy("seed_detail", kwargs={"pk": batch.seed_id})
        )


class QuickQRSearchView(LoginRequiredMixin, FormView):
    form_class = QuickQRSearchForm
    template_name = "seeds/quick_qr_search.html"

    def _extract_batch_number(self, qr_content: str):
        text = (qr_content or "").strip()
        if not text:
            return None
        batch_line = re.search(r"Batch:\s*([A-Za-z]-\d{6}-\d{4})", text, re.IGNORECASE)
        if batch_line:
            return batch_line.group(1).upper()
        full_match = re.search(r"\b([A-Za-z]-\d{6}-\d{4})\b", text)
        if full_match:
            return full_match.group(1).upper()
        return None

    def form_valid(self, form):
        batch_number = self._extract_batch_number(form.cleaned_data["qr_content"])
        if not batch_number:
            form.add_error(
                "qr_content", "Could not find a valid batch number in QR content."
            )
            return self.form_invalid(form)

        batch = (
            SeedBatch.objects.filter(
                seed__user=self.request.user, batch_number__iexact=batch_number
            )
            .select_related("seed")
            .first()
        )
        if not batch:
            form.add_error("qr_content", f"No seed found for batch {batch_number}.")
            return self.form_invalid(form)
        return HttpResponseRedirect(
            reverse_lazy("seed_detail", kwargs={"pk": batch.seed_id})
        )
