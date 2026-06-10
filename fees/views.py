from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import FeeCollection, FeeStructure, FeeFollowUp
from .forms import FeeCollectionForm, FeeStructureForm, FeeFollowUpForm
from academics.models import Class, AcademicSession
from students.models import Student
from core.views import get_selected_session


def get_active_session(request=None):

    if request:

        selected_session = get_selected_session(request)

        session = AcademicSession.objects.filter(
            session_name=selected_session
        ).first()

        if session:
            return session

    return AcademicSession.objects.filter(
        is_active=True
    ).first()


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
    selected_section = request.GET.get('section')
    selected_date = request.GET.get('payment_date')
    selected_session = request.GET.get('session_id')

    active_session = get_active_session(request)

    fees = FeeCollection.objects.filter(is_deleted=False).select_related(
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

    if selected_section:
        fees = fees.filter(section=selected_section)

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

    return render(request, 'fees/fee_list.html', {
        'fees': fees,
        'classes': classes,
        'sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
        'selected_class': selected_class,
        'selected_section': selected_section,
        'selected_date': selected_date,
        'total_fee': totals['total_fee'] or 0,
        'total_discount': totals['total_discount'] or 0,
        'total_paid': totals['total_paid'] or 0,
        'total_due': totals['total_due'] or 0,
    })


@login_required
def fee_add(request):
    if request.method == 'POST':
        form = FeeCollectionForm(request.POST, user=request.user)
        if form.is_valid():
            fee = form.save(commit=False)

            if not fee.session:
                active_session = get_active_session(request)
                fee.session = active_session

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
    fee = get_object_or_404(
        FeeCollection,
        pk=pk
    )

    if request.method == 'POST':

        fee.is_deleted = True
        fee.deleted_at = timezone.now()
        fee.deleted_by = request.user
        fee.save()

        messages.success(
            request,
            'Fee moved to recycle bin successfully.'
        )

        return redirect('fee_list')

    return render(
        request,
        'fees/fee_delete.html',
        {'fee': fee}
    )


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
        active_session = get_active_session(request)
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
        section=student.section or "",
        is_active=True
    )

    if session_id:
        structure_qs = structure_qs.filter(session_id=session_id)
    else:
        active_session = get_active_session(request)
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
    selected_section = request.GET.get('section')
    selected_month = request.GET.get('fees_month')
    selected_session = request.GET.get('session_id')

    active_session = get_active_session(request)
    classes = Class.objects.all().order_by('class_name')
    sessions = AcademicSession.objects.all().order_by('-start_date')

    fee_qs = FeeCollection.objects.select_related(
        'student',
        'student__class_assigned',
        'session'
    ).filter(due_balance__gt=0).order_by(
        'student__class_assigned__class_name',
        'student__section',
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

    if selected_section:
        fee_qs = fee_qs.filter(section=selected_section)

    if selected_month:
        fee_qs = fee_qs.filter(fees_month=selected_month)

    totals = fee_qs.aggregate(total_due=Sum('due_balance'))

    return render(request, 'fees/defaulters_list.html', {
        'defaulters': fee_qs,
        'classes': classes,
        'sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
        'selected_class': selected_class,
        'selected_section': selected_section,
        'selected_month': selected_month,
        'total_due': totals['total_due'] or 0,
        'total_students': fee_qs.count(),
        'month_choices': FeeCollectionForm.MONTH_CHOICES,
    })


@login_required
def pending_amount_list(request):
    selected_class = request.GET.get('class_id')
    selected_section = request.GET.get('section')
    selected_session = request.GET.get('session_id')
    search_query = request.GET.get('q', '').strip().lower()

    active_session = get_active_session(request)
    classes = Class.objects.all().order_by('class_name')
    sessions = AcademicSession.objects.all().order_by('-start_date')

    students = Student.objects.select_related(
        'class_assigned',
        'current_session'
    ).filter(is_active=True).order_by(
        'class_assigned__class_name',
        'section',
        'roll_no',
        'student_name'
    )

    if selected_session:
        students = students.filter(current_session_id=selected_session)
    elif active_session:
        students = students.filter(current_session=active_session)

    if selected_class:
        students = students.filter(class_assigned_id=selected_class)

    if selected_section:
        students = students.filter(section=selected_section)

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
        {student.section or ''}
        {student.class_assigned.class_name if student.class_assigned else ''}
        """.lower()

        if search_query and search_query not in searchable_text:
            continue

        structure_qs = FeeStructure.objects.filter(
            class_assigned=student.class_assigned,
            section=student.section or "",
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

    return render(request, 'fees/pending_amount_list.html', {
        'classes': classes,
        'sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
        'selected_class': selected_class,
        'selected_section': selected_section,
        'search_query': request.GET.get('q', ''),
        'months': months,
        'rows': rows,
        'total_students': len(rows),
        'grand_total_due': grand_total_due,
    })


@login_required
def fee_demand_slip(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    active_session = get_active_session(request)

    structure_qs = FeeStructure.objects.filter(
        class_assigned=student.class_assigned,
        section=student.section or "",
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

    return render(request, 'fees/fee_demand_slip.html', {
        'student': student,
        'structure': structure,
        'previous_due': previous_due,
        'active_session': active_session,
    })

@login_required
def bulk_demand_slip_page(request):
    classes = Class.objects.all().order_by('id')
    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = get_active_session(request)

    students = []
    selected_class = request.GET.get('class_id')
    selected_section = request.GET.get('section')
    selected_session = request.GET.get('session_id')

    if selected_class:
        students = Student.objects.filter(
            class_assigned_id=selected_class,
            is_active=True
        ).order_by('section', 'roll_no', 'student_name')

        if selected_section:
            students = students.filter(section=selected_section)

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
        'selected_section': selected_section,
        'selected_session': selected_session,
    })


@login_required
def bulk_demand_slip_print(request):
    if request.method != 'POST':
        return redirect('bulk_demand_slip_page')

    active_session = get_active_session(request)
    selected_session = request.POST.get('session_id')

    student_ids = request.POST.getlist('student_ids')

    students = Student.objects.filter(
        id__in=student_ids
    ).order_by(
        'class_assigned',
        'section',
        'roll_no'
    )

    slips = []

    for student in students:
        structure_qs = FeeStructure.objects.filter(
            class_assigned=student.class_assigned,
            section=student.section or "",
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


@login_required
def check_paid_month(request):
    student_id = request.GET.get('student_id')
    month = request.GET.get('month')

    if not student_id or not month:
        return JsonResponse({'already_paid': False})

    # ✅ Active session
    session = get_active_session(request)

    qs = FeeCollection.objects.filter(
        student_id=student_id,
        fees_month=month
    )

    # ✅ Session wise filter
    if session:
        qs = qs.filter(session=session)

    return JsonResponse({
        'already_paid': qs.exists()
    })

# ==========================================
# STUDENT PAYMENT STATEMENT
# ==========================================

@login_required
def student_payment_statement(request, student_id):

    student = get_object_or_404(
        Student.objects.select_related(
            'class_assigned',
            'current_session'
        ),
        pk=student_id
    )

    selected_session = request.GET.get('session_id')

    active_session = get_active_session(request)

    payments = FeeCollection.objects.filter(
        student=student
    ).select_related(
        'session'
    ).order_by(
        'payment_date',
        'id'
    )

    if selected_session:
        payments = payments.filter(
            session_id=selected_session
        )

    elif active_session:
        payments = payments.filter(
            session=active_session
        )

    totals = payments.aggregate(
        total_fee=Sum('total_amount'),
        total_discount=Sum('discount_amount'),
        total_paid=Sum('deposit_amount'),
        total_due=Sum('due_balance'),
    )

    sessions = AcademicSession.objects.all().order_by(
        '-start_date'
    )

    return render(
        request,
        'fees/student_payment_statement.html',
        {
            'student': student,
            'payments': payments,

            'sessions': sessions,
            'active_session': active_session,
            'selected_session': selected_session,

            'total_fee': totals['total_fee'] or 0,
            'total_discount': totals['total_discount'] or 0,
            'total_paid': totals['total_paid'] or 0,
            'total_due': totals['total_due'] or 0,
        }
    )


# =========================================================
# FEE FOLLOW-UP / PROMISE TO PAY
# =========================================================

def get_student_latest_due(student, session=None):
    qs = FeeCollection.objects.filter(student=student)

    if session:
        qs = qs.filter(session=session)

    last_fee = qs.order_by('-payment_date', '-id').first()

    if last_fee:
        return last_fee.due_balance or Decimal('0.00')

    return Decimal('0.00')


@login_required
def fee_followup_dashboard(request):
    today = timezone.now().date()
    active_session = get_active_session(request)

    qs = FeeFollowUp.objects.select_related(
        'student',
        'student__class_assigned',
        'session'
    ).all()

    if active_session:
        qs = qs.filter(session=active_session)

    today_followups = qs.filter(
        promise_date=today
    ).exclude(status__in=['PAID', 'CANCELLED'])

    overdue_followups = qs.filter(
        promise_date__lt=today
    ).exclude(status__in=['PAID', 'CANCELLED'])

    upcoming_followups = qs.filter(
        promise_date__gt=today
    ).exclude(status__in=['PAID', 'CANCELLED'])[:10]

    cards = {
        'today_count': today_followups.count(),
        'overdue_count': overdue_followups.count(),
        'call_count': today_followups.filter(followup_type='CALL').count(),
        'visit_count': today_followups.filter(followup_type='HOME_VISIT').count(),
        'today_amount': today_followups.aggregate(total=Sum('promise_amount'))['total'] or 0,
        'overdue_amount': overdue_followups.aggregate(total=Sum('promise_amount'))['total'] or 0,
    }

    return render(request, 'fees/fee_followup_dashboard.html', {
        'today': today,
        'active_session': active_session,
        'cards': cards,
        'today_followups': today_followups[:20],
        'overdue_followups': overdue_followups[:20],
        'upcoming_followups': upcoming_followups,
    })


@login_required
def fee_followup_list(request):
    today = timezone.now().date()
    active_session = get_active_session(request)

    status = request.GET.get('status', '')
    followup_type = request.GET.get('type', '')
    date_filter = request.GET.get('date_filter', '')
    selected_class = request.GET.get('class_id', '')
    selected_section = request.GET.get('section', '')
    q = request.GET.get('q', '').strip()

    followups = FeeFollowUp.objects.select_related(
        'student',
        'student__class_assigned',
        'session',
        'created_by',
    ).all()

    if active_session:
        followups = followups.filter(session=active_session)

    if status:
        followups = followups.filter(status=status)

    if followup_type:
        followups = followups.filter(followup_type=followup_type)

    if selected_class:
        followups = followups.filter(student__class_assigned_id=selected_class)

    if selected_section:
        followups = followups.filter(student__section=selected_section)

    if date_filter == 'today':
        followups = followups.filter(promise_date=today).exclude(status__in=['PAID', 'CANCELLED'])
    elif date_filter == 'overdue':
        followups = followups.filter(promise_date__lt=today).exclude(status__in=['PAID', 'CANCELLED'])
    elif date_filter == 'upcoming':
        followups = followups.filter(promise_date__gt=today).exclude(status__in=['PAID', 'CANCELLED'])

    if q:
        followups = followups.filter(
            Q(student__student_name__icontains=q) |
            Q(student__student_id__icontains=q) |
            Q(student__father_name__icontains=q) |
            Q(student__guardian_name__icontains=q) |
            Q(student__phone__icontains=q) |
            Q(parent_name__icontains=q) |
            Q(mobile__icontains=q) |
            Q(remark__icontains=q)
        )

    classes = Class.objects.all().order_by('class_name')

    summary = {
        'total': followups.count(),
        'pending': followups.filter(status='PENDING').count(),
        'today': followups.filter(promise_date=today).exclude(status__in=['PAID', 'CANCELLED']).count(),
        'overdue': followups.filter(promise_date__lt=today).exclude(status__in=['PAID', 'CANCELLED']).count(),
        'promise_amount': followups.aggregate(total=Sum('promise_amount'))['total'] or 0,
    }

    return render(request, 'fees/fee_followup_list.html', {
        'followups': followups,
        'classes': classes,
        'summary': summary,
        'today': today,
        'selected_status': status,
        'selected_type': followup_type,
        'date_filter': date_filter,
        'selected_class': selected_class,
        'selected_section': selected_section,
        'q': q,
        'status_choices': FeeFollowUp.STATUS_CHOICES,
        'type_choices': FeeFollowUp.FOLLOWUP_TYPE_CHOICES,
    })


@login_required
def fee_followup_add(request, student_id=None):
    initial = {}

    if student_id:
        student = get_object_or_404(Student, pk=student_id)
        active_session = get_active_session(request)
        due_amount = get_student_latest_due(student, active_session)

        initial = {
            'student': student,
            'session': active_session,
            'parent_name': getattr(student, 'guardian_name', None) or getattr(student, 'father_name', ''),
            'mobile': getattr(student, 'phone', ''),
            'due_amount': due_amount,
            'promise_amount': due_amount,
            'promise_date': timezone.now().date(),
            'next_action': 'Call parent / Visit home',
        }

    if request.method == 'POST':
        form = FeeFollowUpForm(request.POST, user=request.user)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.created_by = request.user
            if not followup.session:
                followup.session = get_active_session(request)
            followup.save()
            messages.success(request, 'Fee follow-up / promise added successfully.')
            return redirect('fee_followup_list')
    else:
        form = FeeFollowUpForm(initial=initial, user=request.user)

    return render(request, 'fees/fee_followup_form.html', {
        'form': form,
        'page_title': 'Add Fee Follow-up / Promise',
    })


@login_required
def fee_followup_edit(request, pk):
    followup = get_object_or_404(FeeFollowUp, pk=pk)

    if request.method == 'POST':
        form = FeeFollowUpForm(request.POST, instance=followup, user=request.user)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.save()
            messages.success(request, 'Fee follow-up updated successfully.')
            return redirect('fee_followup_list')
    else:
        form = FeeFollowUpForm(instance=followup, user=request.user)

    return render(request, 'fees/fee_followup_form.html', {
        'form': form,
        'followup': followup,
        'page_title': 'Edit Fee Follow-up / Promise',
    })


@login_required
def fee_followup_delete(request, pk):
    followup = get_object_or_404(FeeFollowUp, pk=pk)

    if request.method == 'POST':
        followup.delete()
        messages.success(request, 'Fee follow-up deleted successfully.')
        return redirect('fee_followup_list')

    return render(request, 'fees/fee_followup_delete.html', {
        'followup': followup
    })


@login_required
def fee_followup_mark_status(request, pk, status):
    followup = get_object_or_404(FeeFollowUp, pk=pk)

    allowed_status = [choice[0] for choice in FeeFollowUp.STATUS_CHOICES]

    if status in allowed_status:
        followup.status = status
        if status in ['PAID', 'CANCELLED']:
            followup.completed_at = timezone.now()
        followup.save()
        messages.success(request, f'Follow-up marked as {status}.')
    else:
        messages.error(request, 'Invalid follow-up status.')

    return redirect(request.META.get('HTTP_REFERER', 'fee_followup_list'))


@login_required
def fee_followup_print(request):
    today = timezone.now().date()
    active_session = get_active_session(request)

    status = request.GET.get('status', '')
    date_filter = request.GET.get('date_filter', '')

    followups = FeeFollowUp.objects.select_related(
        'student',
        'student__class_assigned',
        'session',
    ).all()

    if active_session:
        followups = followups.filter(session=active_session)

    if status:
        followups = followups.filter(status=status)

    if date_filter == 'today':
        followups = followups.filter(promise_date=today).exclude(status__in=['PAID', 'CANCELLED'])
        report_title = 'Today Fee Follow-up Report'
    elif date_filter == 'overdue':
        followups = followups.filter(promise_date__lt=today).exclude(status__in=['PAID', 'CANCELLED'])
        report_title = 'Overdue Fee Follow-up Report'
    elif date_filter == 'upcoming':
        followups = followups.filter(promise_date__gt=today).exclude(status__in=['PAID', 'CANCELLED'])
        report_title = 'Upcoming Fee Follow-up Report'
    else:
        report_title = 'Fee Follow-up Report'

    totals = followups.aggregate(
        due_total=Sum('due_amount'),
        promise_total=Sum('promise_amount')
    )

    return render(request, 'fees/fee_followup_print.html', {
        'followups': followups,
        'today': today,
        'active_session': active_session,
        'report_title': report_title,
        'due_total': totals['due_total'] or 0,
        'promise_total': totals['promise_total'] or 0,
    })

@login_required
def fee_recycle_bin(request):

    fees = FeeCollection.objects.filter(
        is_deleted=True
    ).select_related(
        'student',
        'deleted_by'
    ).order_by(
        '-deleted_at'
    )

    return render(
        request,
        'fees/fee_recycle_bin.html',
        {
            'fees': fees
        }
    )


@login_required
def fee_restore(request, pk):

    fee = get_object_or_404(
        FeeCollection,
        pk=pk,
        is_deleted=True
    )

    fee.is_deleted = False
    fee.deleted_at = None
    fee.deleted_by = None
    fee.save()

    messages.success(
        request,
        'Fee restored successfully.'
    )

    return redirect('fee_recycle_bin')


@login_required
def fee_permanent_delete(request, pk):

    # ONLY SUPER ADMIN CAN PERMANENT DELETE
    if not request.user.is_superuser:
        messages.error(
            request,
            "Only Super Admin can permanently delete records."
        )
        return redirect('fee_recycle_bin')

    fee = get_object_or_404(
        FeeCollection,
        pk=pk,
        is_deleted=True
    )

    # SECURITY: ONLY POST REQUEST
    if request.method != 'POST':
        messages.error(
            request,
            "Invalid request method."
        )
        return redirect('fee_recycle_bin')

    receipt_no = fee.receipt_no

    fee.delete()

    messages.success(
        request,
        f'Fee Receipt {receipt_no} permanently deleted successfully.'
    )

    return redirect('fee_recycle_bin')

@login_required
def fee_restore(request, pk):

    # ADMIN / SUPER ADMIN ONLY
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(
            request,
            "You are not authorized to restore deleted records."
        )
        return redirect('fee_recycle_bin')

    fee = get_object_or_404(
        FeeCollection,
        pk=pk,
        is_deleted=True
    )

    fee.is_deleted = False
    fee.deleted_at = None
    fee.deleted_by = None
    fee.save()

    messages.success(
        request,
        f'Fee Receipt {fee.receipt_no} restored successfully.'
    )

    return redirect('fee_recycle_bin')