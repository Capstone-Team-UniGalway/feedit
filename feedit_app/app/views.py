from django.shortcuts import redirect
from django.views.generic import TemplateView


class WelcomeView(TemplateView):
    template_name = "pages/welcome.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            if not user.is_fully_activated:
                return redirect("account_edit")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)
