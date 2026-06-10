from django.db import models
from django.utils import timezone

from students.models import Student


CERTIFICATE_TYPES = (
    ("TC", "Transfer Certificate"),
    ("CHARACTER", "Character Certificate"),
    ("BONAFIDE", "Bonafide Certificate"),
    ("STUDY", "Study Certificate"),
    ("FEE_CLEARANCE", "Fee Clearance Certificate"),
    ("CUSTOM", "Custom Certificate"),
)


class Certificate(models.Model):
    certificate_no = models.CharField(
        max_length=50,
        unique=True,
        blank=True
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="certificates"
    )

    certificate_type = models.CharField(
        max_length=30,
        choices=CERTIFICATE_TYPES
    )

    title = models.CharField(
        max_length=150,
        blank=True
    )

    # ✅ Global selected session store here
    session = models.CharField(
        max_length=20,
        blank=True
    )

    issue_date = models.DateField(
        default=timezone.now
    )

    reason = models.CharField(
        max_length=255,
        blank=True
    )

    conduct = models.CharField(
        max_length=255,
        default="Good"
    )

    remarks = models.TextField(
        blank=True
    )

    custom_body = models.TextField(
        blank=True
    )

    qr_code = models.ImageField(
        upload_to="certificates/qr/",
        blank=True,
        null=True
    )

    is_printed = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["certificate_no"]),
            models.Index(fields=["session"]),
            models.Index(fields=["certificate_type"]),
            models.Index(fields=["issue_date"]),
        ]

    def save(self, *args, **kwargs):
        if not self.certificate_no:
            last = Certificate.objects.order_by("-id").first()
            next_id = 1

            if last:
                next_id = last.id + 1

            self.certificate_no = f"ARM-CERT-{next_id:06d}"

        if not self.title:
            self.title = dict(CERTIFICATE_TYPES).get(
                self.certificate_type,
                "Certificate"
            )

        if not self.session and self.student and self.student.current_session:
            self.session = str(self.student.current_session)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.certificate_no} - {self.student}"