from django.shortcuts import redirect
from django.contrib.auth import logout


class SessionSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("MIDDLEWARE CALL")
        if request.user.is_authenticated:
            print("USER IS AUTH")
            ua = request.META.get("HTTP_USER_AGENT", "")
            ip = request.META.get("REMOTE_ADDR")

            if "user_agent" not in request.session:
                print("UA not in session")
                request.session["user_agent"] = ua
                request.session["ip"] = ip
            else:
                print("UA IN session")
                if request.session["user_agent"] != ua or request.session["ip"] != ip:
                    print("LOGOUT - UA or IP not allowed")
                    logout(request)
                    request.session.flush()

        return self.get_response(request)


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
