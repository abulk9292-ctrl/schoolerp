from django.shortcuts import redirect


class EmployeeAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path

        # =====================================
        # PUBLIC URLS
        # =====================================

        public_prefixes = (
            "/",
            "/admin/",
            "/admin-login/",
            "/logout/",
            "/site/",
            "/website/",
            "/static/",
            "/media/",
            "/api/",
            "/mobile-api/",
            "/favicon.ico",

            "/teachers/login/",
            "/teachers/logout/",

            "/students/login/",
            "/students/logout/",
            "/students/forgot/",
            "/students/verify/",
            "/students/reset/",
            "/students/result-check/",

            "/students/parent/login/",
            "/students/parent/logout/",
        )

        if path.startswith(public_prefixes):
            return self.get_response(request)

        # =====================================
        # NOT LOGGED IN
        # =====================================

        if not request.user.is_authenticated:
            return self.get_response(request)

        # =====================================
        # SUPER ADMIN
        # =====================================

        if request.user.is_superuser or request.user.is_staff:
            return self.get_response(request)

        employee = getattr(request.user, "employee", None)

        if not employee:
            return redirect("/admin-login/")

        if not employee.is_active:
            return redirect("/teachers/login/")

        # =====================================
        # ERP ADMIN
        # =====================================

        if employee.is_erp_admin:
            return self.get_response(request)

        # =====================================
        # ALWAYS ALLOWED FOR TEACHERS
        # =====================================

        teacher_allowed = (
            "/teachers/dashboard/",
            "/homework/",
            "/notices/",
            "/complaints/",
        )

        if path.startswith(teacher_allowed):
            return self.get_response(request)

        # =====================================
        # DASHBOARD REDIRECT
        # =====================================

        if path == "/dashboard/":
            return redirect("/teachers/dashboard/")

        # =====================================
        # MODULE ACCESS MAP
        # =====================================

        access_map = {
            "/students/": employee.can_access_students,
            "/teachers/": employee.can_access_teachers,
            "/academics/": employee.can_access_academics,
            "/attendance/": employee.can_access_attendance,
            "/fees/": employee.can_access_fees,
            "/payroll/": employee.can_access_payroll,
            "/exams/": employee.can_access_exams,
            "/reports/": employee.can_access_reports,
            "/admissions/": employee.can_access_admissions,
            "/idcards/": employee.can_access_idcards,
            "/communications/": employee.can_access_communications,
            "/expenses/": employee.can_access_expenses,
            "/backup/": employee.can_access_backup,
            "/settings/": employee.can_access_settings,

            # Shared Permissions
            "/certificates/": employee.can_access_reports,
            "/behaviour/": employee.can_access_attendance,

            # New Modules
            "/online-store/": employee.can_access_students,
            "/timetable/": employee.can_access_academics,
            "/live-classes/": employee.can_access_academics,
            "/question-answers/": employee.can_access_academics,
            "/assets/": employee.can_access_reports,
        }

        for prefix, allowed in access_map.items():

            if path.startswith(prefix):

                if allowed:
                    return self.get_response(request)

                return redirect("/teachers/dashboard/")

        # =====================================
        # DEFAULT
        # =====================================

        return redirect("/teachers/dashboard/")