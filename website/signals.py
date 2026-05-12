from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Admission
from students.models import Student
from academics.models import Class, AcademicSession
from datetime import date


@receiver(post_save, sender=Admission)
def create_student_on_approval(sender, instance, created, **kwargs):
    if instance.status == 'Approved':

        if not Student.objects.filter(admission_no=instance.admission_no).exists():

            class_obj = Class.objects.filter(
                class_name__iexact=instance.student_class
            ).first()

            active_session = AcademicSession.objects.filter(
                is_active=True
            ).first()

            if class_obj:
                Student.objects.create(
                    admission_no=instance.admission_no,
                    student_name=instance.student_name,
                    father_name=instance.father_name,
                    mother_name=instance.mother_name,
                    phone=instance.mobile,
                    address=instance.address,
                    date_of_birth=instance.date_of_birth,
                    gender=instance.gender,
                    aadhaar_number=instance.aadhaar_no,
                    previous_school=instance.previous_school,
                    transport_required=instance.transport_required,
                    photo=instance.student_photo,
                    class_assigned=class_obj,
                    current_session=active_session,
                    admission_date=date.today(),
                )