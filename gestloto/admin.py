from django.contrib import admin
from .models import (
    UserProfile, Agent, Collecteur, ActiviteCollecteur, 
    TypeDepense, Depense, Machine, ChiffreAffaire, PenaliteCommission
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'poste_user')
    search_fields = ('user__username', 'user__email', 'poste_user')
    list_filter = ('role',)

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('reference_agent', 'nom_agent', 'prenom_agent', 'num_tel_agent', 'date_debut_activites', 'pourcentage_commission')
    search_fields = ('nom_agent', 'prenom_agent', 'reference_agent', 'num_tel_agent', 'email_agent')
    list_filter = ('date_debut_activites',)

@admin.register(Collecteur)
class CollecteurAdmin(admin.ModelAdmin):
    list_display = ('reference_collecteur', 'nom_collecteur', 'prenom_collecteur', 'num_tel_collecteur', 'date_debut_activites', 'pourcentage_commission')
    search_fields = ('nom_collecteur', 'prenom_collecteur', 'reference_collecteur', 'num_tel_collecteur', 'email_collecteur')
    list_filter = ('date_debut_activites',)

@admin.register(ActiviteCollecteur)
class ActiviteCollecteurAdmin(admin.ModelAdmin):
    list_display = ('collecteur', 'reference_recu', 'date_activite', 'montant_activite', 'pourcentage_commission')
    search_fields = ('collecteur__nom_collecteur', 'collecteur__prenom_collecteur', 'reference_recu')
    list_filter = ('date_activite',)

@admin.register(TypeDepense)
class TypeDepenseAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'details')
    search_fields = ('libelle', 'details')

@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('type_depense', 'agent', 'date_depense', 'montant', 'reference')
    search_fields = ('reference', 'agent__nom_agent', 'agent__prenom_agent')
    list_filter = ('type_depense', 'date_depense')

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('numero_terminal', 'nom_point_vente', 'agent')
    search_fields = ('numero_terminal', 'nom_point_vente', 'agent__nom_agent', 'agent__prenom_agent')
    list_filter = ('agent',)

@admin.register(ChiffreAffaire)
class ChiffreAffaireAdmin(admin.ModelAdmin):
    list_display = ('machine', 'date_chiffre_affaire', 'ventes_totales', 'annulations_totales', 'solde_total', 'montant_commission', 'agent_enregistreur')
    search_fields = ('machine__numero_terminal', 'agent_enregistreur__nom_agent')
    list_filter = ('date_chiffre_affaire', 'jour_tirage')
    readonly_fields = ('montant_commission',)

@admin.register(PenaliteCommission)
class PenaliteCommissionAdmin(admin.ModelAdmin):
    list_display = ('agent', 'machine', 'date_penalite', 'montant_penalite', 'date_commission', 'montant_commission')
    search_fields = ('agent__nom_agent', 'agent__prenom_agent', 'machine__numero_terminal')
    list_filter = ('date_penalite', 'date_commission')

# Personnaliser l'interface d'administration
admin.site.site_header = "Administration LONATO GESTLOTO"
admin.site.site_title = "Portail d'administration LONATO"
admin.site.index_title = "Bienvenue dans le système de gestion LOTO"