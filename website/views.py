from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone


from .forms import AdmissionForm, ContactMessageForm
from .models import DownloadFile
from .models import Gallery
from .models import (
    Admission,
    ContactMessage,
    HomeSlider,
    Notice,
    Gallery,
    SchoolEvent,
    Infrastructure,
    WhyChoose,
)

from students.models import Student
from academics.models import Class, AcademicSession


def website_home(request):
    sliders = HomeSlider.objects.filter(is_active=True).order_by('order', '-id')
    notices = Notice.objects.filter(is_active=True).order_by('order', '-created_at')
    important_notices = notices.filter(is_important=True)

    galleries = Gallery.objects.filter(is_active=True).order_by('order', '-id')[:8]
    events = SchoolEvent.objects.filter(is_active=True).order_by('order', '-event_date', '-id')[:3]
    infrastructures = Infrastructure.objects.filter(is_active=True).order_by('order', '-id')[:6]
    why_choose_items = WhyChoose.objects.filter(is_active=True).order_by('order', '-id')[:6]

    return render(request, 'website/home.html', {
        'sliders': sliders,
        'notices': notices,
        'important_notices': important_notices,
        'galleries': galleries,
        'events': events,
        'infrastructures': infrastructures,
        'why_choose_items': why_choose_items,
    })


def website_about(request):
    return render(request, 'website/about.html')


def website_admission(request):
    if request.method == 'POST':
        form = AdmissionForm(request.POST, request.FILES)

        if form.is_valid():
            admission = form.save()
            messages.success(request, "Application Submitted Successfully!")
            return redirect('admission_print', pk=admission.pk)

        if hasattr(form, 'existing_admission'):
            messages.warning(request, "You have already applied. Showing previous application.")
            return redirect('admission_print', pk=form.existing_admission.pk)

        messages.error(request, "Form submission failed. Please check the details.")
    else:
        form = AdmissionForm()

    return render(request, 'website/admission.html', {'form': form})


def admission_list(request):
    admissions = Admission.objects.all().order_by('-created_at')
    return render(request, 'website/admission_list.html', {
        'admissions': admissions
    })


def admission_approve(request, pk):
    admission = get_object_or_404(Admission, pk=pk)

    if admission.status == 'Approved' and admission.student_id:
        messages.warning(request, "This admission is already approved.")
        return redirect('admission_list')

    class_obj = Class.objects.filter(
        class_name__iexact=admission.student_class.strip()
    ).first()

    if not class_obj:
        messages.error(request, f"Class '{admission.student_class}' not found. Please create this class first in Academics.")
        return redirect('admission_list')

    session = AcademicSession.objects.filter(is_active=True).first()

    student = Student.objects.create(
        student_name=admission.student_name,
        admission_no=admission.admission_no,
        admission_date=timezone.now().date(),
        current_session=session,
        class_assigned=class_obj,
        father_name=admission.father_name,
        mother_name=admission.mother_name,
        phone=admission.mobile,
        gender=admission.gender,
        date_of_birth=admission.date_of_birth,
        aadhaar_number=admission.aadhaar_no,
        transport_required=admission.transport_required,
        previous_school=admission.previous_school,
        address=admission.address,
        photo=admission.student_photo,
        is_active=True,
    )

    admission.status = 'Approved'
    admission.student_id = student.student_id
    admission.registration_no = student.registration_no
    admission.save()

    messages.success(request, f"Admission approved. Student created: {student.student_id}")
    return redirect('admission_list')


def website_contact(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been submitted successfully!")
            return redirect('website_contact')
        else:
            messages.error(request, "Message submission failed. Please check the form.")
    else:
        form = ContactMessageForm()

    return render(request, 'website/contact.html', {
        'form': form
    })


def contact_message_list(request):
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    return render(request, 'website/contact_message_list.html', {
        'messages_list': messages_list
    })


def admission_print(request, pk):
    admission = get_object_or_404(Admission, pk=pk)
    return render(request, 'website/admission_print.html', {
        'admission': admission
    })


def contact_mark_read(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.is_read = True
    msg.save(update_fields=['is_read'])
    messages.success(request, "Message marked as read.")
    return redirect('contact_message_list')


def contact_delete(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.delete()
    messages.success(request, "Message deleted successfully.")
    return redirect('contact_message_list')

from django.shortcuts import render
from .models import Gallery


def gallery_page(request):
    galleries = Gallery.objects.filter(is_active=True).order_by('order', '-id')
    return render(request, 'website/gallery.html', {
        'galleries': galleries
    })

def download_list(request):
    downloads = DownloadFile.objects.filter(is_active=True).order_by('order', '-created_at')

    return render(request, 'website/download_list.html', {
        'downloads': downloads
    })

def gallery_list(request):
    galleries = Gallery.objects.filter(is_active=True).order_by('order', '-id')

    return render(request, 'website/gallery_list.html', {
        'galleries': galleries
    })