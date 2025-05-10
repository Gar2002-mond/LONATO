from django import forms
from .models import (
    Agent, Collecteur, ActiviteCollecteur, Machine, ChiffreAffaire,
    TypeDepense, Depense, PenaliteCommission
)
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserCreateForm(UserCreationForm):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('user', 'Utilisateur simple'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    poste_user = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = ['nom_agent', 'prenom_agent', 'reference_agent', 'num_tel_agent', 'email_agent', 
                 'date_debut_activites', 'pourcentage_commission', 'autres_details']
        widgets = {
            'date_debut_activites': forms.DateInput(attrs={'type': 'date'}),
            'autres_details': forms.Textarea(attrs={'rows': 3}),
        }

class CollecteurForm(forms.ModelForm):
    class Meta:
        model = Collecteur
        fields = ['nom_collecteur', 'prenom_collecteur', 'reference_collecteur', 'num_tel_collecteur', 
                 'email_collecteur', 'date_debut_activites', 'pourcentage_commission', 'autres_details']
        widgets = {
            'date_debut_activites': forms.DateInput(attrs={'type': 'date'}),
            'autres_details': forms.Textarea(attrs={'rows': 3}),
        }

class ActiviteCollecteurForm(forms.ModelForm):
    class Meta:
        model = ActiviteCollecteur
        fields = ['collecteur', 'pourcentage_commission', 'reference_recu', 'date_activite', 
                 'montant_activite', 'observations', 'autres_details']
        widgets = {
            'date_activite': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
            'autres_details': forms.Textarea(attrs={'rows': 3}),
        }

class TypeDepenseForm(forms.ModelForm):
    class Meta:
        model = TypeDepense
        fields = ['libelle', 'details', 'autres_details']
        widgets = {
            'details': forms.Textarea(attrs={'rows': 3}),
            'autres_details': forms.Textarea(attrs={'rows': 3}),
        }

class DepenseForm(forms.ModelForm):
    class Meta:
        model = Depense
        fields = ['type_depense', 'agent', 'date_depense', 'montant', 'reference', 'autres_details']
        widgets = {
            'date_depense': forms.DateInput(attrs={'type': 'date'}),
            'autres_details': forms.Textarea(attrs={'rows': 3}),
        }

class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ['numero_terminal', 'nom_point_vente', 'details', 'agent']
        widgets = {
            'details': forms.Textarea(attrs={'rows': 3}),
        }

class ChiffreAffaireForm(forms.ModelForm):
    class Meta:
        model = ChiffreAffaire
        fields = ['machine', 'date_chiffre_affaire', 'ventes_totales', 'annulations_totales', 
                 'paiements_totaux', 'solde_total', 'pourcentage_commission_potentielle', 
                 'agent_enregistreur', 'jour_tirage', 'observations', 'autres_details']
        exclude = ['montant_commission']  # Calculé automatiquement
        widgets = {
            'date_chiffre_affaire': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
            'autres_details': forms.Textarea(attrs={'rows': 3}),
        }

class PenaliteCommissionForm(forms.ModelForm):
    class Meta:
        model = PenaliteCommission
        fields = ['machine', 'agent', 'date_penalite', 'montant_penalite', 'motif_penalite',
                 'date_commission', 'montant_commission', 'observations', 'autres_details']
        widgets = {
            'date_penalite': forms.DateInput(attrs={'type': 'date'}),
            'date_commission': forms.DateInput(attrs={'type': 'date'}),
            'motif_penalite': forms.Textarea(attrs={'rows': 3}),
            'observations': forms.Textarea(attrs={'rows': 3}),
            'autres_details': forms.Textarea(attrs={'rows': 3}),
        }

class DateRangeForm(forms.Form):
    date_debut = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    date_fin = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))