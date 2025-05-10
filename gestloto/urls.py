from django.urls import path

from gestloto.views import collecteurs, rapports
from . import views
from .views import (
    dashboard_view, agent_list, agent_detail, agent_create, agent_update, agent_delete,
    collecteur_list, collecteur_detail, collecteur_create, collecteur_update, collecteur_delete,
    machine_list, machine_detail, machine_create, machine_update, machine_delete,
    chiffre_affaire_list, chiffre_affaire_detail, chiffre_affaire_create, chiffre_affaire_update, chiffre_affaire_delete,
    depense_list, depense_create, depense_update, depense_delete,
    activite_collecteur_list, activite_collecteur_create, activite_collecteur_update, activite_collecteur_delete,
    penalite_commission_list, penalite_commission_create, penalite_commission_update, penalite_commission_delete,
    rapport_chiffre_affaire, rapport_depense, rapport_collecteur, rapport_agent,rapports, machines, chiffres_affaire,activites_collecteur
)

urlpatterns = [
    
    path('', views.home, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Gestion des agents
    path('agents/', agent_list, name='agent_list'),
    path('agents/<int:pk>/', agent_detail, name='agent_detail'),
    path('agents/create/', agent_create, name='agent_create'),
    path('agents/<int:pk>/update/', agent_update, name='agent_update'),
    path('agents/<int:pk>/delete/', agent_delete, name='agent_delete'),
    path('export/agents/', rapports.export_agents_report_view, name='export_agents_report'),
    
    
    # Gestion des collecteurs
    path('collecteurs/', collecteur_list, name='collecteur_list'),
    path('collecteurs/<int:pk>/', collecteur_detail, name='collecteur_detail'),
    path('collecteurs/create/', collecteur_create, name='collecteur_create'),
    path('collecteurs/<int:pk>/update/', collecteur_update, name='collecteur_update'),
    path('collecteurs/<int:pk>/delete/', collecteur_delete, name='collecteur_delete'),
     path('export/collecteurs/', rapports.export_collecteurs_report_view, name='export_collecteurs_report'),
    
    # Gestion des machines
    path('machines/', machine_list, name='machine_list'),
    path('machines/<int:pk>/', machine_detail, name='machine_detail'),
    path('machines/create/', machine_create, name='machine_create'),
    path('machines/<int:pk>/update/', machine_update, name='machine_update'),
    path('machines/<int:pk>/delete/', machine_delete, name='machine_delete'),
    # Nouvelle URL pour les informations de la machine (pour HTMX)
    path('ajax/machine-info/', machines.get_machine_info_view, name='machine_info'),
    # Gestion des chiffres d'affaires
    path('chiffres-affaire/', chiffre_affaire_list, name='chiffre_affaire_list'),
    path('chiffres-affaire/<int:pk>/', chiffre_affaire_detail, name='chiffre_affaire_detail'),
    path('chiffres-affaire/create/', chiffre_affaire_create, name='chiffre_affaire_create'),
    path('chiffres-affaire/<int:pk>/update/', chiffre_affaire_update, name='chiffre_affaire_update'),
    path('chiffres-affaire/<int:pk>/delete/', chiffre_affaire_delete, name='chiffre_affaire_delete'),
    path('ajax/calculate-solde/', chiffres_affaire.calculate_solde_view, name='calculate_solde'),
    path('export/ca/', rapports.export_ca_report_view, name='export_ca_report'),

    
    # Gestion des dépenses
    path('depenses/', depense_list, name='depense_list'),
    path('depenses/create/', depense_create, name='depense_create'),
    path('depenses/<int:pk>/update/', depense_update, name='depense_update'),
    path('depenses/<int:pk>/delete/', depense_delete, name='depense_delete'),
    path('export/depenses/', rapports.export_depenses_report_view, name='export_depenses_report'),
    
    # Gestion des activités des collecteurs
    path('activites-collecteurs/', activite_collecteur_list, name='activite_collecteur_list'),
    path('activites-collecteurs/create/', activite_collecteur_create, name='activite_collecteur_create'),
    path('activites-collecteurs/<int:pk>/update/', activite_collecteur_update, name='activite_collecteur_update'),
    path('activites-collecteurs/<int:pk>/delete/', activite_collecteur_delete, name='activite_collecteur_delete'),
    path('get-collecteur-commission/', collecteurs.get_collecteur_commission_view, name='get_collecteur_commission'),
    path('ajax/calculate-commission/', activites_collecteur.calculate_commission_view, name='calculate_commission'),

    # Gestion des pénalités et commissions
    path('penalites-commissions/', penalite_commission_list, name='penalite_commission_list'),
    path('penalites-commissions/create/', penalite_commission_create, name='penalite_commission_create'),
    path('penalites-commissions/<int:pk>/update/', penalite_commission_update, name='penalite_commission_update'),
    path('penalites-commissions/<int:pk>/delete/', penalite_commission_delete, name='penalite_commission_delete'),
    
    # Rapports
    path('rapports/chiffres-affaire/', rapport_chiffre_affaire, name='rapport_chiffre_affaire'),
    path('rapports/depenses/', rapport_depense, name='rapport_depense'),
    path('rapports/collecteurs/', rapport_collecteur, name='rapport_collecteur'),
    path('rapports/agents/', rapport_agent, name='rapport_agent'),
]