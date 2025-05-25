from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from ..models import ChiffreAffaire, Machine, Agent
from ..forms import ChiffreAffaireForm

@login_required
def chiffre_affaire_list(request):
    # Récupération des paramètres de recherche et filtrage
    search_query = request.GET.get('q', '').strip()
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    machine_filter = request.GET.get('machine', '')
    agent_filter = request.GET.get('agent', '')
    sort_by = request.GET.get('sort', '-date_chiffre_affaire')
    page_number = request.GET.get('page', 1)
    
    # Base queryset avec préchargement des relations
    chiffres_queryset = ChiffreAffaire.objects.select_related('machine', 'agent_enregistreur').all()
    
    # Application de la recherche
    if search_query:
        chiffres_queryset = chiffres_queryset.filter(
            Q(machine__numero_terminal__icontains=search_query) |
            Q(machine__nom_point_vente__icontains=search_query) |
            Q(agent_enregistreur__nom_agent__icontains=search_query) |
            Q(agent_enregistreur__prenom_agent__icontains=search_query) |
            Q(observations__icontains=search_query)
        )
    
    # Application des filtres
    if machine_filter:
        chiffres_queryset = chiffres_queryset.filter(machine_id=machine_filter)
    
    if agent_filter:
        chiffres_queryset = chiffres_queryset.filter(agent_enregistreur_id=agent_filter)
    
    # Filtrage par dates
    if date_debut:
        try:
            chiffres_queryset = chiffres_queryset.filter(date_chiffre_affaire__gte=date_debut)
        except ValueError:
            pass
    
    if date_fin:
        try:
            chiffres_queryset = chiffres_queryset.filter(date_chiffre_affaire__lte=date_fin)
        except ValueError:
            pass
    
    # Application du tri
    valid_sort_fields = [
        'date_chiffre_affaire', '-date_chiffre_affaire', 
        'solde_total', '-solde_total',
        'montant_commission', '-montant_commission',
        'machine__numero_terminal', '-machine__numero_terminal',
        'ventes_totales', '-ventes_totales'
    ]
    
    if sort_by in valid_sort_fields:
        chiffres_queryset = chiffres_queryset.order_by(sort_by)
    else:
        chiffres_queryset = chiffres_queryset.order_by('-date_chiffre_affaire')
    
    # Calcul des statistiques
    stats = chiffres_queryset.aggregate(
        total_ventes=Sum('ventes_totales') or 0,
        total_annulations=Sum('annulations_totales') or 0,
        total_paiements=Sum('paiements_totaux') or 0,
        total_solde=Sum('solde_total') or 0,
        total_commission=Sum('montant_commission') or 0,
        nb_enregistrements=Count('id'),
        solde_moyen=Avg('solde_total') or 0
    )
    
    # Statistiques par machine
    stats_par_machine = chiffres_queryset.values(
        'machine__numero_terminal', 'machine__nom_point_vente'
    ).annotate(
        total_solde=Sum('solde_total'),
        total_commission=Sum('montant_commission'),
        count=Count('id')
    ).order_by('-total_solde')[:5]
    
    # CA ce mois
    first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ca_ce_mois = ChiffreAffaire.objects.filter(
        date_chiffre_affaire__gte=first_day_of_month
    ).aggregate(total=Sum('solde_total'))['total'] or 0
    
    # Pagination
    paginator = Paginator(chiffres_queryset, 20)  # 20 enregistrements par page
    chiffres = paginator.get_page(page_number)
    
    # Données pour les filtres
    machines = Machine.objects.all().order_by('numero_terminal')
    agents = Agent.objects.all().order_by('nom_agent', 'prenom_agent')
    
    context = {
        'chiffres': chiffres,
        'machines': machines,
        'agents': agents,
        'stats': stats,
        'stats_par_machine': stats_par_machine,
        'ca_ce_mois': ca_ce_mois,
        'search_query': search_query,
        'machine_filter': machine_filter,
        'agent_filter': agent_filter,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'sort_by': sort_by,
    }
    
    # Si c'est une requête HTMX, ne retourner que le contenu de la liste
    if request.headers.get('HX-Request'):
        return render(request, 'gestloto/chiffres_affaire/list_partial.html', context)
    
    return render(request, 'gestloto/chiffres_affaire/list.html', context)

@login_required
def chiffre_affaire_detail(request, pk):
    chiffre_affaire = get_object_or_404(ChiffreAffaire, pk=pk)
    return render(request, 'gestloto/chiffres_affaire/detail.html', {'chiffre_affaire': chiffre_affaire})

@login_required
def chiffre_affaire_create(request):
    if request.method == 'POST':
        form = ChiffreAffaireForm(request.POST)
        if form.is_valid():
            chiffre_affaire = form.save(commit=False)
            # Le montant_commission est calculé automatiquement lors du save()
            chiffre_affaire.save()
            
            messages.success(request, f"Le chiffre d'affaires pour la machine {chiffre_affaire.machine.numero_terminal} a été créé avec succès.")
            
            # Standardisation sur HTMX uniquement
            if request.headers.get('HX-Request'):
                return redirect('chiffre_affaire_list')
            
            return redirect('chiffre_affaire_list')
        else:
            # Si le formulaire n'est pas valide et c'est HTMX
            if request.headers.get('HX-Request'):
                return render(request, 'gestloto/chiffres_affaire/form_partial.html', {'form': form})
    else:
        form = ChiffreAffaireForm()
    
    return render(request, 'gestloto/chiffres_affaire/form.html', {
        'form': form, 
        'title': "Ajouter un chiffre d'affaires",
        'submit_text': 'Créer le chiffre d\'affaires'
    })

@login_required
def chiffre_affaire_update(request, pk):
    chiffre_affaire = get_object_or_404(ChiffreAffaire, pk=pk)
    if request.method == 'POST':
        form = ChiffreAffaireForm(request.POST, instance=chiffre_affaire)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le chiffre d'affaires pour la machine {chiffre_affaire.machine.numero_terminal} a été modifié avec succès.")
            
            # Standardisation sur HTMX uniquement
            if request.headers.get('HX-Request'):
                return redirect('chiffre_affaire_list')
            
            return redirect('chiffre_affaire_detail', pk=chiffre_affaire.pk)
        else:
            # Si le formulaire n'est pas valide et c'est HTMX
            if request.headers.get('HX-Request'):
                return render(request, 'gestloto/chiffres_affaire/form_partial.html', {'form': form})
    else:
        form = ChiffreAffaireForm(instance=chiffre_affaire)
    
    return render(request, 'gestloto/chiffres_affaire/form.html', {
        'form': form, 
        'chiffre_affaire': chiffre_affaire, 
        'title': "Modifier un chiffre d'affaires",
        'submit_text': 'Sauvegarder les modifications'
    })

@login_required
def chiffre_affaire_delete(request, pk):
    chiffre_affaire = get_object_or_404(ChiffreAffaire, pk=pk)
    if request.method == 'POST':
        machine_numero = chiffre_affaire.machine.numero_terminal
        date = chiffre_affaire.date_chiffre_affaire
        chiffre_affaire.delete()
        
        # Standardisation sur HTMX uniquement
        if request.headers.get('HX-Request'):
            messages.success(request, f"Le chiffre d'affaires du {date} pour la machine {machine_numero} a été supprimé.")
            return redirect('chiffre_affaire_list')
        
        messages.success(request, f"Le chiffre d'affaires du {date} pour la machine {machine_numero} a été supprimé.")
        return redirect('chiffre_affaire_list')
    
    return render(request, 'gestloto/chiffres_affaire/delete.html', {'chiffre_affaire': chiffre_affaire})

def calculate_solde_view(request):
    if request.method == 'POST':
        try:
            ventes_totales_str = request.POST.get('ventes_totales', '0')
            annulations_totales_str = request.POST.get('annulations_totales', '0')
            paiements_totaux_str = request.POST.get('paiements_totaux', '0')

            # Gérer les chaînes vides ou non valides en les traitant comme zéro
            ventes_totales = Decimal(ventes_totales_str) if ventes_totales_str else Decimal('0')
            annulations_totales = Decimal(annulations_totales_str) if annulations_totales_str else Decimal('0')
            paiements_totaux = Decimal(paiements_totaux_str) if paiements_totaux_str else Decimal('0')

            solde_total = ventes_totales - annulations_totales - paiements_totaux
            
            context = {'solde_total': solde_total}
            return render(request, 'gestloto/chiffres_affaire/partials/solde_total_input.html', context)

        except InvalidOperation:
            context = {'solde_total': Decimal('0.00')}
            return render(request, 'gestloto/chiffres_affaire/partials/solde_total_input.html', context)
        except Exception as e:
            context = {'solde_total': Decimal('0.00')}
            return render(request, 'gestloto/chiffres_affaire/partials/solde_total_input.html', context)

    return HttpResponseBadRequest("Méthode de requête non valide ou erreur.")
