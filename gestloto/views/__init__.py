from .dashboard import dashboard_view
from .agents import agent_list, agent_detail, agent_create, agent_update, agent_delete
from .collecteurs import collecteur_list, collecteur_detail, collecteur_create, collecteur_update, collecteur_delete
from .machines import machine_list, machine_detail, machine_create, machine_update, machine_delete
from .chiffres_affaire import chiffre_affaire_list, chiffre_affaire_detail, chiffre_affaire_create, chiffre_affaire_update, chiffre_affaire_delete
from .depenses import depense_list, depense_create, depense_update, depense_delete
from .activites_collecteur import activite_collecteur_list, activite_collecteur_create, activite_collecteur_update, activite_collecteur_delete
from .penalites_commissions import penalite_commission_list, penalite_commission_create, penalite_commission_update, penalite_commission_delete
from .rapports import rapport_chiffre_affaire, rapport_depense, rapport_collecteur, rapport_agent

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def home(request):
    """Vue de la page d'accueil"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'gestloto/home.html')