import os
import shutil
import datetime

from django.conf import settings
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def manual_backup(request):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = os.path.join(settings.BACKUP_ROOT, f'backup_{timestamp}')

        os.makedirs(backup_folder, exist_ok=True)

        # 📌 1. Database backup (SQLite)
        db_path = settings.DATABASES['default']['NAME']
        if os.path.exists(db_path):
            shutil.copy(db_path, os.path.join(backup_folder, 'db.sqlite3'))

        # 📌 2. Media backup
        media_path = settings.MEDIA_ROOT
        if os.path.exists(media_path):
            shutil.copytree(media_path, os.path.join(backup_folder, 'media'), dirs_exist_ok=True)

        # 📌 3. ZIP create
        zip_file = shutil.make_archive(backup_folder, 'zip', backup_folder)

        messages.success(request, "Backup created successfully!")

        return FileResponse(open(zip_file, 'rb'), as_attachment=True, filename=os.path.basename(zip_file))

    except Exception as e:
        return HttpResponse(f"Error: {e}")


@login_required
def backup_history(request):
    backups = []

    if os.path.exists(settings.BACKUP_ROOT):
        for file_name in os.listdir(settings.BACKUP_ROOT):
            if file_name.endswith('.zip'):
                file_path = os.path.join(settings.BACKUP_ROOT, file_name)
                backups.append({
                    'name': file_name,
                    'size': round(os.path.getsize(file_path) / (1024 * 1024), 2),
                    'created': datetime.datetime.fromtimestamp(os.path.getctime(file_path)),
                })

    backups = sorted(backups, key=lambda x: x['created'], reverse=True)

    return render(request, 'backup/backup_history.html', {
        'backups': backups
    })


@login_required
def download_backup(request, file_name):
    file_path = os.path.join(settings.BACKUP_ROOT, file_name)

    if not os.path.exists(file_path):
        raise Http404("Backup file not found")

    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_name)