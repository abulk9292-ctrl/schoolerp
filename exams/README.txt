EXAMS MODEL FIX

Replace these files:

1) D:\SchoolERP\exams\models.py
2) D:\SchoolERP\exams\admin.py

Then run:

python manage.py makemigrations exams
python manage.py migrate
python manage.py check

Important:
Your current D:\SchoolERP\exams\models.py contains attendance models by mistake.
That is why Django says: cannot import name 'Exam' from 'exams.models'
