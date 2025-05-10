from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Agent
from ..forms import AgentForm

@login_required
def agent_list(request):
    agents = Agent.objects.all().order_by('nom_agent')
    return render(request, 'gestloto/agents/list.html', {'agents': agents})

@login_required
def agent_detail(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    machines = agent.machines.all()
    chiffres_affaires = agent.chiffres_enregistres.all().order_by('-date_chiffre_affaire')[:10]
    penalites_commissions = agent.penalites_commissions.all().order_by('-date_penalite', '-date_commission')[:10]
    
    context = {
        'agent': agent,
        'machines': machines,
        'chiffres_affaires': chiffres_affaires,
        'penalites_commissions': penalites_commissions,
    }
    return render(request, 'gestloto/agents/detail.html', context)

@login_required
def agent_create(request):
    if request.method == 'POST':
        form = AgentForm(request.POST)
        if form.is_valid():
            agent = form.save()
            messages.success(request, f"L'agent {agent.nom_agent} {agent.prenom_agent} a été créé avec succès.")
            return redirect('agent_list')
    else:
        form = AgentForm()
    
    return render(request, 'gestloto/agents/form.html', {'form': form, 'title': 'Ajouter un agent'})

@login_required
def agent_update(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    if request.method == 'POST':
        form = AgentForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'agent {agent.nom_agent} {agent.prenom_agent} a été modifié avec succès.")
            return redirect('agent_detail', pk=agent.pk)
    else:
        form = AgentForm(instance=agent)
    
    return render(request, 'gestloto/agents/form.html', {'form': form, 'agent': agent, 'title': 'Modifier un agent'})

@login_required
def agent_delete(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    if request.method == 'POST':
        nom_complet = f"{agent.nom_agent} {agent.prenom_agent}"
        agent.delete()
        messages.success(request, f"L'agent {nom_complet} a été supprimé.")
        return redirect('agent_list')
    
    return render(request, 'gestloto/agents/delete.html', {'agent': agent})