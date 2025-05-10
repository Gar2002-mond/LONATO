from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from ..models import Collecteur, ActiviteCollecteur
from ..forms import CollecteurForm
from django.http import HttpResponse, Http404
# from django.shortcuts import render # Déjà importé plus haut

from decimal import Decimal # Ajouté pour les calculs financiers précis
from django.db.models.functions import Coalesce # Ajouté pour gérer les agrégations NULL

# ... autres vues
@login_required
def collecteur_list(request):
    collecteurs = Collecteur.objects.all().order_by('nom_collecteur')
    return render(request, 'gestloto/collecteurs/list.html', {'collecteurs': collecteurs})

@login_required
def collecteur_detail(request, pk):
    collecteur = get_object_or_404(Collecteur, pk=pk)
    # Supposons que 'activites' est le related_name correct pour ActiviteCollecteur depuis Collecteur
    activites = collecteur.activites.all().order_by('-date_activite')[:15] 
    
    commission_rate_percentage = collecteur.pourcentage_commission
    # S'assurer que commission_rate_percentage est un Decimal, avec 0 par défaut si None
    if commission_rate_percentage is None:
        commission_rate_percentage = Decimal('0')
    else:
        # S'assurer que c'est un Decimal, au cas où ce serait un float ou int depuis la BDD
        commission_rate_percentage = Decimal(str(commission_rate_percentage)) 

    # Statistiques des activités
    aggregated_data = collecteur.activites.aggregate(
        # Coalesce Sum en Decimal('0.00') pour éviter les problèmes avec None * Decimal
        # et pour s'assurer que total_montant n'est jamais None.
        # Suppose que 'montant_activite' est un champ qui peut être sommé (ex: DecimalField, IntegerField, FloatField)
        total_montant_sum=Coalesce(Sum('montant_activite'), Decimal('0.00'))
    )
    
    total_montant = aggregated_data['total_montant_sum']
    
    # Calculer la commission en utilisant la somme agrégée et le taux de commission
    total_commission = (total_montant * commission_rate_percentage) / Decimal('100')
            
    stats = {
        'total_montant': total_montant,    # Sera Decimal('0.00') s'il n'y a pas d'activités ou si la somme est 0
        'total_commission': total_commission, # Sera aussi Decimal('0.00') si total_montant ou le taux est 0
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
        messages.success(request, f"Le collecteur {nom_complet} a été supprimé.")
        return redirect('collecteur_list')
    
    return render(request, 'gestloto/collecteurs/delete.html', {'collecteur': collecteur})

def get_collecteur_commission_view(request):
    collecteur_id = request.GET.get('collecteur') # HTMX enverra la valeur du select avec le nom 'collecteur'

    if not collecteur_id:
        # Renvoyer un input vide ou avec une valeur par défaut si aucun collecteur n'est sélectionné
        # ou si la requête est faite sans ce paramètre pour une raison quelconque.
        html_response = '<input type="number" name="pourcentage_commission" value="" class="input input-bordered" readonly placeholder="Sélectionnez un collecteur d\'abord">'
        return HttpResponse(html_response)

    try:
        collecteur = Collecteur.objects.get(id=collecteur_id)
        commission = collecteur.pourcentage_commission
        if commission is None: # Gérer le cas où la commission est None
            commission = "" # Ou une valeur par défaut comme 0

        # Renvoyer l'input avec la valeur de la commission.
        # Il est important que cet input ait les mêmes attributs (name, class) que celui qu'il remplace
        # pour que le style et la soumission du formulaire fonctionnent toujours.
        # L'attribut 'readonly' est généralement une bonne idée si cette valeur est dérivée.
        html_response = f'<input type="number" name="pourcentage_commission" value="{commission}" class="input input-bordered" readonly>'
        return HttpResponse(html_response)
    except Collecteur.DoesNotExist:
        html_response = '<input type="number" name="pourcentage_commission" value="" class="input input-bordered" readonly placeholder="Collecteur non trouvé">'
        return HttpResponse(html_response)
    except ValueError: # Au cas où collecteur_id ne serait pas un entier valide
        html_response = '<input type="number" name="pourcentage_commission" value="" class="input input-bordered" readonly placeholder="ID de collecteur invalide">'
        return HttpResponse(html_response)
