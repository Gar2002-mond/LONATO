from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from ..models import Collecteur, ActiviteCollecteur
from ..forms import CollecteurForm

@login_required
def collecteur_list(request):
    collecteurs = Collecteur.objects.all().order_by('nom_collecteur')
    return render(request, 'gestloto/collecteurs/list.html', {'collecteurs': collecteurs})

@login_required
def collecteur_detail(request, pk):
    collecteur = get_object_or_404(Collecteur, pk=pk)
    activites = collecteur.activites.all().order_by('-date_activite')[:15]
    
    # Statistiques des activités
    stats = collecteur.activites.aggregate(
        total_montant=Sum('montant_activite'),
        total_commission=Sum('montant_activite') * collecteur.pourcentage_commission / 100
    )
    
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