ATTENDANCE APP - FULL EDITED FILES

Replace these files inside your Django app folder:
D:\SchoolERP\attendance\

Files included:
- admin.py
- apps.py
- forms.py
- models.py
- tests.py
- urls.py
- utils.py
- views.py

Main fixes:
- Removed markdown/code-block text from admin.py and forms.py.
- Full syntax check passed for all Python files.
- Attendance student ordering is now numeric by roll_no: 1, 2, 3 ... 10, 11.
- Daily report, monthly report, register, graph, class-wise attendance use numeric roll sorting.
- Fixed duplicated date/date_str logic in monthly report and attendance register.
- Monthly report and attendance register now show full month dates.
- Holiday add/edit cleaned using ModelForm instance.
- Alert approval updates sms_sent / whatsapp_sent fields.
- Reset views include admin permission and date-range validation.

After replacing files, run:
python manage.py makemigrations attendance
python manage.py migrate
python manage.py check
python manage.py runserver
