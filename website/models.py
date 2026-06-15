from django.db import models


class Admission(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    admission_no = models.CharField(max_length=100, blank=True, null=True, unique=True)

    student_name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200)
    mother_name = models.CharField(max_length=200, blank=True, null=True)

    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)

    student_class = models.CharField(max_length=50)

    aadhaar_no = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=15)
    guardian_mobile = models.CharField(max_length=15, blank=True, null=True)

    address = models.TextField()
    previous_school = models.CharField(max_length=250, blank=True, null=True)

    transport_required = models.BooleanField(default=False)
    hostel_required = models.BooleanField(default=False)

    student_photo = models.ImageField(upload_to='admission_photos/', blank=True, null=True)

    student_id = models.CharField(max_length=100, blank=True, null=True)
    registration_no = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.admission_no:
            Admission.objects.filter(id=self.id).update(
                admission_no=f"ARM-ADM-{self.id:06d}"
            )
            self.admission_no = f"ARM-ADM-{self.id:06d}"

    def __str__(self):
        return f"{self.student_name} - {self.admission_no}"
    
class Student(models.Model):
    admission_no = models.CharField(max_length=100, unique=True)
    student_name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200)
    mother_name = models.CharField(max_length=200, blank=True, null=True)

    student_class = models.CharField(max_length=50)

    mobile = models.CharField(max_length=15)
    guardian_mobile = models.CharField(max_length=15, blank=True, null=True)

    address = models.TextField()

    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)

    student_photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)

    session = models.CharField(max_length=50, default='2025-26')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.admission_no}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.mobile}"


class HomeSlider(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    image = models.ImageField(upload_to='website_sliders/')
    button_text = models.CharField(max_length=100, blank=True, null=True)
    button_link = models.CharField(max_length=300, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title


class Notice(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)

    notice_date = models.DateField(blank=True, null=True)

    is_important = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class Gallery(models.Model):
    CATEGORY_CHOICES = [
        ('Campus', 'Campus'),
        ('Classroom', 'Classroom'),
        ('Hostel', 'Hostel'),
        ('Transport', 'Transport'),
        ('Event', 'Event'),
        ('Sports', 'Sports'),
        ('Other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Campus')

    image = models.ImageField(upload_to='website_gallery/', blank=True, null=True)
    video = models.FileField(upload_to='website_gallery_videos/', blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title


class SchoolEvent(models.Model):
    title = models.CharField(max_length=200)
    event_date = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='website_events/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-event_date', '-id']

    def __str__(self):
        return self.title


class Infrastructure(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='website_infrastructure/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title


class WhyChoose(models.Model):
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Example: 📘, 🏫, 🎯")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title
    
class DownloadFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('Result', 'Result'),
        ('Routine', 'Routine'),
        ('Notice', 'Notice'),
        ('Syllabus', 'Syllabus'),
        ('Form', 'Admission Form'),
        ('Fee', 'Fee Structure'),
        ('Holiday', 'Holiday List'),
        ('Book', 'Book List'),
        ('Prospectus', 'Prospectus'),
        ('Other', 'Other'),
    ]

    title = models.CharField(max_length=250)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES, default='Other')
    pdf_file = models.FileField(upload_to='website_downloads/')
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title

class WebsiteSetting(models.Model):
    school_name = models.CharField(
        max_length=200,
        default="AL RAHMAN MISSION"
    )


    logo = models.ImageField(
        upload_to="website/logo/",
        blank=True,
        null=True
    )

    favicon = models.ImageField(
        upload_to="website/favicon/",
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    whatsapp_number = models.CharField(
        max_length=20,
        blank=True
    )

    website_url = models.CharField(
        max_length=200,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    facebook = models.URLField(
        blank=True
    )

    youtube = models.URLField(
        blank=True
    )

    instagram = models.URLField(
        blank=True
    )

    about_school = models.TextField(
        blank=True
    )

    mission = models.TextField(
        blank=True
    )

    vision = models.TextField(
        blank=True
    )

    principal_name = models.CharField(
        max_length=200,
        blank=True
    )

    principal_message = models.TextField(
        blank=True
    )

    footer_text = models.TextField(
        blank=True
    )

    maintenance_mode = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.school_name

class WebsiteTeacher(models.Model):
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=200)
    qualification = models.CharField(max_length=200, blank=True)
    photo = models.ImageField(upload_to='website/teachers/')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class WebsiteTopper(models.Model):
    student_name = models.CharField(max_length=200)
    exam_name = models.CharField(max_length=200)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    photo = models.ImageField(upload_to='website/toppers/')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'student_name']

    def __str__(self):
        return self.student_name


class WebsiteCounter(models.Model):
    title = models.CharField(max_length=100)
    value = models.PositiveIntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=200, blank=True)
    photo = models.ImageField(
        upload_to='website/testimonials/',
        blank=True,
        null=True
    )
    review = models.TextField()
    rating = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PopupNotice(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()

    image = models.ImageField(
        upload_to='website/popup/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title