from django.shortcuts import render


def index(request):
    return render(request, 'index.html')

def attest_overview(request):
    may_attest = request.user.profile.may_attest()
    expenses = models.Expense.objects.exclude(owner__user=request.user).filter(
        expensepart__attested_by=None,
        expensepart__committee_name__iregex=r'(' + '|'.join(may_attest) + ')'
    ).distinct()
    return render(request, 'expenses/action_attest.html', {
        'attestable_expenses': json.dumps([expense.to_dict() for expense in expenses], default=json_serial)
    })

def attest_expense_part(request, pk):
    try:
        expense_part = models.ExpensePart.objects.get(pk=int(pk))
        if request.method == 'POST':
            if request.user.username == expense_part.expense.owner.user.username:
                messages.error(request, 'Du kan inte attestera dina egna kvitton')
                return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense_part.expense.id}))

            expense_part.attested_by = request.user.profile
            expense_part.attest_date = date.today()

            expense_part.save()
            comment = models.Comment(
                author=request.user.profile,
                expense=expense_part.expense,
                content="Attesterade kvittodelen: " + str(expense_part)
            )
            comment.save()
            return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense_part.expense.id}))
        else:
            raise Http404()

    except ObjectDoesNotExist:
        raise Http404("Kvittodelen finns inte")

def confirm_overview(request):
    if not dauth.has_permission('confirm', request):
        return HttpResponseForbidden("Du har inte rättigheterna för att se den här sidan")
    expenses = models.Expense.objects.filter(
        confirmed_by=None
    ).order_by('id').distinct()

    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return fakefloat(obj)
        raise TypeError ("Type %s not serializable" % type(obj))

    return render(request, 'expenses/action_confirm.html', {
        'confirmable_expenses': json.dumps([expense.to_dict() for expense in expenses], default=json_serial)
    })

def pay_overview(request):
    if not dauth.has_permission('pay', request):
        return HttpResponseForbidden("Du har inte rättigheterna för att se den här sidan")

    expenses = models.Expense.objects.filter(reimbursement=None).exclude(expensepart__attested_by=None).exclude(confirmed_by=None).order_by('owner__user__username')
    context = {
        'payable_expenses': json.dumps([expense.to_dict() for expense in expenses], default=json_serial),
        'accounts': json.dumps([s.name for s in models.BankAccount.objects.all().order_by('name')])
    }

    if request.GET:
        context['payment'] = models.Payment.objects.get(id=int(request.GET['payment']))

    return render(request, 'expenses/action_pay.html', context)

def account_overview(request):
    may_account = request.user.profile.may_account()
    if '*' in may_account:
        expenses = models.Expense.objects.exclude(reimbursement=None).filter(
            verification=''
        ).distinct()
    else:
        expenses = models.Expense.objects.exclude(reimbursement=None).filter(
            verification='',
            expensepart__committee_name__iregex=r'(' + '|'.join(may_account) + ')'
        ).distinct()

    return render(request, 'expenses/action_account.html', {
        'account_ready_expenses': json.dumps([expense.to_dict() for expense in expenses], default=json_serial)
    })

def edit_expense_verification(request, pk):
    try:
        expense = models.Expense.objects.get(pk=pk)
        if not may_account(request, expense):
            return HttpResponseForbidden("Du har inte rättigheter att bokföra det här")
        if expense.reimbursement is None:
            return HttpResponseBadRequest("Du kan inte bokföra det här utlägget än")

        if request.method == 'POST':
            expense.verification = request.POST['verification']
            expense.save()

            comment = models.Comment(
                author=request.user.profile,
                expense=expense,
                content="Ändrade verifikationsnumret till: " + expense.verification
            )
            comment.save()

            return HttpResponseRedirect(reverse('expenses-expense', kwargs={'pk': expense.id}))
        else:
            return render(request, 'expenses/edit_expense_verification.html', {
                "expense": expense,
                "expense_parts": expense.expensepart_set.all()
            })
    except ObjectDoesNotExist:
        raise Http404("Utlägget finns inte")

def confirm_expense(request, pk):
    if request.method == 'POST':
        try:
            expense = models.Expense.objects.get(pk=pk)

            if not dauth.has_permission('confirm', request):
                return HttpResponseForbidden("Du har inte rättigheterna för att se den här sidan")

            expense.confirmed_by = request.user
            expense.confirmed_at = date.today()
            expense.save()

            comment = models.Comment(
                expense=expense,
                author=request.user.profile,
                content='Jag bekräftar att kvittot finns i pärmen.'
            )
            comment.save()

            return HttpResponseRedirect(reverse('expenses-action-confirm'))
        except ObjectDoesNotExist:
            raise Http404("Utlägget finns inte")
    else:
        raise Http404()

def set_verification(request, expense_pk):
    if request.method == 'POST':
        try:
            expense = models.Expense.objects.get(pk=expense_pk)
            if not may_account(request, expense):
                return HttpResponseForbidden("Du har inte rättigheter att bokföra det här")
            if expense.reimbursement is None:
                return HttpResponseBadRequest("Du kan inte bokföra det här utlägget än")

            expense.verification = request.POST['verification']
            expense.save()

            comment = models.Comment(
                author=request.user.profile,
                expense=expense,
                content="Bokförde med verifikationsnumret: " + expense.verification
            )
            comment.save()

            return HttpResponseRedirect(reverse('expenses-action-account'))
        except ObjectDoesNotExist:
            raise Http404("Utlägget finns inte")
    else:
        raise Http404()