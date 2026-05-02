from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import FeeCollection, FeeStructure
from .forms import FeeCollectionForm, FeeStructureForm
from academics.models import Class, AcademicSession
from students.models import Student


def get_active_session():
    return AcademicSession.objects.filter(is_active=True).first()


def zero_fee_response():
    return JsonResponse({
        'monthly_fee': '0.00',
        'admission_fee': '0.00',
        'registration_fee': '0.00',
        'art_material': '0.00',
        'transport_fee': '0.00',
        'books_fee': '0.00',
        'uniform_fee': '0.00',
    })


@login_required
def fee_list(request):
    selected_class = request.GET.get('class_id')
    selected_date = request.GET.get('payment_date')
    selected_session = request.GET.get('session_id')

    active_session = get_active_session()

    fees = FeeCollection.objects.select_related(
        'student',
        'student__class_assigned',
        'session'
    ).all().order_by('-payment_date', '-id')

    if selected_session:
        fees = fees.filter(session_id=selected_session)
    elif active_session:
        fees = fees.filter(session=active_session)

    if selected_class:
        fees = fees.filter(student__class_assigned_id=selected_class)

    if selected_date:
        fees = fees.filter(payment_date=selected_date)

    classes = Class.objects.all().order_by('class_name')
    sessions = AcademicSession.objects.all().order_by('-start_date')

    totals = fees.aggregate(
        total_fee=Sum('total_amount'),
        total_discount=Sum('discount_amount'),
        total_paid=Sum('deposit_amount'),
        total_due=Sum('due_balance'),
    )

    context = {
        'fees': fees,
        'classes': classes,
        'sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
        'selected_class': selected_class,
        'selected_date': selected_date,
        'total_fee': totals['total_fee'] or 0,
        'total_discount': totals['total_discount'] or 0,
        'total_paid': totals['total_paid'] or 0,
        'total_due': totals['total_due'] or 0,
    }
    return render(request, 'fees/fee_list.html', context)


@login_required
def fee_add(request):
    if request.method == 'POST':
        form = FeeCollectionForm(request.POST, user=request.user)
        if form.is_valid():
            fee = form.save(commit=False)

            if not fee.session:
                fee.session = get_active_session()

            if not request.user.is_superuser and not request.user.has_perm('fees.can_change_fee_date'):
                fee.payment_date = timezone.now().date()

            fee.save()
            messages.success(request, 'Fee collected successfully.')
            return redirect('fee_receipt', pk=fee.pk)
    else:
        form = FeeCollectionForm(user=request.user)

    return render(request, 'fees/fee_form.html', {
        'form': form,
        'page_title': 'Collect Fees'
    })


@login_required
def fee_edit(request, pk):
    fee = get_object_or_404(FeeCollection, pk=pk)

    if request.method == 'POST':
        form = FeeCollectionForm(request.POST, instance=fee, user=request.user)
        if form.is_valid():
            fee = form.save(commit=False)

            if not request.user.is_superuser and not request.user.has_perm('fees.can_change_fee_date'):
                fee.payment_date = timezone.now().date()

            fee.save()
            messages.success(request, 'Fee updated successfully.')
            return redirect('fee_receipt', pk=fee.pk)
    else:
        form = FeeCollectionForm(instance=fee, user=request.user)

    return render(request, 'fees/fee_form.html', {
        'form': form,
        'page_title': 'Edit Fee Collection'
    })


@login_required
def fee_delete(request, pk):
    fee = get_object_or_404(FeeCollection, pk=pk)

    if request.method == 'POST':
        fee.delete()
        messages.success(request, 'Fee deleted successfully.')
        return redirect('fee_list')

    return render(request, 'fees/fee_delete.html', {'fee': fee})


@login_required
def fee_receipt(request, pk):
    fee = get_object_or_404(
        FeeCollection.objects.select_related(
            'student',
            'student__class_assigned',
            'session'
        ),
        pk=pk
    )
    return render(request, 'fees/fee_receipt.html', {'fee': fee})


@login_required
def get_student_old_due(request):
    student_id = request.GET.get('student_id')
    session_id = request.GET.get('session_id')

    if not student_id:
        return JsonResponse({'previous_balance': '0.00'})

    fee_qs = FeeCollection.objects.filter(student_id=student_id)

    if session_id:
        fee_qs = fee_qs.filter(session_id=session_id)
    else:
        active_session = get_active_session()
        if active_session:
            fee_qs = fee_qs.filter(session=active_session)

    latest_fee = fee_qs.order_by('-payment_date', '-id').first()

    if latest_fee:
        previous_balance = latest_fee.due_balance or Decimal('0.00')
    else:
        previous_balance = Decimal('0.00')

    return JsonResponse({
        'previous_balance': str(previous_balance)
    })


@login_required
def get_student_fee_structure(request):
    student_id = request.GET.get('student_id')
    session_id = request.GET.get('session_id')

    if not student_id:
        return zero_fee_response()

    student = Student.objects.select_related('class_assigned').filter(pk=student_id).first()

    if not student or not student.class_assigned:
        return zero_fee_response()

    structure_qs = FeeStructure.objects.filter(
        class_assigned=student.class_assigned,
        is_active=True
    )

    if session_id:
        structure_qs = structure_qs.filter(session_id=session_id)
    else:
        active_session = get_active_session()
        if active_session:
            structure_qs = structure_qs.filter(session=active_session)

    structure = structure_qs.first()

    if structure:
        return JsonResponse({
            'monthly_fee': str(structure.monthly_fee),
            'admission_fee': str(structure.admission_fee),
            'registration_fee': str(structure.registration_fee),
            'art_material': str(structure.art_material),
            'transport_fee': str(structure.transport_fee),
            'books_fee': str(structure.books_fee),
            'uniform_fee': str(structure.uniform_fee),
        })

    return zero_fee_response()


@login_required
def fee_structure_list(request):
    structures = FeeStructure.objects.select_related(
        'class_assigned',
        'session'
    ).all().order_by('class_assigned__class_name')

    edit_id = request.GET.get('edit')
    edit_structure = None

    if edit_id:
        edit_structure = get_object_or_404(FeeStructure, pk=edit_id)
        form = FeeStructureForm(instance=edit_structure)
    else:
        form = FeeStructureForm()

    if request.method == 'POST':
        structure_id = request.POST.get('structure_id')

        if structure_id:
            structure = get_object_or_404(FeeStructure, pk=structure_id)
            form = FeeStructureForm(request.POST, instance=structure)
            success_message = 'Fee structure updated successfully.'
        else:
            form = FeeStructureForm(request.POST)
            success_message = 'Fee structure added successfully.'

        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect('fee_structure_list')

    return render(request, 'fees/fee_structure_list.html', {
        'form': form,
        'structures': structures,
        'edit_structure': edit_structure,
    })


@login_required
def fee_structure_delete(request, pk):
    structure = get_object_or_404(FeeStructure, pk=pk)
    structure.delete()
    messages.success(request, 'Fee structure deleted successfully.')
    return redirect('fee_structure_list')


@login_required
def fee_structure_edit(request, pk):
    structure = get_object_or_404(FeeStructure, pk=pk)

    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=structure)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee Structure updated successfully")
            return redirect('fee_structure_list')
    else:
        form = FeeStructureForm(instance=structure)

    return render(request, 'fees/fee_structure_form.html', {
        'form': form
    })


@login_required
def defaulters_list(request):
    selected_class = request.GET.get('class_id')
    selected_month = request.GET.get('fees_month')
    selected_session = request.GET.get('session_id')

    active_session = get_active_session()
    classes = Class.objects.all().order_by('class_name')
    sessions = AcademicSession.objects.all().order_by('-start_date')

    fee_qs = FeeCollection.objects.select_related(
        'student',
        'student__class_assigned',
        'session'
    ).filter(due_balance__gt=0).order_by(
        'student__class_assigned__class_name',
        'student__roll_no',
        'student__student_name',
        '-payment_date',
        '-id'
    )

    if selected_session:
        fee_qs = fee_qs.filter(session_id=selected_session)
    elif active_session:
        fee_qs = fee_qs.filter(session=active_session)

    if selected_class:
        fee_qs = fee_qs.filter(student__class_assigned_id=selected_class)

    if selected_month:
        fee_qs = fee_qs.filter(fees_month=selected_month)

    totals = fee_qs.aggregate(total_due=Sum('due_balance'))

    context = {
        'defaulters': fee_qs,
        'classes': classes,
        'sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
        'selected_class': selected_class,
        'selected_month': selected_month,
        'total_due': totals['total_due'] or 0,
        'total_students': fee_qs.count(),
        'month_choices': FeeCollectionForm.MONTH_CHOICES,
    }
    return render(request, 'fees/defaulters_list.html', context)


@login_required
def pending_amount_list(request):
    selected_class = request.GET.get('class_id')
    selected_session = request.GET.get('session_id')
    search_query = request.GET.get('q', '').strip().lower()

    active_session = get_active_session()
    classes = Class.objects.all().order_by('class_name')
    sessions = AcademicSession.objects.all().order_by('-start_date')

    students = Student.objects.select_related('class_assigned', 'current_session').filter(
        is_active=True
    ).order_by(
        'class_assigned__class_name',
        'roll_no',
        'student_name'
    )

    if selected_session:
        students = students.filter(current_session_id=selected_session)
    elif active_session:
        students = students.filter(current_session=active_session)

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    months = [
        'April', 'May', 'June', 'July', 'August', 'September',
        'October', 'November', 'December', 'January', 'February', 'March'
    ]

    rows = []
    grand_total_due = Decimal('0.00')

    for student in students:
        searchable_text = f"""
        {student.student_id or ''}
        {student.student_name or ''}
        {student.father_name or ''}
        {student.guardian_name or ''}
        {student.phone or ''}
        {student.class_assigned.class_name if student.class_assigned else ''}
        """.lower()

        if search_query and search_query not in searchable_text:
            continue

        structure_qs = FeeStructure.objects.filter(
            class_assigned=student.class_assigned,
            is_active=True
        )

        if selected_session:
            structure_qs = structure_qs.filter(session_id=selected_session)
        elif active_session:
            structure_qs = structure_qs.filter(session=active_session)

        structure = structure_qs.first()
        monthly_fee = structure.monthly_fee if structure else Decimal('0.00')

        fee_qs = FeeCollection.objects.filter(student=student)

        if selected_session:
            fee_qs = fee_qs.filter(session_id=selected_session)
        elif active_session:
            fee_qs = fee_qs.filter(session=active_session)

        latest_student_fee = fee_qs.order_by('-payment_date', '-id').first()
        balance = latest_student_fee.due_balance if latest_student_fee else Decimal('0.00')

        student_row = {
            'student': student,
            'month_values': {},
            'balance': balance,
            'total_pending': Decimal('0.00'),
        }

        for month in months:
            fee = fee_qs.filter(
                fees_month=month
            ).order_by('-payment_date', '-id').first()

            if fee:
                due = fee.due_balance or Decimal('0.00')

                if due > 0:
                    student_row['month_values'][month] = due
                    student_row['total_pending'] += due
                else:
                    student_row['month_values'][month] = 'Paid'
            else:
                if monthly_fee > 0:
                    student_row['month_values'][month] = monthly_fee
                    student_row['total_pending'] += monthly_fee
                else:
                    student_row['month_values'][month] = '-'

        if student_row['total_pending'] > 0:
            grand_total_due += student_row['total_pending']
            rows.append(student_row)

    context = {
        'classes': classes,
        'sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
        'selected_class': selected_class,
        'search_query': request.GET.get('q', ''),
        'months': months,
        'rows': rows,
        'total_students': len(rows),
        'grand_total_due': grand_total_due,
    }

    return render(request, 'fees/pending_amount_list.html', context)


@login_required
def fee_demand_slip(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    active_session = get_active_session()

    structure_qs = FeeStructure.objects.filter(
        class_assigned=student.class_assigned,
        is_active=True
    )

    if active_session:
        structure_qs = structure_qs.filter(session=active_session)

    structure = structure_qs.first()

    last_fee_qs = FeeCollection.objects.filter(student=student)

    if active_session:
        last_fee_qs = last_fee_qs.filter(session=active_session)

    last_fee = last_fee_qs.order_by('-payment_date', '-id').first()
    previous_due = last_fee.due_balance if last_fee else 0

    context = {
        'student': student,
        'structure': structure,
        'previous_due': previous_due,
        'active_session': active_session,
    }

    return render(request, 'fees/fee_demand_slip.html', context)


@login_required
def bulk_demand_slip_page(request):
    classes = Class.objects.all().order_by('id')
    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = get_active_session()

    students = []
    selected_class = request.GET.get('class_id')
    selected_session = request.GET.get('session_id')

    if selected_class:
        students = Student.objects.filter(
            class_assigned_id=selected_class,
            is_active=True
        ).order_by('roll_no', 'student_name')

        if selected_session:
            students = students.filter(current_session_id=selected_session)
        elif active_session:
            students = students.filter(current_session=active_session)

    return render(request, 'fees/bulk_demand_slip_page.html', {
        'classes': classes,
        'sessions': sessions,
        'active_session': active_session,
        'students': students,
        'selected_class': selected_class,
        'selected_session': selected_session,
    })


@login_required
def bulk_demand_slip_print(request):
    if request.method != 'POST':
        return redirect('bulk_demand_slip_page')

    active_session = get_active_session()
    selected_session = request.POST.get('session_id')

    student_ids = request.POST.getlist('student_ids')
    students = Student.objects.filter(id__in=student_ids).order_by('class_assigned', 'roll_no')

    slips = []

    for student in students:
        structure_qs = FeeStructure.objects.filter(
            class_assigned=student.class_assigned,
            is_active=True
        )

        if selected_session:
            structure_qs = structure_qs.filter(session_id=selected_session)
        elif active_session:
            structure_qs = structure_qs.filter(session=active_session)

        structure = structure_qs.first()

        last_fee_qs = FeeCollection.objects.filter(student=student)

        if selected_session:
            last_fee_qs = last_fee_qs.filter(session_id=selected_session)
        elif active_session:
            last_fee_qs = last_fee_qs.filter(session=active_session)

        last_fee = last_fee_qs.order_by('-payment_date', '-id').first()
        previous_due = last_fee.due_balance if last_fee else 0

        monthly_fee = structure.monthly_fee if structure else 0
        transport_fee = structure.transport_fee if structure else 0
        total_due = previous_due + monthly_fee + transport_fee

        slips.append({
            'student': student,
            'structure': structure,
            'previous_due': previous_due,
            'monthly_fee': monthly_fee,
            'transport_fee': transport_fee,
            'total_due': total_due,
        })

    return render(request, 'fees/bulk_demand_slip_print.html', {
        'slips': slips,
        'active_session': active_session,
    })