from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from ..models import Depense, TypeDepense
from ..forms import DepenseForm

@login_required
def depense_list(request):
    type_filter = request.GET.get('type', None)
    
    depenses = Depense.objects.all()
    
    if type_filter:
        depenses = depenses.filter(type_depense__id=type_filter)
    
    depenses = depenses.select_related('type_depense', 'agent').order_by('-date_depense')
    
    types_depenses = TypeDepense.objects.all()
    total_depenses = depenses.aggregate(total=Sum('montant'))['total'] or 0
    
    context = {
        'depenses': depenses,
        'types_depenses': types_depenses,
        'type_filter': type_filter,
        'total_depenses': total_depenses,
    }
    
    return render(request, 'gestloto/depenses/list.html', context)

@login_required
def depense_create(request):
    if request.method == 'POST':
        form = DepenseForm(request.POST)
        if form.is_valid():
            depense = form.save()
            messages.success(request, f"La dépense de {depense.montant} FCFA a été créée avec succès.")
            return redirect('depense_list')
    else:
        form = DepenseForm()
    
    return render(request, 'gestloto/depenses/form.html', {'form': form, 'title': 'Ajouter une dépense'})

@login_required
def depense_update(request, pk):
    depense = get_object_or_404(Depense, pk=pk)
    if request.method == 'POST':
        form = DepenseForm(request.POST, instance=depense)
        if form.is_valid():
            form.save()
            messages.success(request, f"La dépense a été modifiée avec succès.")
            return redirect('depense_list')
    else:
        form = DepenseForm(instance=depense)
    
    return render(request, 'gestloto/depenses/form.html', {
        'form': form, 
        'depense': depense, 
        'title': 'Modifier une dépense'
    })

@login_required
def depense_delete(request, pk):
    depense = get_object_or_404(Depense, pk=pk)
    if request.method == 'POST':
        montant = depense.montant
        type_depense = depense.type_depense.get_libelle_display()
        depense.delete()
        messages.success(request, f"La dépense de {montant} FCFA de type '{type_depense}' a été supprimée.")
        return redirect('depense_list')
    
    return render(request, 'gestloto/depenses/delete.html', {'depense': depense})