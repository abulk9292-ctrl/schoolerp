from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
from django.apps import apps

from .models import Expense
from .forms import ExpenseForm


@login_required
def expense_list(request):
    expenses = Expense.objects.filter(is_deleted=False).order_by('-date')

    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # 🔥 Income from Fees
    FeeModel = apps.get_model('fees', 'FeeCollection')
    total_income = FeeModel.objects.aggregate(
        total=Sum('deposit_amount')
    )['total'] or Decimal('0')

    profit_loss = total_income - total_expense

    if profit_loss > 0:
        status = "PROFIT"
    elif profit_loss < 0:
        status = "LOSS"
    else:
        status = "BALANCED"

    return render(request, 'expenses/expense_list.html', {
        'expenses': expenses,
        'total_expense': total_expense,
        'total_income': total_income,
        'profit_loss': profit_loss,
        'status': status,
    })


# ✅ ADD
@login_required
def expense_add(request):
    form = ExpenseForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('expense_list')

    return render(request, 'expenses/expense_form.html', {'form': form})


# ✅ EDIT / UPDATE
@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    form = ExpenseForm(request.POST or None, instance=expense)

    if form.is_valid():
        form.save()
        return redirect('expense_list')

    return render(request, 'expenses/expense_form.html', {'form': form})


# ✅ DELETE
from django.utils import timezone

@login_required
def expense_delete(request, pk):

    expense = get_object_or_404(
        Expense,
        pk=pk
    )

    expense.is_deleted = True
    expense.deleted_at = timezone.now()
    expense.deleted_by = request.user
    expense.save()

    return redirect('expense_list')

@login_required
def expense_recycle_bin(request):

    expenses = Expense.objects.filter(
        is_deleted=True
    ).order_by(
        '-deleted_at'
    )

    return render(
        request,
        'expenses/expense_recycle_bin.html',
        {
            'expenses': expenses
        }
    )


@login_required
def expense_restore(request, pk):

    expense = get_object_or_404(
        Expense,
        pk=pk,
        is_deleted=True
    )

    expense.is_deleted = False
    expense.deleted_at = None
    expense.deleted_by = None
    expense.save()

    return redirect(
        'expense_recycle_bin'
    )


@login_required
def expense_permanent_delete(request, pk):

    if not request.user.is_superuser:
        return redirect(
            'expense_recycle_bin'
        )

    expense = get_object_or_404(
        Expense,
        pk=pk,
        is_deleted=True
    )

    expense.delete()

    return redirect(
        'expense_recycle_bin'
    )