from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import ActiviteCollecteur, Collecteur
from ..forms import ActiviteCollecteurForm
from django.http import HttpResponse # Ajout pour HttpResponse
from decimal import Decimal, InvalidOperation # Ajout pour les calculs et la gestion d'erreur

@login_required
def activite_collecteur_list(request):
    collecteur_filter = request.GET.get('collecteur', None)
    
    activites = ActiviteCollecteur.objects.all()
    
    if collecteur_filter:
        activites = activites.filter(collecteur__id=collecteur_filter)
    
    activites = activites.select_related('collecteur').order_by('-date_activite')
    collecteurs = Collecteur.objects.all()
    
    context = {
        'activites': activites,
        'collecteurs': collecteurs,
        'collecteur_filter': collecteur_filter,
    }
    
    return render(request, 'gestloto/activites_collecteur/list.html', context)

@login_required
def activite_collecteur_create(request):
    if request.method == 'POST':
        form = ActiviteCollecteurForm(request.POST)
        if form.is_valid():
            activite = form.save()
            messages.success(request, f"L'activité du collecteur {activite.collecteur} a été créée avec succès.")
            return redirect('activite_collecteur_list')
    else:
        form = ActiviteCollecteurForm()
    
    return render(request, 'gestloto/activites_collecteur/form.html', {'form': form, 'title': 'Ajouter une activité de collecteur'})

@login_required
def activite_collecteur_update(request, pk):
    activite = get_object_or_404(ActiviteCollecteur, pk=pk)
    if request.method == 'POST':
        form = ActiviteCollecteurForm(request.POST, instance=activite)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'activité du collecteur {activite.collecteur} a été modifiée avec succès.")
            return redirect('activite_collecteur_list')
    else:
        form = ActiviteCollecteurForm(instance=activite)
    
    return render(request, 'gestloto/activites_collecteur/form.html', {
        'form': form, 
        'activite': activite, 
        'title': 'Modifier une activité de collecteur'
    })

@login_required
def activite_collecteur_delete(request, pk):
    activite = get_object_or_404(ActiviteCollecteur, pk=pk)
    if request.method == 'POST':
        collecteur_nom = activite.collecteur
        date_activite = activite.date_activite
        activite.delete()
        messages.success(request, f"L'activité du {date_activite} pour le collecteur {collecteur_nom} a été supprimée.")
        return redirect('activite_collecteur_list')
    
    return render(request, 'gestloto/activites_collecteur/delete.html', {'activite': activite})

@login_required
def calculate_commission_view(request):
    montant_activite_str = request.GET.get('montant_activite')
    pourcentage_commission_str = request.GET.get('pourcentage_commission')

    if montant_activite_str and pourcentage_commission_str:
        try:
            montant_activite = Decimal(montant_activite_str)
            pourcentage_commission = Decimal(pourcentage_commission_str)
            
            if montant_activite < 0 or pourcentage_commission < 0:
                # Gérer les valeurs négatives si nécessaire, ici on retourne 0 ou un message d'erreur
                commission_calculee_html = '<span class="text-error text-sm">Montant ou pourcentage invalide.</span>'
                return HttpResponse(commission_calculee_html)

            commission = (montant_activite * pourcentage_commission) / Decimal('100')
            # Formatter la commission à deux décimales
            commission_formatee = "{:.2f}".format(commission)
            
            # Le HTML retourné doit correspondre à ce que hx-target attend.
            # Si c'est pour afficher dans un simple span ou div :
            commission_calculee_html = f'<span id="commission-preview" class="text-success font-bold">{commission_formatee} FCFA</span>'
            # Si vous voulez remplacer un input (par exemple, pour un champ de commission calculée non modifiable) :
            # commission_calculee_html = f'<input type="text" name="commission_calculee" value="{commission_formatee}" class="input input-bordered" readonly>'
            
            return HttpResponse(commission_calculee_html)
        except InvalidOperation:
            # Gérer le cas où la conversion en Decimal échoue (par exemple, texte non numérique)
            error_html = '<span id="commission-preview" class="text-error text-sm">Valeurs numériques invalides.</span>'
            return HttpResponse(error_html)
        except Exception:
            # Gérer toute autre erreur inattendue
            error_html = '<span id="commission-preview" class="text-error text-sm">Erreur de calcul.</span>'
            return HttpResponse(error_html)
    else:
        # Si les paramètres sont manquants, retourner un message ou un état initial
        # Cela peut être un span vide ou un message indiquant d'entrer les valeurs
        initial_html = '<span id="commission-preview" class="text-info text-sm">Entrez montant et % commission.</span>'
        return HttpResponse(initial_html)