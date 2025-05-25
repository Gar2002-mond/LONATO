from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
from datetime import timedelta
from ..models import ActiviteCollecteur, Collecteur
from ..forms import ActiviteCollecteurForm

@login_required
def activite_collecteur_list(request):
    # Récupération des paramètres de recherche et filtrage
    search_query = request.GET.get('q', '').strip()
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    collecteur_filter = request.GET.get('collecteur', '')
    sort_by = request.GET.get('sort', '-date_activite')
    page_number = request.GET.get('page', 1)
    
    # Base queryset avec préchargement des relations
    activites_queryset = ActiviteCollecteur.objects.select_related('collecteur').all()
    
    # Application de la recherche
    if search_query:
        activites_queryset = activites_queryset.filter(
            Q(collecteur__nom_collecteur__icontains=search_query) |
            Q(collecteur__prenom_collecteur__icontains=search_query) |
            Q(collecteur__reference_collecteur__icontains=search_query) |
            Q(reference_recu__icontains=search_query) |
            Q(observations__icontains=search_query)
        )
    
    # Application des filtres
    if collecteur_filter:
        activites_queryset = activites_queryset.filter(collecteur_id=collecteur_filter)
    
    # Filtrage par dates
    if date_debut:
        try:
            activites_queryset = activites_queryset.filter(date_activite__gte=date_debut)
        except ValueError:
            pass
    
    if date_fin:
        try:
            activites_queryset = activites_queryset.filter(date_activite__lte=date_fin)
        except ValueError:
            pass
    
    # Application du tri
    valid_sort_fields = [
        'date_activite', '-date_activite', 
        'montant_activite', '-montant_activite',
        'pourcentage_commission', '-pourcentage_commission',
        'collecteur__nom_collecteur', '-collecteur__nom_collecteur',
        'reference_recu', '-reference_recu'
    ]
    
    if sort_by in valid_sort_fields:
        activites_queryset = activites_queryset.order_by(sort_by)
    else:
        activites_queryset = activites_queryset.order_by('-date_activite')
    
    # Calcul de la commission pour chaque activité
    commission_expression = ExpressionWrapper(
        F('montant_activite') * F('pourcentage_commission') / 100,
        output_field=DecimalField(max_digits=15, decimal_places=2)
    )
    
    activites_queryset = activites_queryset.annotate(
        commission_calculee=commission_expression
    )
    
    # Calcul des statistiques globales - FIX de l'erreur
    stats_aggregates = activites_queryset.aggregate(
        total_montant=Sum('montant_activite'),
        total_commission=Sum('commission_calculee'),
        nb_activites=Count('id'),
        commission_moyenne=Avg('commission_calculee')  # Utilisation d'Avg au lieu de la division manuelle
    )
    
    # Conversion des valeurs None en 0
    stats = {
        'total_montant': stats_aggregates['total_montant'] or Decimal('0'),
        'total_commission': stats_aggregates['total_commission'] or Decimal('0'),
        'nb_activites': stats_aggregates['nb_activites'] or 0,
        'commission_moyenne': stats_aggregates['commission_moyenne'] or Decimal('0')
    }
    
    # Statistiques par collecteur
    stats_par_collecteur = activites_queryset.values(
        'collecteur__id',
        'collecteur__nom_collecteur', 
        'collecteur__prenom_collecteur',
        'collecteur__reference_collecteur'
    ).annotate(
        total_montant=Sum('montant_activite'),
        total_commission=Sum('commission_calculee'),
        count=Count('id')
    ).order_by('-total_montant')[:5]
    
    # Activités ce mois
    first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    activites_ce_mois_aggregates = ActiviteCollecteur.objects.filter(
        date_activite__gte=first_day_of_month
    ).annotate(
        commission_calc=commission_expression
    ).aggregate(
        total=Sum('montant_activite'),
        commission=Sum('commission_calc')
    )
    
    activites_ce_mois = {
        'total': activites_ce_mois_aggregates['total'] or Decimal('0'),
        'commission': activites_ce_mois_aggregates['commission'] or Decimal('0')
    }
    
    # Pagination
    paginator = Paginator(activites_queryset, 20)  # 20 activités par page
    activites = paginator.get_page(page_number)
    
    # Données pour les filtres
    collecteurs = Collecteur.objects.all().order_by('nom_collecteur', 'prenom_collecteur')
    
    context = {
        'activites': activites,
        'collecteurs': collecteurs,
        'stats': stats,
        'stats_par_collecteur': stats_par_collecteur,
        'activites_ce_mois': activites_ce_mois,
        'search_query': search_query,
        'collecteur_filter': collecteur_filter,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'sort_by': sort_by,
    }
    
    # Si c'est une requête HTMX, ne retourner que le contenu de la liste
    if request.headers.get('HX-Request'):
        return render(request, 'gestloto/activites_collecteur/list_partial.html', context)
    
    return render(request, 'gestloto/activites_collecteur/list.html', context)

@login_required
def activite_collecteur_create(request):
    if request.method == 'POST':
        form = ActiviteCollecteurForm(request.POST)
        if form.is_valid():
            activite = form.save()
            messages.success(request, f"L'activité du collecteur {activite.collecteur} a été créée avec succès.")
            
            # Standardisation sur HTMX uniquement
            if request.headers.get('HX-Request'):
                return redirect('activite_collecteur_list')
            
            return redirect('activite_collecteur_list')
        else:
            # Si le formulaire n'est pas valide et c'est HTMX
            if request.headers.get('HX-Request'):
                return render(request, 'gestloto/activites_collecteur/form_partial.html', {'form': form})
    else:
        form = ActiviteCollecteurForm()
    
    return render(request, 'gestloto/activites_collecteur/form.html', {
        'form': form, 
        'title': 'Ajouter une activité de collecteur',
        'submit_text': 'Créer l\'activité'
    })

@login_required
def activite_collecteur_update(request, pk):
    activite = get_object_or_404(ActiviteCollecteur, pk=pk)
    if request.method == 'POST':
        form = ActiviteCollecteurForm(request.POST, instance=activite)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'activité du collecteur {activite.collecteur} a été modifiée avec succès.")
            
            # Standardisation sur HTMX uniquement
            if request.headers.get('HX-Request'):
                return redirect('activite_collecteur_list')
            
            return redirect('activite_collecteur_list')
        else:
            # Si le formulaire n'est pas valide et c'est HTMX
            if request.headers.get('HX-Request'):
                return render(request, 'gestloto/activites_collecteur/form_partial.html', {'form': form})
    else:
        form = ActiviteCollecteurForm(instance=activite)
    
    return render(request, 'gestloto/activites_collecteur/form.html', {
        'form': form, 
        'activite': activite, 
        'title': 'Modifier une activité de collecteur',
        'submit_text': 'Sauvegarder les modifications'
    })

@login_required
def activite_collecteur_delete(request, pk):
    activite = get_object_or_404(ActiviteCollecteur, pk=pk)
    if request.method == 'POST':
        collecteur_nom = str(activite.collecteur)
        date_activite = activite.date_activite
        activite.delete()
        
        # Standardisation sur HTMX uniquement
        if request.headers.get('HX-Request'):
            messages.success(request, f"L'activité du {date_activite} pour le collecteur {collecteur_nom} a été supprimée.")
            return redirect('activite_collecteur_list')
        
        messages.success(request, f"L'activité du {date_activite} pour le collecteur {collecteur_nom} a été supprimée.")
        return redirect('activite_collecteur_list')
    
    return render(request, 'gestloto/activites_collecteur/delete.html', {'activite': activite})

def get_collecteur_commission_view(request):
    """Vue pour récupérer la commission d'un collecteur"""
    if request.method == 'POST':
        collecteur_id = request.POST.get('collecteur')
        
        if not collecteur_id:
            html_response = '''
            <input type="number" 
                   name="pourcentage_commission" 
                   value="" 
                   min="0" max="100" step="0.01"
                   class="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-100 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200" 
                   readonly 
                   placeholder="Sélectionnez d'abord un collecteur">
            '''
            return HttpResponse(html_response)

        try:
            collecteur = Collecteur.objects.get(id=collecteur_id)
            commission = collecteur.pourcentage_commission
            if commission is None:
                commission = ""

            html_response = f'''
            <input type="number" 
                   name="pourcentage_commission" 
                   value="{commission}" 
                   min="0" max="100" step="0.01"
                   class="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-100 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200" 
                   readonly
                   hx-post="{request.build_absolute_uri('/ajax/calculate-commission/')}"
                   hx-trigger="change"
                   hx-target="#commission-preview"
                   hx-include="[name='montant_activite'], [name='pourcentage_commission']">
            '''
            return HttpResponse(html_response)
        except Collecteur.DoesNotExist:
            html_response = '''
            <input type="number" 
                   name="pourcentage_commission" 
                   value="" 
                   min="0" max="100" step="0.01"
                   class="w-full px-4 py-3 border border-gray-300 rounded-lg bg-red-100 focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200" 
                   readonly 
                   placeholder="Collecteur non trouvé">
            '''
            return HttpResponse(html_response)
        except ValueError:
            html_response = '''
            <input type="number" 
                   name="pourcentage_commission" 
                   value="" 
                   min="0" max="100" step="0.01"
                   class="w-full px-4 py-3 border border-gray-300 rounded-lg bg-red-100 focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200" 
                   readonly 
                   placeholder="ID de collecteur invalide">
            '''
            return HttpResponse(html_response)

    return HttpResponse("Méthode de requête non valide.")

def calculate_commission_view(request):
    if request.method == 'POST':
        try:
            montant_activite_str = request.POST.get('montant_activite', '0')
            pourcentage_commission_str = request.POST.get('pourcentage_commission', '0')

            # Gérer les chaînes vides ou non valides en les traitant comme zéro
            montant_activite = Decimal(montant_activite_str) if montant_activite_str else Decimal('0')
            pourcentage_commission = Decimal(pourcentage_commission_str) if pourcentage_commission_str else Decimal('0')

            commission = (montant_activite * pourcentage_commission) / Decimal('100')
            
            context = {'commission_calculee': commission}
            return render(request, 'gestloto/activites_collecteur/partials/commission_preview.html', context)

        except InvalidOperation:
            context = {'commission_calculee': Decimal('0.00')}
            return render(request, 'gestloto/activites_collecteur/partials/commission_preview.html', context)
        except Exception as e:
            context = {'commission_calculee': Decimal('0.00')}
            return render(request, 'gestloto/activites_collecteur/partials/commission_preview.html', context)

    return HttpResponse("Méthode de requête non valide ou erreur.")