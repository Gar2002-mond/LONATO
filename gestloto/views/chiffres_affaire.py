from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import ChiffreAffaire, Machine
from ..forms import ChiffreAffaireForm
from django.utils import timezone

@login_required
def chiffre_affaire_list(request):
    date_filter = request.GET.get('date', None)
    machine_filter = request.GET.get('machine', None)
    
    chiffres_affaire = ChiffreAffaire.objects.all()
    
    if date_filter:
        try:
            date_parts = date_filter.split('-')
            year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
            filter_date = timezone.datetime(year, month, day).date()
            chiffres_affaire = chiffres_affaire.filter(date_chiffre_affaire=filter_date)
        except (ValueError, IndexError):
            messages.error(request, "Format de date invalide.")
    
    if machine_filter:
        chiffres_affaire = chiffres_affaire.filter(machine__numero_terminal__icontains=machine_filter)
    
    chiffres_affaire = chiffres_affaire.select_related('machine', 'agent_enregistreur').order_by('-date_chiffre_affaire')
    
    context = {
        'chiffres_affaire': chiffres_affaire,
        'machines': Machine.objects.all(),
        'date_filter': date_filter,
        'machine_filter': machine_filter,
    }
    
    return render(request, 'gestloto/chiffres_affaire/list.html', context)

@login_required
def chiffre_affaire_detail(request, pk):
    chiffre_affaire = get_object_or_404(ChiffreAffaire, pk=pk)
    return render(request, 'gestloto/chiffres_affaire/detail.html', {'chiffre_affaire': chiffre_affaire})

@login_required
def chiffre_affaire_create(request):
    if request.method == 'POST':
        form = ChiffreAffaireForm(request.POST)
        if form.is_valid():
            chiffre_affaire = form.save(commit=False)
            # Le montant_commission est calculé automatiquement lors du save()
            chiffre_affaire.save()
            
            messages.success(request, f"Le chiffre d'affaires pour la machine {chiffre_affaire.machine.numero_terminal} a été créé avec succès.")
            return redirect('chiffre_affaire_list')
    else:
        form = ChiffreAffaireForm()
    
    return render(request, 'gestloto/chiffres_affaire/form.html', {'form': form, 'title': "Ajouter un chiffre d'affaires"})

@login_required
def chiffre_affaire_update(request, pk):
    chiffre_affaire = get_object_or_404(ChiffreAffaire, pk=pk)
    if request.method == 'POST':
        form = ChiffreAffaireForm(request.POST, instance=chiffre_affaire)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le chiffre d'affaires pour la machine {chiffre_affaire.machine.numero_terminal} a été modifié avec succès.")
            return redirect('chiffre_affaire_detail', pk=chiffre_affaire.pk)
    else:
        form = ChiffreAffaireForm(instance=chiffre_affaire)
    
    return render(request, 'gestloto/chiffres_affaire/form.html', {
        'form': form, 
        'chiffre_affaire': chiffre_affaire, 
        'title': "Modifier un chiffre d'affaires"
    })

@login_required
def chiffre_affaire_delete(request, pk):
    chiffre_affaire = get_object_or_404(ChiffreAffaire, pk=pk)
    if request.method == 'POST':
        machine_numero = chiffre_affaire.machine.numero_terminal
        date = chiffre_affaire.date_chiffre_affaire
        chiffre_affaire.delete()
        messages.success(request, f"Le chiffre d'affaires du {date} pour la machine {machine_numero} a été supprimé.")
        return redirect('chiffre_affaire_list')
    
    return render(request, 'gestloto/chiffres_affaire/delete.html', {'chiffre_affaire': chiffre_affaire})