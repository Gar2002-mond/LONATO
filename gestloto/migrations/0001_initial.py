# Generated by Django 5.2.1 on 2025-05-09 22:51

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_agent', models.CharField(max_length=100)),
                ('prenom_agent', models.CharField(max_length=100)),
                ('reference_agent', models.CharField(max_length=50, unique=True)),
                ('num_tel_agent', models.CharField(max_length=20)),
                ('email_agent', models.EmailField(blank=True, max_length=254)),
                ('date_debut_activites', models.DateField(default=django.utils.timezone.now)),
                ('pourcentage_commission', models.DecimalField(decimal_places=2, help_text="Pourcentage de commission pour l'agent", max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('autres_details', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Agent',
                'verbose_name_plural': 'Agents',
            },
        ),
        migrations.CreateModel(
            name='Collecteur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_collecteur', models.CharField(max_length=100)),
                ('prenom_collecteur', models.CharField(max_length=100)),
                ('reference_collecteur', models.CharField(max_length=50, unique=True)),
                ('num_tel_collecteur', models.CharField(max_length=20)),
                ('email_collecteur', models.EmailField(blank=True, max_length=254)),
                ('date_debut_activites', models.DateField(default=django.utils.timezone.now)),
                ('pourcentage_commission', models.DecimalField(decimal_places=2, help_text='Pourcentage de commission pour le collecteur', max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('autres_details', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Collecteur',
                'verbose_name_plural': 'Collecteurs',
            },
        ),
        migrations.CreateModel(
            name='TypeDepense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('libelle', models.CharField(choices=[('salaire', 'Salaire'), ('loyer', 'Loyer'), ('impot', 'Impôt'), ('fourniture', 'Achat Fourniture'), ('autre', 'Autre')], max_length=20)),
                ('details', models.TextField(blank=True)),
                ('autres_details', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Type de dépense',
                'verbose_name_plural': 'Types de dépenses',
            },
        ),
        migrations.CreateModel(
            name='ActiviteCollecteur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pourcentage_commission', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('reference_recu', models.CharField(max_length=100)),
                ('date_activite', models.DateField(default=django.utils.timezone.now)),
                ('montant_activite', models.DecimalField(decimal_places=2, max_digits=15)),
                ('observations', models.TextField(blank=True)),
                ('autres_details', models.TextField(blank=True)),
                ('collecteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activites', to='gestloto.collecteur')),
            ],
            options={
                'verbose_name': 'Activité collecteur',
                'verbose_name_plural': 'Activités collecteurs',
            },
        ),
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_terminal', models.CharField(max_length=50, unique=True)),
                ('nom_point_vente', models.CharField(max_length=100)),
                ('details', models.TextField(blank=True)),
                ('agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='machines', to='gestloto.agent')),
            ],
            options={
                'verbose_name': 'Machine',
                'verbose_name_plural': 'Machines',
            },
        ),
        migrations.CreateModel(
            name='ChiffreAffaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_chiffre_affaire', models.DateField(default=django.utils.timezone.now)),
                ('ventes_totales', models.DecimalField(decimal_places=2, max_digits=15)),
                ('annulations_totales', models.DecimalField(decimal_places=2, max_digits=15)),
                ('paiements_totaux', models.DecimalField(decimal_places=2, max_digits=15)),
                ('solde_total', models.DecimalField(decimal_places=2, max_digits=15)),
                ('pourcentage_commission_potentielle', models.DecimalField(decimal_places=2, help_text='Pourcentage de commission potentielle pour la société', max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('montant_commission', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('jour_tirage', models.IntegerField(help_text='Jour de tirage (de J1 à J365)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(365)])),
                ('observations', models.TextField(blank=True)),
                ('autres_details', models.TextField(blank=True)),
                ('agent_enregistreur', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='chiffres_enregistres', to='gestloto.agent')),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chiffres_affaire', to='gestloto.machine')),
            ],
            options={
                'verbose_name': "Chiffre d'affaire",
                'verbose_name_plural': "Chiffres d'affaire",
            },
        ),
        migrations.CreateModel(
            name='PenaliteCommission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_penalite', models.DateField(blank=True, null=True)),
                ('montant_penalite', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('motif_penalite', models.TextField(blank=True)),
                ('date_commission', models.DateField(blank=True, null=True)),
                ('montant_commission', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('observations', models.TextField(blank=True)),
                ('autres_details', models.TextField(blank=True)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='penalites_commissions', to='gestloto.agent')),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='penalites_commissions', to='gestloto.machine')),
            ],
            options={
                'verbose_name': 'Pénalité et commission',
                'verbose_name_plural': 'Pénalités et commissions',
            },
        ),
        migrations.CreateModel(
            name='Depense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_depense', models.DateField(default=django.utils.timezone.now)),
                ('montant', models.DecimalField(decimal_places=2, max_digits=15)),
                ('reference', models.CharField(max_length=100)),
                ('autres_details', models.TextField(blank=True)),
                ('agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='depenses', to='gestloto.agent')),
                ('type_depense', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='depenses', to='gestloto.typedepense')),
            ],
            options={
                'verbose_name': 'Dépense',
                'verbose_name_plural': 'Dépenses',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Administrateur'), ('user', 'Utilisateur simple')], default='user', max_length=10)),
                ('poste_user', models.CharField(blank=True, max_length=100)),
                ('autres_details', models.TextField(blank=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profil utilisateur',
                'verbose_name_plural': 'Profils utilisateurs',
            },
        ),
    ]
