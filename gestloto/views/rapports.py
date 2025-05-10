from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from ..models import ChiffreAffaire, Depense, Collecteur, Agent, ActiviteCollecteur, PenaliteCommission, Machine
from ..forms import DateRangeForm

@login_required
def rapport_chiffre_affaire(request):
    """Rapport sur les chiffres d'affaires"""
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    machine_id = request.GET.get('machine')
    form = DateRangeForm(request.GET or None)
    
    # Valeurs par défaut si non spécifiées
    if not date_debut:
        date_debut = (timezone.now() - timedelta(days=30)).date().strftime('%Y-%m-%d')
    if not date_fin:
        date_fin = timezone.now().date().strftime('%Y-%m-%d')
    
    chiffres = ChiffreAffaire.objects.filter(
        date_chiffre_affaire__range=[date_debut, date_fin]
    )
    
    if machine_id:
        chiffres = chiffres.filter(machine_id=machine_id)
    
    # Statistiques globales
    stats = chiffres.aggregate(
        total_ventes=Sum('ventes_totales'),
        total_annulations=Sum('annulations_totales'),
        total_paiements=Sum('paiements_totaux'),
        total_solde=Sum('solde_total'),
        total_commission=Sum('montant_commission'),
    )
    
    # Chiffres par machine
    chiffres_par_machine = chiffres.values('machine__numero_terminal', 'machine__nom_point_vente').annotate(
        total_ventes=Sum('ventes_totales'),
        total_solde=Sum('solde_total'),
        total_commission=Sum('montant_commission'),
        nombre_jours=Count('id')
    ).order_by('-total_solde')
    
    # Chiffres par jour
    chiffres_par_jour = chiffres.values('date_chiffre_affaire').annotate(
        total_ventes=Sum('ventes_totales'),
        total_solde=Sum('solde_total'),
        total_commission=Sum('montant_commission'),
        nombre_machines=Count('machine', distinct=True)
    ).order_by('date_chiffre_affaire')
    
    context = {
        'form': form,
        'stats': stats,
        'chiffres_par_machine': chiffres_par_machine,
        'chiffres_par_jour': chiffres_par_jour,
        'machines': Machine.objects.all(),
        'machine_id': machine_id,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    
    return render(request, 'gestloto/rapports/chiffre_affaire.html', context)

@login_required
def rapport_depense(request):
    """Rapport sur les dépenses"""
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    form = DateRangeForm(request.GET or None)
    
    # Valeurs par défaut si non spécifiées
    if not date_debut:
        date_debut = (timezone.now() - timedelta(days=30)).date().strftime('%Y-%m-%d')
    if not date_fin:
        date_fin = timezone.now().date().strftime('%Y-%m-%d')
    
    depenses = Depense.objects.filter(
        date_depense__range=[date_debut, date_fin]
    )
    
    # Statistiques globales
    stats = depenses.aggregate(
        total_depenses=Sum('montant'),
        nombre_depenses=Count('id'),
    )
    
    # Dépenses par type
    depenses_par_type = depenses.values('type_depense__libelle').annotate(
        total=Sum('montant'),
        nombre=Count('id')
    ).order_by('-total')
    
    # Dépenses par mois
    depenses_par_mois = depenses.annotate(
        mois=TruncMonth('date_depense')
    ).values('mois').annotate(
        total=Sum('montant'),
        nombre=Count('id')
    ).order_by('mois')
    
    context = {
        'form': form,
        'stats': stats,
        'depenses_par_type': depenses_par_type,
        'depenses_par_mois': depenses_par_mois,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    
    return render(request, 'gestloto/rapports/depense.html', context)

@login_required
def rapport_collecteur(request):
    """Rapport sur les collecteurs"""
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    form = DateRangeForm(request.GET or None)
    
    # Valeurs par défaut si non spécifiées
    if not date_debut:
        date_debut = (timezone.now() - timedelta(days=30)).date().strftime('%Y-%m-%d')
    if not date_fin:
        date_fin = timezone.now().date().strftime('%Y-%m-%d')
    
    activites = ActiviteCollecteur.objects.filter(
        date_activite__range=[date_debut, date_fin]
    )
    
    # Statistiques globales
    stats = activites.aggregate(
        total_montant=Sum('montant_activite'),
        nombre_activites=Count('id'),
    )
    
    # Commission calculée (montant * pourcentage / 100)
    commission_expression = ExpressionWrapper(
        F('montant_activite') * F('pourcentage_commission') / 100,
        output_field=DecimalField(max_digits=15, decimal_places=2)
    )
    
    # Activités par collecteur
    activites_par_collecteur = activites.values(
        'collecteur__reference_collecteur', 
        'collecteur__nom_collecteur', 
        'collecteur__prenom_collecteur'
    ).annotate(
        total_montant=Sum('montant_activite'),
        total_commission=Sum(commission_expression),
        nombre_activites=Count('id')
    ).order_by('-total_montant')
    
    context = {
        'form': form,
        'stats': stats,
        'activites_par_collecteur': activites_par_collecteur,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    
    return render(request, 'gestloto/rapports/collecteur.html', context)

@login_required
def rapport_agent(request):
    """Rapport sur les agents"""
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    form = DateRangeForm(request.GET or None)
    
    # Valeurs par défaut si non spécifiées
    if not date_debut:
        date_debut = (timezone.now() - timedelta(days=30)).date().strftime('%Y-%m-%d')
    if not date_fin:
        date_fin = timezone.now().date().strftime('%Y-%m-%d')
    
    chiffres = ChiffreAffaire.objects.filter(
        date_chiffre_affaire__range=[date_debut, date_fin]
    )
    
    penalites = PenaliteCommission.objects.filter(
        date_penalite__range=[date_debut, date_fin]
    )
    
    commissions = PenaliteCommission.objects.filter(
        date_commission__range=[date_debut, date_fin]
    )
    
    # Statistiques par agent pour les chiffres d'affaires
    chiffres_par_agent = chiffres.values(
        'agent_enregistreur__reference_agent',
        'agent_enregistreur__nom_agent',
        'agent_enregistreur__prenom_agent'
    ).annotate(
        total_ventes=Sum('ventes_totales'),
        total_solde=Sum('solde_total'),
        total_commission=Sum('montant_commission'),
        nombre_enregistrements=Count('id')
    ).order_by('-total_solde')
    
    # Statistiques pour les pénalités et commissions
    penalites_par_agent = penalites.values(
        'agent__reference_agent',
        'agent__nom_agent',
        'agent__prenom_agent'
    ).annotate(
        total_penalites=Sum('montant_penalite'),
        nombre_penalites=Count('id')
    ).order_by('-total_penalites')
    
    commissions_par_agent = commissions.values(
        'agent__reference_agent',
        'agent__nom_agent',
        'agent__prenom_agent'
    ).annotate(
        total_commissions=Sum('montant_commission'),
        nombre_commissions=Count('id')
    ).order_by('-total_commissions')
    
    context = {
        'form': form,
        'chiffres_par_agent': chiffres_par_agent,
        'penalites_par_agent': penalites_par_agent,
        'commissions_par_agent': commissions_par_agent,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    
    return render(request, 'gestloto/rapports/agent.html', context)