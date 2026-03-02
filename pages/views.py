from django.shortcuts import redirect
from django.views.generic import TemplateView


class HomePageView(TemplateView):
    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("seed_dashboard")
        return super().get(request, *args, **kwargs)


class AboutPageView(TemplateView):
    template_name = "pages/about.html"
