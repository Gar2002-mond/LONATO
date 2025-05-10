from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import PenaliteCommission, Agent, Machine
from ..forms import PenaliteCommissionForm

@login_required
def penalite_commission_list(request):
    agent_filter = request.GET.get('agent', None)
    machine_filter = request.GET.get('machine', None)
    
    penalites_commissions = PenaliteCommission.objects.all()
    
    if agent_filter:
        penalites_commissions = penalites_commissions.filter(agent__id=agent_filter)
    
    if machine_filter:
        penalites_commissions = penalites_commissions.filter(machine__id=machine_filter)
    
    penalites_commissions = penalites_commissions.select_related('agent', 'machine').order_by('-date_penalite', '-date_commission')
    
    context = {
        'penalites_commissions': penalites_commissions,
        'agents': Agent.objects.all(),
        'machines': Machine.objects.all(),
        'agent_filter': agent_filter,
        'machine_filter': machine_filter,
    }
    
    return render(request, 'gestloto/penalites_commissions/list.html', context)

@login_required
def penalite_commission_create(request):
    if request.method == 'POST':
        form = PenaliteCommissionForm(request.POST)
        if form.is_valid():
            penalite_commission = form.save()
            messages.success(request, f"L'enregistrement pour l'agent {penalite_commission.agent} a été créé avec succès.")
            return redirect('penalite_commission_list')
    else:
        form = PenaliteCommissionForm()
    
    return render(request, 'gestloto/penalites_commissions/form.html', {'form': form, 'title': 'Ajouter une pénalité/commission'})

@login_required
def penalite_commission_update(request, pk):
    penalite_commission = get_object_or_404(PenaliteCommission, pk=pk)
    if request.method == 'POST':
        form = PenaliteCommissionForm(request.POST, instance=penalite_commission)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'enregistrement pour l'agent {penalite_commission.agent} a été modifié avec succès.")
            return redirect('penalite_commission_list')
    else:
        form = PenaliteCommissionForm(instance=penalite_commission)
    
    return render(request, 'gestloto/penalites_commissions/form.html', {
        'form': form, 
        'penalite_commission': penalite_commission, 
        'title': 'Modifier une pénalité/commission'
    })

@login_required
def penalite_commission_delete(request, pk):
    penalite_commission = get_object_or_404(PenaliteCommission, pk=pk)
    if request.method == 'POST':
        agent_nom = penalite_commission.agent
        penalite_commission.delete()
        messages.success(request, f"L'enregistrement pour l'agent {agent_nom} a été supprimé.")
        return redirect('penalite_commission_list')
    
    return render(request, 'gestloto/penalites_commissions/delete.html', {'penalite_commission': penalite_commission})