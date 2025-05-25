from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('user', 'Utilisateur simple'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    poste_user = models.CharField(max_length=100, blank=True)
    autres_details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

class Agent(models.Model):
    nom_agent = models.CharField(max_length=100)
    prenom_agent = models.CharField(max_length=100)
    reference_agent = models.CharField(max_length=50, unique=True)
    num_tel_agent = models.CharField(max_length=20)
    email_agent = models.EmailField(blank=True)
    date_debut_activites = models.DateField(default=timezone.now)
    pourcentage_commission = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Pourcentage de commission pour l'agent"
    )
    autres_details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nom_agent} {self.prenom_agent} - {self.reference_agent}"
    
    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"

class Collecteur(models.Model):
    nom_collecteur = models.CharField(max_length=100)
    prenom_collecteur = models.CharField(max_length=100)
    reference_collecteur = models.CharField(max_length=50, unique=True)
    num_tel_collecteur = models.CharField(max_length=20)
    email_collecteur = models.EmailField(blank=True)
    date_debut_activites = models.DateField(default=timezone.now)
    pourcentage_commission = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Pourcentage de commission pour le collecteur"
    )
    autres_details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nom_collecteur} {self.prenom_collecteur} - {self.reference_collecteur}"
    
    class Meta:
        verbose_name = "Collecteur"
        verbose_name_plural = "Collecteurs"

class ActiviteCollecteur(models.Model):
    collecteur = models.ForeignKey(Collecteur, on_delete=models.CASCADE, related_name='activites')
    pourcentage_commission = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    reference_recu = models.CharField(max_length=100)
    date_activite = models.DateField(default=timezone.now)
    montant_activite = models.DecimalField(max_digits=15, decimal_places=2)
    observations = models.TextField(blank=True)
    autres_details = models.TextField(blank=True)

    def clean(self):
        
        # Validation pour s'assurer que la date n'est pas dans le futur
        if self.date_activite and self.date_activite > timezone.now().date():
            raise ValidationError({
                'date_activite': 'La date d\'activité ne peut pas être dans le futur.'
            })
    
    def __str__(self):
        return f"Activité de {self.collecteur} - {self.date_activite}"
    
    class Meta:
        verbose_name = "Activité collecteur"
        verbose_name_plural = "Activités collecteurs"

class TypeDepense(models.Model):
    LIBELLE_CHOICES = [
        ('salaire', 'Salaire'),
        ('loyer', 'Loyer'),
        ('impot', 'Impôt'),
        ('fourniture', 'Achat Fourniture'),
        ('autre', 'Autre'),
    ]
    libelle = models.CharField(max_length=20, choices=LIBELLE_CHOICES)
    details = models.TextField(blank=True)
    autres_details = models.TextField(blank=True)

    def __str__(self):
        return self.get_libelle_display()
    
    class Meta:
        verbose_name = "Type de dépense"
        verbose_name_plural = "Types de dépenses"

class Depense(models.Model):
    type_depense = models.ForeignKey(TypeDepense, on_delete=models.PROTECT, related_name='depenses')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='depenses')
    date_depense = models.DateField(default=timezone.now)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    reference = models.CharField(max_length=100)
    autres_details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.type_depense} - {self.montant} - {self.date_depense}"
    
    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"

class Machine(models.Model):
    numero_terminal = models.CharField(max_length=50, unique=True)
    nom_point_vente = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='machines')

    def __str__(self):
        return f"{self.numero_terminal} - {self.nom_point_vente}"
    
    class Meta:
        verbose_name = "Machine"
        verbose_name_plural = "Machines"

class ChiffreAffaire(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='chiffres_affaire')
    date_chiffre_affaire = models.DateField(default=timezone.now)
    ventes_totales = models.DecimalField(max_digits=15, decimal_places=2)
    annulations_totales = models.DecimalField(max_digits=15, decimal_places=2)
    paiements_totaux = models.DecimalField(max_digits=15, decimal_places=2)
    solde_total = models.DecimalField(max_digits=15, decimal_places=2)
    pourcentage_commission_potentielle = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Pourcentage de commission potentielle pour la société"
    )
    montant_commission = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    agent_enregistreur = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='chiffres_enregistres')
    jour_tirage = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text="Jour de tirage (de J1 à J365)"
    )
    observations = models.TextField(blank=True)
    autres_details = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Calculer automatiquement le montant de la commission
        self.montant_commission = (self.solde_total * self.pourcentage_commission_potentielle) / Decimal('100.0')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.machine} - {self.date_chiffre_affaire} - {self.solde_total}"
    
    class Meta:
        verbose_name = "Chiffre d'affaire"
        verbose_name_plural = "Chiffres d'affaire"

class PenaliteCommission(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='penalites_commissions')
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='penalites_commissions')
    date_penalite = models.DateField(null=True, blank=True)
    montant_penalite = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    motif_penalite = models.TextField(blank=True)
    date_commission = models.DateField(null=True, blank=True)
    montant_commission = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    observations = models.TextField(blank=True)
    autres_details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.agent} - {self.date_penalite or self.date_commission}"
    
    class Meta:
        verbose_name = "Pénalité et commission"
        verbose_name_plural = "Pénalités et commissions"