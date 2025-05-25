from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models.functions import Coalesce
from ..models import Collecteur, ActiviteCollecteur
from ..forms import CollecteurForm

@login_required
def collecteur_list(request):
    # Récupération des paramètres de recherche et filtrage
    search_query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'nom_collecteur')
    page_number = request.GET.get('page', 1)
    
    # Base queryset avec préchargement des relations
    collecteurs_queryset = Collecteur.objects.select_related().prefetch_related('activites').all()
    
    # Application de la recherche
    if search_query:
        collecteurs_queryset = collecteurs_queryset.filter(
            Q(nom_collecteur__icontains=search_query) |
            Q(prenom_collecteur__icontains=search_query) |
            Q(reference_collecteur__icontains=search_query) |
            Q(num_tel_collecteur__icontains=search_query) |
            Q(email_collecteur__icontains=search_query) |
            Q(autres_details__icontains=search_query)
        )
    
    # Application du tri
    valid_sort_fields = [
        'nom_collecteur', '-nom_collecteur', 'prenom_collecteur', '-prenom_collecteur',
        'reference_collecteur', '-reference_collecteur',
        'date_debut_activites', '-date_debut_activites',
        'pourcentage_commission', '-pourcentage_commission'
    ]
    
    # Mappage des options de tri simples vers les vrais noms de champs
    sort_mapping = {
        'nom': 'nom_collecteur',
        'reference': 'reference_collecteur',
        'date': '-date_debut_activites',
        'commission': '-pourcentage_commission'
    }
    
    if sort_by in sort_mapping:
        sort_by = sort_mapping[sort_by]
    
    if sort_by in valid_sort_fields:
        collecteurs_queryset = collecteurs_queryset.order_by(sort_by)
    else:
        collecteurs_queryset = collecteurs_queryset.order_by('nom_collecteur')
    
    # Calcul des statistiques
    total_collecteurs = Collecteur.objects.count()
    
    # Nouveaux collecteurs ce mois
    first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    nouveaux_collecteurs_count = Collecteur.objects.filter(
        date_debut_activites__gte=first_day_of_month
    ).count()
    
    # Commission moyenne
    commission_moyenne = Collecteur.objects.aggregate(
        avg_commission=Avg('pourcentage_commission')
    )['avg_commission'] or 0
    
    # Pagination
    paginator = Paginator(collecteurs_queryset, 20)  # 20 collecteurs par page
    collecteurs = paginator.get_page(page_number)
    
    context = {
        'collecteurs': collecteurs,
        'search_query': search_query,
        'sort_by': request.GET.get('sort', 'nom'),  # Garder la valeur originale pour le template
        'nouveaux_collecteurs': nouveaux_collecteurs_count,
        'commission_moyenne': commission_moyenne,
        'total_collecteurs': total_collecteurs,
    }
    
    # Si c'est une requête HTMX, ne retourner que le contenu de la liste
    if request.headers.get('HX-Request'):
        return render(request, 'gestloto/collecteurs/list_partial.html', context)
    
    return render(request, 'gestloto/collecteurs/list.html', context)

@login_required
def collecteur_detail(request, pk):
    collecteur = get_object_or_404(Collecteur, pk=pk)
    activites = collecteur.activites.all().order_by('-date_activite')[:15] 
    
    commission_rate_percentage = collecteur.pourcentage_commission
    if commission_rate_percentage is None:
        commission_rate_percentage = Decimal('0')
    else:
        commission_rate_percentage = Decimal(str(commission_rate_percentage)) 

    # Statistiques des activités
    aggregated_data = collecteur.activites.aggregate(
        total_montant_sum=Coalesce(Sum('montant_activite'), Decimal('0.00'))
    )
    
    total_montant = aggregated_data['total_montant_sum']
    total_commission = (total_montant * commission_rate_percentage) / Decimal('100')
            
    stats = {
        'total_montant': total_montant,
        'total_commission': total_commission,
    }
    
    context = {
        'collecteur': collecteur,
        'activites': activites,
        'stats': stats,
    }
    return render(request, 'gestloto/collecteurs/detail.html', context)

@login_required
def collecteur_create(request):
    if request.method == 'POST':
        form = CollecteurForm(request.POST)
        if form.is_valid():
            collecteur = form.save()
            messages.success(request, f"Le collecteur {collecteur.nom_collecteur} {collecteur.prenom_collecteur} a été créé avec succès.")
            return redirect('collecteur_list')
    else:
        form = CollecteurForm()
    
    return render(request, 'gestloto/collecteurs/form.html', {'form': form, 'title': 'Ajouter un collecteur'})

@login_required
def collecteur_update(request, pk):
    collecteur = get_object_or_404(Collecteur, pk=pk)
    if request.method == 'POST':
        form = CollecteurForm(request.POST, instance=collecteur)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le collecteur {collecteur.nom_collecteur} {collecteur.prenom_collecteur} a été modifié avec succès.")
            return redirect('collecteur_detail', pk=collecteur.pk)
    else:
        form = CollecteurForm(instance=collecteur)
    
    return render(request, 'gestloto/collecteurs/form.html', {'form': form, 'collecteur': collecteur, 'title': 'Modifier un collecteur'})

@login_required
def collecteur_delete(request, pk):
    collecteur = get_object_or_404(Collecteur, pk=pk)
    
    if request.method == 'POST':
        nom_complet = f"{collecteur.nom_collecteur} {collecteur.prenom_collecteur}"
        collecteur.delete()
        
        # Si c'est une requête AJAX, retourner une réponse JSON
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('HX-Request'):
            return JsonResponse({'success': True, 'message': f"Le collecteur {nom_complet} a été supprimé."})
        
        messages.success(request, f"Le collecteur {nom_complet} a été supprimé.")
        return redirect('collecteur_list')
    
    return render(request, 'gestloto/collecteurs/delete.html', {'collecteur': collecteur})

def get_collecteur_commission_view(request):
    collecteur_id = request.GET.get('collecteur')

    if not collecteur_id:
        html_response = '<input type="number" name="pourcentage_commission" value="" class="input input-bordered" readonly placeholder="Sélectionnez un collecteur d\'abord">'
        return HttpResponse(html_response)

    try:
        collecteur = Collecteur.objects.get(id=collecteur_id)
        commission = collecteur.pourcentage_commission
        if commission is None:
            commission = ""

        html_response = f'<input type="number" name="pourcentage_commission" value="{commission}" class="input input-bordered" readonly>'
        return HttpResponse(html_response)
    except Collecteur.DoesNotExist:
        html_response = '<input type="number" name="pourcentage_commission" value="" class="input input-bordered" readonly placeholder="Collecteur non trouvé">'
        return HttpResponse(html_response)
    except ValueError:
        html_response = '<input type="number" name="pourcentage_commission" value="" class="input input-bordered" readonly placeholder="ID de collecteur invalide">'
        return HttpResponse(html_response)
