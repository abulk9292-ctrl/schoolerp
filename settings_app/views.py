from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import GeneralSetting
from .forms import GeneralSettingForm


@login_required
def general_settings(request):

    settings_obj, created = GeneralSetting.objects.get_or_create(id=1)

    form = GeneralSettingForm(
        request.POST or None,
        request.FILES or None,
        instance=settings_obj
    )

    if request.method == "POST":

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "General settings updated successfully."
            )

            return redirect('general_settings')

    return render(request, 'settings_app/general_settings.html', {
        'form': form
    })