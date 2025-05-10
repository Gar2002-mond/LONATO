from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import ActiviteCollecteur, Collecteur
from ..forms import ActiviteCollecteurForm

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