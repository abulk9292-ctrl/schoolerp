from django.db import models


class GeneralSetting(models.Model):

    DAY_CHOICES = [
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ]

    school_name = models.CharField(
        max_length=200,
        default="AL RAHMAN MISSION"
    )

    principal_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    principal_signature = models.ImageField(
        upload_to="principal_sign/",
        blank=True,
        null=True
    )

    school_logo = models.ImageField(
        upload_to="school_logo/",
        blank=True,
        null=True
    )

    school_header = models.ImageField(
        upload_to="school_header/",
        blank=True,
        null=True
    )

    weekly_holiday = models.CharField(
        max_length=20,
        choices=DAY_CHOICES,
        default="Monday",
        help_text="Main weekly holiday for school"
    )

    half_day_enabled = models.BooleanField(
        default=True
    )

    half_day = models.CharField(
        max_length=20,
        choices=DAY_CHOICES,
        default="Friday",
        blank=True,
        null=True,
        help_text="Half-day school day"
    )

    count_holiday_attendance = models.BooleanField(
        default=False,
        help_text="If enabled, holiday will be counted in attendance reports"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "General Setting"
        verbose_name_plural = "General Settings"

    def __str__(self):
        return self.school_name

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj