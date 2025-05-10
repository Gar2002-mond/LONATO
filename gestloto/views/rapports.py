from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from ..models import ChiffreAffaire, Depense, Collecteur, Agent, ActiviteCollecteur, PenaliteCommission, Machine
from ..forms import DateRangeForm
from ..models import ChiffreAffaire, Depense, Collecteur, Agent, ActiviteCollecteur, PenaliteCommission, Machine, TypeDepense
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime 
from openpyxl.utils import get_column_letter
import openpyxl
from openpyxl.styles import Font

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




@login_required
def export_depenses_report_view(request):
    # Récupérer les paramètres de filtrage de la requête GET
    # Ces paramètres sont ceux encodés par {{ request.GET.urlencode }} dans le template
    date_debut_str = request.GET.get('date_debut')
    date_fin_str = request.GET.get('date_fin')
    type_depense_id_str = request.GET.get('type')
    agent_id_str = request.GET.get('agent')
    # Le paramètre 'periode' est implicitement géré si la vue rapport_depense
    # met à jour date_debut et date_fin dans request.GET en fonction de la période.

    # Requête de base pour les dépenses
    queryset = Depense.objects.select_related('type_depense', 'agent').order_by('-date_depense', '-id')

    # Filtrage par date (en supposant que date_debut_str et date_fin_str sont fiables)
    # La vue rapport_depense devrait s'assurer que ces dates sont correctement définies
    # dans request.GET en fonction de la période sélectionnée par l'utilisateur.
    if date_debut_str and date_fin_str:
        try:
            # Valider et convertir les chaînes de date si nécessaire, bien que le SGBD puisse les gérer
            datetime.strptime(date_debut_str, '%Y-%m-%d')
            datetime.strptime(date_fin_str, '%Y-%m-%d')
            queryset = queryset.filter(date_depense__range=[date_debut_str, date_fin_str])
        except ValueError:
            # Gérer les dates invalides si nécessaire, ou laisser le SGBD lever une erreur
            pass 
    elif date_debut_str:
        try:
            datetime.strptime(date_debut_str, '%Y-%m-%d')
            queryset = queryset.filter(date_depense__gte=date_debut_str)
        except ValueError:
            pass
    elif date_fin_str:
        try:
            datetime.strptime(date_fin_str, '%Y-%m-%d')
            queryset = queryset.filter(date_depense__lte=date_fin_str)
        except ValueError:
            pass

    # Filtrage par type de dépense
    if type_depense_id_str:
        try:
            type_depense_id = int(type_depense_id_str)
            if type_depense_id > 0: # S'assurer que ce n'est pas une valeur vide comme "" convertie en 0 par erreur
                 queryset = queryset.filter(type_depense_id=type_depense_id)
        except (ValueError, TypeError):
            pass # ID de type invalide ou non fourni

    # Filtrage par agent
    if agent_id_str:
        try:
            agent_id = int(agent_id_str)
            if agent_id > 0: # S'assurer que ce n'est pas une valeur vide
                queryset = queryset.filter(agent_id=agent_id)
        except (ValueError, TypeError):
            pass # ID d'agent invalide ou non fourni

    # Création du classeur Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename_date = timezone.localdate().strftime("%Y%m%d")
    response['Content-Disposition'] = f'attachment; filename="rapport_depenses_{filename_date}.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Dépenses"

    # Définition des en-têtes
    headers = ["Date", "Type", "Référence", "Description", "Agent concerné", "Montant (FCFA)"]
    ws.append(headers)
    
    # Style pour les en-têtes (optionnel)
    for col_num, header_title in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = openpyxl.styles.Font(bold=True)

    # Remplissage des données
    for depense in queryset:
        agent_details = "-"
        if depense.agent:
            agent_details = f"{depense.agent.nom_agent or ''} {depense.agent.prenom_agent or ''}".strip()
            if not agent_details: agent_details = "-"


        type_display = "-"
        if depense.type_depense:
            if hasattr(depense.type_depense, 'get_libelle_display'):
                type_display = depense.type_depense.get_libelle_display()
            elif hasattr(depense.type_depense, 'libelle'):
                type_display = depense.type_depense.libelle
        
        description = getattr(depense, 'description', '') # Au cas où le champ description n'existe pas

        row_data = [
            depense.date_depense,
            type_display,
            depense.reference or "-",
            description or "-",
            agent_details,
            depense.montant,
        ]
        ws.append(row_data)

    # Ajustement de la largeur des colonnes et formatage des nombres/dates
    for col_idx, header in enumerate(headers, 1):
        column_letter = get_column_letter(col_idx)
        max_length = 0
        # Calculer la longueur maximale du contenu de la colonne
        for cell in ws[column_letter]:
            try:
                if cell.value:
                    cell_length = len(str(cell.value))
                    if isinstance(cell.value, datetime): # Longueur pour format date 'DD/MM/YYYY'
                        cell_length = 10
                    elif isinstance(cell.value, (int, float)) and col_idx == headers.index("Montant (FCFA)") + 1: # Montant
                        cell_length = len(f"{cell.value:,}".split('.')[0]) # Longueur pour format nombre groupé

                    if cell_length > max_length:
                        max_length = cell_length
            except:
                pass
        adjusted_width = (max_length + 2) if max_length > 0 else (len(header) + 2)
        ws.column_dimensions[column_letter].width = min(adjusted_width, 50) # Limiter la largeur maximale

    # Appliquer le format de date et de nombre
    for row_num in range(2, ws.max_row + 1): # Commencer à la ligne 2 (après les en-têtes)
        # Colonne Date (supposons que c'est la première colonne, A)
        date_cell = ws.cell(row=row_num, column=1)
        if isinstance(date_cell.value, (datetime, datetime.date)): # datetime.date est aussi possible
             date_cell.number_format = 'DD/MM/YYYY'

        # Colonne Montant (supposons que c'est la sixième colonne, F)
        amount_cell = ws.cell(row=row_num, column=headers.index("Montant (FCFA)") + 1)
        if isinstance(amount_cell.value, (int, float)):
            amount_cell.number_format = '#,##0' # Pour les nombres sans décimales, ou '#,##0.00' pour deux décimales

    wb.save(response)
    return response





@login_required
def export_collecteurs_report_view(request):
    date_debut_str = request.GET.get('date_debut')
    date_fin_str = request.GET.get('date_fin')
    collecteur_id_str = request.GET.get('collecteur')
    tri = request.GET.get('tri')

    # Requête de base pour les activités des collecteurs
    queryset = ActiviteCollecteur.objects.select_related('collecteur').all()

    # Filtrage par date
    # La vue rapport_collecteur devrait s'assurer que ces dates sont correctement définies
    # dans request.GET en fonction de la période sélectionnée par l'utilisateur.
    if date_debut_str and date_fin_str:
        try:
            datetime.strptime(date_debut_str, '%Y-%m-%d') # Validation du format
            datetime.strptime(date_fin_str, '%Y-%m-%d')   # Validation du format
            queryset = queryset.filter(date_activite__range=[date_debut_str, date_fin_str])
        except ValueError:
            pass # Ignorer les dates invalides ou laisser le SGBD gérer
    elif date_debut_str:
        try:
            datetime.strptime(date_debut_str, '%Y-%m-%d')
            queryset = queryset.filter(date_activite__gte=date_debut_str)
        except ValueError:
            pass
    elif date_fin_str:
        try:
            datetime.strptime(date_fin_str, '%Y-%m-%d')
            queryset = queryset.filter(date_activite__lte=date_fin_str)
        except ValueError:
            pass

    # Filtrage par collecteur spécifique
    if collecteur_id_str:
        try:
            collecteur_id = int(collecteur_id_str)
            if collecteur_id > 0: # S'assurer que ce n'est pas une valeur vide
                queryset = queryset.filter(collecteur_id=collecteur_id)
        except (ValueError, TypeError):
            pass # ID de collecteur invalide ou non fourni

    # Annotation pour la commission calculée (pour le tri et l'affichage)
    # Assure que pourcentage_commission est sur ActiviteCollecteur et est un nombre (pas en %)
    commission_expression = ExpressionWrapper(
        F('montant_activite') * F('pourcentage_commission') / 100,
        output_field=DecimalField(max_digits=15, decimal_places=2)
    )
    queryset = queryset.annotate(calculated_commission=commission_expression)

    # Tri des données
    order_by_fields = ['-date_activite', 'collecteur__nom_collecteur'] # Tri par défaut
    if tri == 'montant':
        order_by_fields = ['-montant_activite', '-date_activite']
    elif tri == 'commission':
        order_by_fields = ['-calculated_commission', '-date_activite']
    # 'activites' est pour un résumé, pour une liste détaillée, le tri par défaut (date) est plus pertinent.
    
    queryset = queryset.order_by(*order_by_fields)

    # Création du classeur Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename_date = timezone.localdate().strftime("%Y%m%d")
    response['Content-Disposition'] = f'attachment; filename="rapport_collecteurs_{filename_date}.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Activités Collecteurs"

    # Définition des en-têtes
    headers = [
        "Date Activité", "Collecteur", "Référence Reçu", 
        "Montant Activité (FCFA)", "% Commission", 
        "Commission Calculée (FCFA)", "Observations"
    ]
    ws.append(headers)

    # Style pour les en-têtes
    for col_num, header_title in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = Font(bold=True)

    # Remplissage des données
    for activite in queryset:
        collecteur_info = "-"
        if activite.collecteur:
            nom = activite.collecteur.nom_collecteur or ""
            prenom = activite.collecteur.prenom_collecteur or ""
            ref = activite.collecteur.reference_collecteur or ""
            collecteur_info = f"{nom} {prenom} ({ref})".strip()
            if collecteur_info == "()": collecteur_info = ref or "-"


        row_data = [
            activite.date_activite,
            collecteur_info,
            activite.reference_recu or "-",
            activite.montant_activite,
            activite.pourcentage_commission, # Affichage direct du pourcentage stocké
            activite.calculated_commission,  # Commission calculée via annotation
            activite.observations or "-",
        ]
        ws.append(row_data)

    # Ajustement de la largeur des colonnes et formatage
    for col_idx, header in enumerate(headers, 1):
        column_letter = get_column_letter(col_idx)
        max_length = len(header) # Commencer avec la longueur de l'en-tête
        for cell_row_idx in range(2, ws.max_row + 1): # Commencer après l'en-tête
            cell_value = ws.cell(row=cell_row_idx, column=col_idx).value
            if cell_value:
                cell_length = len(str(cell_value))
                if isinstance(cell_value, (datetime, datetime.date)):
                    cell_length = 10 # "DD/MM/YYYY"
                elif isinstance(cell_value, (int, float, DecimalField)):
                     # Pour les montants, prendre la longueur du nombre formaté
                    if header == "Montant Activité (FCFA)" or header == "Commission Calculée (FCFA)":
                        cell_length = len(f"{cell_value:,.0f}") # Format avec séparateur de milliers, sans décimales
                    elif header == "% Commission":
                         cell_length = len(f"{cell_value:.2f}%")


                if cell_length > max_length:
                    max_length = cell_length
        
        adjusted_width = (max_length + 2) if max_length > 0 else (len(header) + 2)
        ws.column_dimensions[column_letter].width = min(adjusted_width, 60) # Limiter la largeur

    # Appliquer le format de date et de nombre
    for row_num in range(2, ws.max_row + 1):
        # Date Activité (Colonne 1)
        date_cell = ws.cell(row=row_num, column=1)
        if isinstance(date_cell.value, (datetime, datetime.date)):
            date_cell.number_format = 'DD/MM/YYYY'

        # Montant Activité (Colonne 4)
        montant_cell = ws.cell(row=row_num, column=4)
        if isinstance(montant_cell.value, (int, float, DecimalField)):
            montant_cell.number_format = '#,##0' 

        # % Commission (Colonne 5)
        pourcentage_cell = ws.cell(row=row_num, column=5)
        if isinstance(pourcentage_cell.value, (int, float, DecimalField)):
            pourcentage_cell.number_format = '0.00"%"' # Affiche comme 10.00%

        # Commission Calculée (Colonne 6)
        commission_cell = ws.cell(row=row_num, column=6)
        if isinstance(commission_cell.value, (int, float, DecimalField)):
            commission_cell.number_format = '#,##0'

    wb.save(response)
    return response
