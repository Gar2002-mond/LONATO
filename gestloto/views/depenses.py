from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from ..models import Depense, TypeDepense, Agent
from ..forms import DepenseForm

@login_required
def depense_list(request):
    # Récupération des paramètres de recherche et filtrage
    search_query = request.GET.get('q', '').strip()
    type_filter = request.GET.get('type', '')
    agent_filter = request.GET.get('agent', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    sort_by = request.GET.get('sort', '-date_depense')
    page_number = request.GET.get('page', 1)
    
    # Base queryset avec préchargement des relations
    depenses_queryset = Depense.objects.select_related('type_depense', 'agent').all()
    
    # Application de la recherche
    if search_query:
        depenses_queryset = depenses_queryset.filter(
            Q(reference__icontains=search_query) |
            Q(type_depense__libelle__icontains=search_query) |
            Q(agent__nom_agent__icontains=search_query) |
            Q(agent__prenom_agent__icontains=search_query) |
            Q(autres_details__icontains=search_query)
        )
    
    # Application des filtres
    if type_filter:
        depenses_queryset = depenses_queryset.filter(type_depense_id=type_filter)
    
    if agent_filter:
        depenses_queryset = depenses_queryset.filter(agent_id=agent_filter)
    
    # Filtrage par dates
    if date_debut:
        try:
            depenses_queryset = depenses_queryset.filter(date_depense__gte=date_debut)
        except ValueError:
            pass
    
    if date_fin:
        try:
            depenses_queryset = depenses_queryset.filter(date_depense__lte=date_fin)
        except ValueError:
            pass
    
    # Application du tri
    valid_sort_fields = [
        'date_depense', '-date_depense', 'montant', '-montant',
        'type_depense__libelle', '-type_depense__libelle',
        'reference', '-reference'
    ]
    
    if sort_by in valid_sort_fields:
        depenses_queryset = depenses_queryset.order_by(sort_by)
    else:
        depenses_queryset = depenses_queryset.order_by('-date_depense')
    
    # Calcul des statistiques
    stats = depenses_queryset.aggregate(
        total_depenses=Sum('montant') or 0,
        nb_depenses=Count('id')
    )
    
    # Statistiques par type
    stats_par_type = depenses_queryset.values(
        'type_depense__libelle'
    ).annotate(
        total=Sum('montant'),
        count=Count('id')
    ).order_by('-total')
    
    # Dépenses ce mois
    first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    depenses_ce_mois = Depense.objects.filter(
        date_depense__gte=first_day_of_month
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    # Pagination
    paginator = Paginator(depenses_queryset, 20)  # 20 dépenses par page
    depenses = paginator.get_page(page_number)
    
    # Données pour les filtres
    types_depenses = TypeDepense.objects.all()
    agents = Agent.objects.all().order_by('nom_agent', 'prenom_agent')
    
    context = {
        'depenses': depenses,
        'types_depenses': types_depenses,
        'agents': agents,
        'stats': stats,
        'stats_par_type': stats_par_type,
        'depenses_ce_mois': depenses_ce_mois,
        'search_query': search_query,
        'type_filter': type_filter,
        'agent_filter': agent_filter,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'sort_by': sort_by,
    }
    
    # Si c'est une requête HTMX, ne retourner que le contenu de la liste
    if request.headers.get('HX-Request'):
        return render(request, 'gestloto/depenses/list_partial.html', context)
    
    return render(request, 'gestloto/depenses/list.html', context)

@login_required
def depense_create(request):
    if request.method == 'POST':
        form = DepenseForm(request.POST)
        if form.is_valid():
            depense = form.save()
            messages.success(request, f"La dépense {depense.reference} a été créée avec succès.")
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
            messages.success(request, f"La dépense {depense.reference} a été modifiée avec succès.")
            return redirect('depense_list')
    else:
        form = DepenseForm(instance=depense)
    
    return render(request, 'gestloto/depenses/form.html', {'form': form, 'depense': depense, 'title': 'Modifier une dépense'})

@login_required
def depense_delete(request, pk):
    depense = get_object_or_404(Depense, pk=pk)
    
    if request.method == 'POST':
        reference = depense.reference
        depense.delete()
        
        # Si c'est une requête AJAX, retourner une réponse JSON
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('HX-Request'):
            return JsonResponse({'success': True, 'message': f"La dépense {reference} a été supprimée."})
        
        messages.success(request, f"La dépense {reference} a été supprimée.")
        return redirect('depense_list')
    
    return render(request, 'gestloto/depenses/delete.html', {'depense': depense})