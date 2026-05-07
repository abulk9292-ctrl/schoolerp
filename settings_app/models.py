from django.db import models


class GeneralSetting(models.Model):

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
        upload_to='principal_sign/',
        blank=True,
        null=True
    )

    school_logo = models.ImageField(
        upload_to='school_logo/',
        blank=True,
        null=True
    )

    school_header = models.ImageField(
        upload_to='school_header/',
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.school_name