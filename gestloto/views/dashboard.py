from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from ..models import ChiffreAffaire, Machine, Agent, Collecteur, Depense
from django.db import models

@login_required
def dashboard_view(request):
    """Tableau de bord principal avec les statistiques et données récentes"""
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    # Statistiques générales
    stats = {
        'total_machines': Machine.objects.count(),
        'total_agents': Agent.objects.count(),
        'total_collecteurs': Collecteur.objects.count(),
    }
    
    # Chiffres d'affaires
    ca_today = ChiffreAffaire.objects.filter(date_chiffre_affaire=today).aggregate(
        total_ventes=Sum('ventes_totales'),
        total_solde=Sum('solde_total'),
        total_commission=Sum('montant_commission')
    )
    
    ca_month = ChiffreAffaire.objects.filter(date_chiffre_affaire__gte=start_of_month).aggregate(
        total_ventes=Sum('ventes_totales'),
        total_solde=Sum('solde_total'),
        total_commission=Sum('montant_commission')
    )
    
    # Dépenses du mois
    depenses_month = Depense.objects.filter(date_depense__gte=start_of_month).aggregate(
        total_depenses=Sum('montant')
    )
    
    # Chiffres d'affaires récents
    recent_ca = ChiffreAffaire.objects.select_related('machine', 'agent_enregistreur').order_by('-date_chiffre_affaire')[:10]
    
    # Top machines (par chiffre d'affaires)
    top_machines = Machine.objects.annotate(
        total_ca=Sum('chiffres_affaire__solde_total')
    ).filter(total_ca__isnull=False).order_by('-total_ca')[:5]
    
    # Top agents (par nombre de machines gérées)
    top_agents = Agent.objects.annotate(
        nb_machines=models.Count('machines')
    ).order_by('-nb_machines')[:5]
    
    context = {
        'stats': stats,
        'ca_today': ca_today,
        'ca_month': ca_month,
        'depenses_month': depenses_month,
        'recent_ca': recent_ca,
        'top_machines': top_machines,
        'top_agents': top_agents,
    }
    
    return render(request, 'gestloto/dashboard.html', context)