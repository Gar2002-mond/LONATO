from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json
from ..models import Agent
from ..forms import AgentForm

@login_required
def agent_list(request):
    # Récupération des paramètres de recherche et filtrage
    search_query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'nom_agent')
    commission_filter = request.GET.get('commission', '')
    page_number = request.GET.get('page', 1)
    
    # Base queryset avec préchargement des relations
    agents_queryset = Agent.objects.select_related().prefetch_related('machines').all()
    
    # Application de la recherche avec les champs corrects du modèle
    if search_query:
        agents_queryset = agents_queryset.filter(
            Q(nom_agent__icontains=search_query) |
            Q(prenom_agent__icontains=search_query) |
            Q(reference_agent__icontains=search_query) |
            Q(num_tel_agent__icontains=search_query) |
            Q(email_agent__icontains=search_query) |
            Q(autres_details__icontains=search_query)  # Utiliser 'autres_details' au lieu d'adresse_agent
        )
    
    # Application du filtre par commission
    if commission_filter == 'high':
        agents_queryset = agents_queryset.filter(pourcentage_commission__gte=10)
    elif commission_filter == 'medium':
        agents_queryset = agents_queryset.filter(
            pourcentage_commission__gte=5,
            pourcentage_commission__lt=10
        )
    elif commission_filter == 'low':
        agents_queryset = agents_queryset.filter(pourcentage_commission__lt=5)
    
    # Application du tri avec correction des noms de champs
    valid_sort_fields = [
        'nom_agent', '-nom_agent', 'prenom_agent', '-prenom_agent', 
        'reference_agent', '-reference_agent',
        'date_debut_activites', '-date_debut_activites',
        'pourcentage_commission', '-pourcentage_commission'
    ]
    
    if sort_by in valid_sort_fields:
        agents_queryset = agents_queryset.order_by(sort_by)
    else:
        agents_queryset = agents_queryset.order_by('nom_agent')
    
    # Calcul des statistiques
    total_agents = Agent.objects.count()
    
    # Nouveaux agents ce mois
    first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    nouveaux_agents_count = Agent.objects.filter(
        date_debut_activites__gte=first_day_of_month
    ).count()
    
    # Commission moyenne
    commission_moyenne = Agent.objects.aggregate(
        avg_commission=Avg('pourcentage_commission')
    )['avg_commission'] or 0
    
    # Total machines gérées
    total_machines_count = Agent.objects.aggregate(
        total_machines=Count('machines')
    )['total_machines'] or 0
    
    # Pagination
    paginator = Paginator(agents_queryset, 20)  # 20 agents par page
    agents = paginator.get_page(page_number)
    
    context = {
        'agents': agents,
        'search_query': search_query,
        'sort_by': sort_by,
        'commission_filter': commission_filter,
        'nouveaux_agents_count': nouveaux_agents_count,
        'commission_moyenne': commission_moyenne,
        'total_machines_count': total_machines_count,
        'total_agents': total_agents,
    }
    
    # Si c'est une requête HTMX, ne retourner que le contenu de la liste
    if request.headers.get('HX-Request'):
        return render(request, 'gestloto/agents/list_partial.html', context)
    
    return render(request, 'gestloto/agents/list.html', context)

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
        
        # Si c'est une requête AJAX, retourner une réponse JSON
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('HX-Request'):
            return JsonResponse({'success': True, 'message': f"L'agent {nom_complet} a été supprimé."})
        
        messages.success(request, f"L'agent {nom_complet} a été supprimé.")
        return redirect('agent_list')
    
    return render(request, 'gestloto/agents/delete.html', {'agent': agent})