from django.shortcuts import redirect


class AdminMFAEnforcementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if path.startswith("/admin/"):
            if path.startswith("/admin/login") or path.startswith("/admin/logout"):
                return self.get_response(request)

            user = request.user

            if (
                user.is_authenticated
                and user.is_staff
                and getattr(user, "has_mfa_enabled", False)
            ):
                if not request.session.get("account_mfa_authenticated"):
                    # Prevent loop if already at the MFA challenge route
                    if not path.startswith("/account/mfa/authenticate"):
                        return redirect("/account/mfa/authenticate/")

        return self.get_response(request)
