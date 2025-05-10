from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg
from ..models import Machine, ChiffreAffaire
from ..forms import MachineForm

@login_required
def machine_list(request):
    machines = Machine.objects.all().order_by('numero_terminal')
    return render(request, 'gestloto/machines/list.html', {'machines': machines})

@login_required
def machine_detail(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    chiffres_affaires = ChiffreAffaire.objects.filter(machine=machine).order_by('-date_chiffre_affaire')[:15]
    
    # Statistiques de la machine
    stats = ChiffreAffaire.objects.filter(machine=machine).aggregate(
        total_ventes=Sum('ventes_totales'),
        total_solde=Sum('solde_total'),
        total_commission=Sum('montant_commission'),
        moyenne_solde=Avg('solde_total')
    )
    
    context = {
        'machine': machine,
        'chiffres_affaires': chiffres_affaires,
        'stats': stats,
    }
    return render(request, 'gestloto/machines/detail.html', context)

@login_required
def machine_create(request):
    if request.method == 'POST':
        form = MachineForm(request.POST)
        if form.is_valid():
            machine = form.save()
            messages.success(request, f"La machine {machine.numero_terminal} a été créée avec succès.")
            return redirect('machine_list')
    else:
        form = MachineForm()
    
    return render(request, 'gestloto/machines/form.html', {'form': form, 'title': 'Ajouter une machine'})

@login_required
def machine_update(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    if request.method == 'POST':
        form = MachineForm(request.POST, instance=machine)
        if form.is_valid():
            form.save()
            messages.success(request, f"La machine {machine.numero_terminal} a été modifiée avec succès.")
            return redirect('machine_detail', pk=machine.pk)
    else:
        form = MachineForm(instance=machine)
    
    return render(request, 'gestloto/machines/form.html', {'form': form, 'machine': machine, 'title': 'Modifier une machine'})

@login_required
def machine_delete(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    if request.method == 'POST':
        numero = machine.numero_terminal
        machine.delete()
        messages.success(request, f"La machine {numero} a été supprimée.")
        return redirect('machine_list')
    
    return render(request, 'gestloto/machines/delete.html', {'machine': machine})