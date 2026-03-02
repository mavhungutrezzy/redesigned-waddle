from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .reminders import build_reminder_rows, get_reminder_querysets_for_user


class ReminderCenterView(LoginRequiredMixin, TemplateView):
    template_name = "seeds/reminders.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reminder_data = get_reminder_querysets_for_user(self.request.user)
        context.update(reminder_data)
        context["reminder_rows"] = build_reminder_rows(
            expiring_seeds=context["expiring_seeds"],
            low_stock_seeds=context["low_stock_seeds"],
            wishlist_follow_ups=context["wishlist_follow_ups"],
            reverse=reverse_lazy,
        )
        context["total_reminders"] = (
            context["expiring_seeds"].count()
            + context["low_stock_seeds"].count()
            + context["wishlist_follow_ups"].count()
        )
        return context
