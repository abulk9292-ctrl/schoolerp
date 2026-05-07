from django.shortcuts import redirect


class EmployeeAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # ✅ Public / safe paths
        public_paths = [
            '/login/',
            '/logout/',
            '/admin/',
            '/static/',
            '/media/',
            '/api/',
            '/mobile-api/',
            '/website/',
            '/site/',
            '/favicon.ico',
        ]

        if any(path.startswith(p) for p in public_paths):
            return self.get_response(request)

        # ✅ Not logged in
        if not request.user.is_authenticated:
            return self.get_response(request)

        # ✅ Admin / Staff full access
        if request.user.is_superuser or request.user.is_staff:
            return self.get_response(request)

        employee = getattr(request.user, 'employee', None)

        if employee is None:
            return redirect('/login/')

        if not employee.is_active:
            return redirect('/login/')

        # ✅ ERP Admin employee full access
        if employee.is_erp_admin:
            return self.get_response(request)

        # ✅ Normal teacher dashboard allowed
        if path.startswith('/teacher-dashboard/'):
            return self.get_response(request)

        # ❌ Normal teacher cannot open main admin dashboard
        if path.startswith('/dashboard/'):
            return redirect('/teacher-dashboard/')

        # ❌ Normal teacher cannot open/mark teacher attendance
        if path.startswith('/attendance/teachers/'):
            return redirect('/teacher-dashboard/')

        # ❌ Normal teacher cannot open admin-only attendance graph/register
        if path.startswith('/attendance/graph/') or path.startswith('/attendance/register/'):
            return redirect('/teacher-dashboard/')

        # ✅ Normal teacher can access student attendance area only if attendance permission true
        student_attendance_paths = [
            '/attendance/students/',
            '/attendance/students/daily-report/',
            '/attendance/students/percentage-report/',
            '/attendance/students/monthly-report/',
        ]

        if any(path.startswith(p) for p in student_attendance_paths):
            if employee.can_access_attendance:
                return self.get_response(request)
            return redirect('/teacher-dashboard/')

        # ✅ Permission based access
        access_map = {
            '/students/': getattr(employee, 'can_access_students', False),
            '/teachers/': getattr(employee, 'can_access_teachers', False),
            '/academics/': getattr(employee, 'can_access_academics', False),
            '/fees/': getattr(employee, 'can_access_fees', False),
            '/payroll/': getattr(employee, 'can_access_payroll', False),
            '/exams/': getattr(employee, 'can_access_exams', False),
            '/reports/': getattr(employee, 'can_access_reports', False),
            '/admissions/': getattr(employee, 'can_access_admissions', False),
            '/idcards/': getattr(employee, 'can_access_idcards', False),
            '/communications/': getattr(employee, 'can_access_communications', False),
            '/expenses/': getattr(employee, 'can_access_expenses', False),
            '/backup/': getattr(employee, 'can_access_backup', False),
            '/settings/': getattr(employee, 'can_access_settings', False),
            '/settings-app/': getattr(employee, 'can_access_settings', False),
        }

        for prefix, allowed in access_map.items():
            if path.startswith(prefix):
                if allowed:
                    return self.get_response(request)
                return redirect('/teacher-dashboard/')

        return redirect('/teacher-dashboard/')