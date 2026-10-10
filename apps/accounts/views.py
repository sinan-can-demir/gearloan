from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        user = self.request.user
        if user.is_admin() or user.is_staff:
            return ["admin_portal/dashboard.html"]
        return ["borrower/dashboard.html"]
