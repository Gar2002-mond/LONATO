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
from openpyxl.styles import Font,Alignment
from django.db.models import Sum, Value, F, CharField, Case, When, IntegerField, DateField, OuterRef, Subquery, Count, Avg, Max, Min, ExpressionWrapper, fields
from django.db.models.functions import Coalesce, TruncMonth, TruncDay, Cast, ExtractYear, ExtractMonth, ExtractDay
from decimal import Decimal # S'assurer que Decimal est importé
from ..models import Agent, ChiffreAffaire, Depense, Collecteur, ActiviteCollecteur, Machine, PenaliteCommission

def _format_excel_sheet(ws, headers, header_row=1, data_start_row=2, column_widths=None, 
                        date_column_indices=None, currency_column_indices=None, 
                        number_column_indices=None, percentage_column_indices=None, 
                        bold_header=True, wrap_text_header=False,
                        title_text=None, filter_texts=None):
    """
    Applique le formatage à une feuille Excel, avec option pour titre et filtres.
    - title_text: Texte du titre à afficher avant les en-têtes.
    - filter_texts: Liste de chaînes de filtres à afficher après le titre.
    """
    current_row = 1
    if title_text:
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(headers))
        title_cell = ws.cell(row=current_row, column=1, value=title_text)
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal='center')
        current_row += 1
    
    if filter_texts:
        for f_text in filter_texts:
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(headers))
            filter_cell = ws.cell(row=current_row, column=1, value=f_text)
            filter_cell.font = Font(italic=True)
            filter_cell.alignment = Alignment(horizontal='center')
            current_row += 1
    
    # Ajuster header_row et data_start_row si des titres/filtres ont été ajoutés
    if current_row > 1: # Si on a ajouté des lignes de titre/filtre
        header_row = current_row
        data_start_row = header_row + 1

    # Écrire les en-têtes à la bonne ligne
    for col_num, header_title in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num, value=header_title)
        if bold_header:
            cell.font = Font(bold=True)
        if wrap_text_header:
            cell.alignment = Alignment(wrap_text=True, vertical='top')


    if date_column_indices is None: date_column_indices = []
    if currency_column_indices is None: currency_column_indices = []
    if number_column_indices is None: number_column_indices = []
    if percentage_column_indices is None: percentage_column_indices = []

    for col_idx, header in enumerate(headers, 1):
        column_letter = get_column_letter(col_idx)
        if column_widths and col_idx <= len(column_widths) and column_widths[col_idx-1] is not None:
            ws.column_dimensions[column_letter].width = column_widths[col_idx-1]
        else:
            max_length = len(str(ws.cell(row=header_row, column=col_idx).value or "")) # Longueur de l'en-tête
            for row_idx_iter in range(data_start_row, ws.max_row + 1):
                cell_value = ws.cell(row=row_idx_iter, column=col_idx).value
                if cell_value is not None:
                    if isinstance(cell_value, datetime): cell_length = 10 # 'DD/MM/YYYY'
                    elif isinstance(cell_value, (int, float, Decimal)):
                        if col_idx in currency_column_indices: cell_length = len(f"{cell_value:,.0f} FCFA")
                        elif col_idx in percentage_column_indices: cell_length = len(f"{cell_value:.2f}%")
                        else: cell_length = len(f"{cell_value:,.0f}")
                    else: cell_length = len(str(cell_value))
                    
                    if cell_length > max_length: max_length = cell_length
            adjusted_width = (max_length + 2) if max_length > 0 else (len(str(header)) + 2)
            ws.column_dimensions[column_letter].width = min(adjusted_width, 50)

    for row_num in range(data_start_row, ws.max_row + 1):
        for col_idx in date_column_indices:
            cell = ws.cell(row=row_num, column=col_idx)
            if isinstance(cell.value, (datetime, datetime.date)):
                cell.number_format = 'DD/MM/YYYY'
        for col_idx in currency_column_indices:
            cell = ws.cell(row=row_num, column=col_idx)
            if isinstance(cell.value, (int, float, Decimal)):
                cell.number_format = '#,##0 "FCFA"'
        for col_idx in number_column_indices:
            if col_idx not in currency_column_indices:
                cell = ws.cell(row=row_num, column=col_idx)
                if isinstance(cell.value, (int, float, Decimal)): cell.number_format = '#,##0'
        for col_idx in percentage_column_indices:
            cell = ws.cell(row=row_num, column=col_idx)
            if isinstance(cell.value, (int, float, Decimal)): cell.number_format = '0.00"%"'

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





@login_required
def export_agents_report_view(request):
    # --- Helper function for Excel sheet styling ---
    def _format_excel_sheet(ws, headers, numeric_columns_indices=None, date_column_indices=None, currency_columns_indices=None):
        """
        Applies bold font to headers, adjusts column widths, and formats numbers/dates.
        numeric_columns_indices: list of 1-based indices for general numeric formatting.
        date_column_indices: list of 1-based indices for date formatting 'DD/MM/YYYY'.
        currency_columns_indices: list of 1-based indices for currency formatting '#,##0 FCFA'.
        """
        if numeric_columns_indices is None: numeric_columns_indices = []
        if date_column_indices is None: date_column_indices = []
        if currency_columns_indices is None: currency_columns_indices = []

        header_font = Font(bold=True)
        for col_num, header_title in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font

        for col_idx, header in enumerate(headers, 1):
            column_letter = get_column_letter(col_idx)
            max_length = len(str(header))  # Start with header length
            for row_idx in range(2, ws.max_row + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell_value = cell.value
                if cell_value is not None:
                    if isinstance(cell_value, (datetime, datetime.date)):
                        cell_length = 10  # For 'DD/MM/YYYY'
                    elif isinstance(cell_value, (int, float, Decimal)):
                        if col_idx in currency_columns_indices or col_idx in numeric_columns_indices:
                             # Consider space for thousands separators and " FCFA"
                            cell_length = len(f"{cell_value:,.0f}") + (5 if col_idx in currency_columns_indices else 0)
                        else:
                            cell_length = len(str(cell_value))
                    else:
                        cell_length = len(str(cell_value))
                    
                    if cell_length > max_length:
                        max_length = cell_length
            
            adjusted_width = (max_length + 2) if max_length > 0 else (len(str(header)) + 2)
            ws.column_dimensions[column_letter].width = min(adjusted_width, 60)

        for row_num in range(2, ws.max_row + 1):
            for col_idx in currency_columns_indices:
                cell = ws.cell(row=row_num, column=col_idx)
                if isinstance(cell.value, (int, float, Decimal)):
                    cell.number_format = '#,##0" FCFA"'
            for col_idx in numeric_columns_indices:
                 if col_idx not in currency_columns_indices: # Avoid double formatting
                    cell = ws.cell(row=row_num, column=col_idx)
                    if isinstance(cell.value, (int, float, Decimal)):
                        cell.number_format = '#,##0'
            for col_idx in date_column_indices:
                cell = ws.cell(row=row_num, column=col_idx)
                if isinstance(cell.value, (datetime, datetime.date)):
                    cell.number_format = 'DD/MM/YYYY'

    # 1. Get and parse filters
    date_debut_str = request.GET.get('date_debut')
    date_fin_str = request.GET.get('date_fin')
    agent_id_str = request.GET.get('agent')
    tri = request.GET.get('tri')

    # Default and parse dates
    try:
        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date() if date_debut_str else (timezone.now() - timedelta(days=30)).date()
    except ValueError:
        date_debut = (timezone.now() - timedelta(days=30)).date()

    try:
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date() if date_fin_str else timezone.now().date()
    except ValueError:
        date_fin = timezone.now().date()

    # 2. Base Queryset for Agents
    agents_queryset = Agent.objects.all()
    specific_agent_requested = False
    parsed_agent_id = None
    if agent_id_str:
        try:
            parsed_agent_id = int(agent_id_str)
            if parsed_agent_id > 0:
                agents_queryset = agents_queryset.filter(id=parsed_agent_id)
                specific_agent_requested = True
        except (ValueError, TypeError):
            pass # Invalid agent_id, report all agents

    # 3. Annotate agents with financial data
    decimal_field_params = {'max_digits': 15, 'decimal_places': 2}
    
    ca_subquery = ChiffreAffaire.objects.filter(
        agent_enregistreur=OuterRef('pk'),
        date_chiffre_affaire__gte=date_debut,
        date_chiffre_affaire__lte=date_fin
    ).values('agent_enregistreur').annotate(total_ca=Sum('solde_total')).values('total_ca')

    commissions_subquery = PenaliteCommission.objects.filter(
        agent=OuterRef('pk'),
        montant_commission__gt=Decimal('0') # Condition pour identifier une commission
    ).values('agent').annotate(total_comm=Sum('montant_commission')).values('total_comm')

    penalites_subquery = PenaliteCommission.objects.filter(
        agent=OuterRef('pk'),
        montant_penalite__gt=Decimal('0') # Condition pour identifier une pénalité
    ).values('agent').annotate(total_pen=Sum('montant_penalite')).values('total_pen')

    agents_data = agents_queryset.annotate(
        chiffre_affaires=Coalesce(Subquery(ca_subquery, output_field=DecimalField(**decimal_field_params)), Value(Decimal('0.00'), output_field=DecimalField(**decimal_field_params))),
        commissions_gains=Coalesce(Subquery(commissions_subquery, output_field=DecimalField(**decimal_field_params)), Value(Decimal('0.00'), output_field=DecimalField(**decimal_field_params))),
        penalites_pertes=Coalesce(Subquery(penalites_subquery, output_field=DecimalField(**decimal_field_params)), Value(Decimal('0.00'), output_field=DecimalField(**decimal_field_params))),
    ).annotate(
        balance=F('chiffre_affaires') + F('commissions_gains') - F('penalites_pertes')
    )

    # 4. Sorting
    if tri == 'nom_asc' or tri == 'nom' or not tri:
        agents_data = agents_data.order_by('nom_agent', 'prenom_agent')
    elif tri == 'nom_desc':
        agents_data = agents_data.order_by('-nom_agent', '-prenom_agent')
    elif tri == 'ca':
        agents_data = agents_data.order_by(F('chiffre_affaires').desc(nulls_last=True), 'nom_agent', 'prenom_agent')
    elif tri == 'commission':
        agents_data = agents_data.order_by(F('commissions_gains').desc(nulls_last=True), 'nom_agent', 'prenom_agent')
    elif tri == 'penalite':
        agents_data = agents_data.order_by(F('penalites_pertes').desc(nulls_last=True), 'nom_agent', 'prenom_agent')
    elif tri == 'balance':
        agents_data = agents_data.order_by(F('balance').desc(nulls_last=True), 'nom_agent', 'prenom_agent')
    else: 
        agents_data = agents_data.order_by('nom_agent', 'prenom_agent')

    # 5. Create Excel Workbook
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename_date = timezone.localdate().strftime("%Y%m%d")
    response['Content-Disposition'] = f'attachment; filename="rapport_agents_{filename_date}.xlsx"'
    wb = openpyxl.Workbook()

    # 6. Summary Sheet
    ws_summary = wb.active
    ws_summary.title = "Résumé Agents"
    headers_summary = ["Réf. Agent", "Nom", "Prénom", "Chiffre d'Affaires", "Commissions Reçues", "Pénalités Subies", "Balance Nette"]
    ws_summary.append(headers_summary)

    for agent in agents_data:
        ws_summary.append([
            agent.reference_agent,
            agent.nom_agent,
            agent.prenom_agent,
            agent.chiffre_affaires,
            agent.commissions_gains,
            agent.penalites_pertes,
            agent.balance,
        ])
    _format_excel_sheet(ws_summary, headers_summary, currency_columns_indices=[4, 5, 6, 7])

    # 7. Detailed Sheets (if a single agent was specifically requested and found)
    is_single_agent_report = specific_agent_requested and parsed_agent_id is not None and agents_data.count() == 1
    
    if is_single_agent_report:
        agent_obj = Agent.objects.get(id=parsed_agent_id)

        # Sheet: CA Details
        ws_ca_details = wb.create_sheet(title="Détails CA")
        headers_ca = ["Date", "Machine", "Ventes Brutes", "Annulations", "Paiements", "Solde (CA)"]
        ws_ca_details.append(headers_ca)
        ca_details_qs = ChiffreAffaire.objects.filter(
            agent_enregistreur=agent_obj, 
            date_chiffre_affaire__gte=date_debut, 
            date_chiffre_affaire__lte=date_fin
        ).select_related('machine').order_by('-date_chiffre_affaire')
        for ca_entry in ca_details_qs:
            ws_ca_details.append([
                ca_entry.date_chiffre_affaire,
                ca_entry.machine.numero_terminal if ca_entry.machine else "-",
                ca_entry.ventes_totales,
                ca_entry.annulations_totales,
                ca_entry.paiements_totaux,
                ca_entry.solde_total,
            ])
        _format_excel_sheet(ws_ca_details, headers_ca, date_column_indices=[1], currency_columns_indices=[3, 4, 5, 6])

        # Sheet: Commissions Details
        ws_comm_details = wb.create_sheet(title="Détails Commissions")
        headers_comm = ["Date", "Motif", "Montant Commission"]
        ws_comm_details.append(headers_comm)
        comm_details_qs = PenaliteCommission.objects.filter(
            agent=agent_obj, montant_commission__gt=Decimal('0'),
            date_commission__gte=date_debut, date_commission__lte=date_fin
        ).order_by('-date_commission')
        for comm_entry in comm_details_qs:
            ws_comm_details.append([
                comm_entry.date_commission,
                comm_entry.motif or "-",
                comm_entry.montant_commission,
            ])
        _format_excel_sheet(ws_comm_details, headers_comm, date_column_indices=[1], currency_columns_indices=[3])

        # Sheet: Pénalités Details
        ws_pen_details = wb.create_sheet(title="Détails Pénalités")
        headers_pen = ["Date", "Motif", "Montant Pénalité"]
        ws_pen_details.append(headers_pen)
        pen_details_qs = PenaliteCommission.objects.filter(
            agent=agent_obj, montant_penalite__gt=Decimal('0'),
            date_penalite__gte=date_debut, date_penalite__lte=date_fin
        ).order_by('-date_penalite')
        for pen_entry in pen_details_qs:
            ws_pen_details.append([
                pen_entry.date_penalite,
                pen_entry.motif or "-",
                pen_entry.montant_penalite,
            ])
        _format_excel_sheet(ws_pen_details, headers_pen, date_column_indices=[1], currency_columns_indices=[3])
        
        # Sheet: Bilan Mensuel
        ws_monthly = wb.create_sheet(title="Bilan Mensuel")
        headers_monthly = ["Mois (AAAA-MM)", "Total CA", "Total Commissions", "Total Pénalités", "Balance Mensuelle"]
        ws_monthly.append(headers_monthly)

        monthly_summary_data = {}
        # CA Mensuel
        ca_mensuel = ChiffreAffaire.objects.filter(
            agent_enregistreur=agent_obj, date_chiffre_affaire__gte=date_debut, date_chiffre_affaire__lte=date_fin
        ).annotate(mois=TruncMonth('date_chiffre_affaire')).values('mois').annotate(total_ca=Sum('solde_total')).order_by('mois')
        for item in ca_mensuel:
            mois_key = item['mois'].strftime('%Y-%m')
            if mois_key not in monthly_summary_data: monthly_summary_data[mois_key] = {'ca': Decimal(0), 'comm': Decimal(0), 'pen': Decimal(0)}
            monthly_summary_data[mois_key]['ca'] += item['total_ca'] or Decimal(0)

        # Commissions Mensuelles
        comm_mensuel = PenaliteCommission.objects.filter(
            agent=agent_obj, montant_commission__gt=Decimal('0'),
            date_commission__gte=date_debut, date_commission__lte=date_fin
        ).annotate(mois=TruncMonth('date_commission')).values('mois').annotate(total_comm=Sum('montant_commission')).order_by('mois')
        for item in comm_mensuel:
            mois_key = item['mois'].strftime('%Y-%m')
            if mois_key not in monthly_summary_data: monthly_summary_data[mois_key] = {'ca': Decimal(0), 'comm': Decimal(0), 'pen': Decimal(0)}
            monthly_summary_data[mois_key]['comm'] += item['total_comm'] or Decimal(0)

        # Pénalités Mensuelles
        pen_mensuel = PenaliteCommission.objects.filter(
            agent=agent_obj, montant_penalite__gt=Decimal('0'),
            date_penalite__gte=date_debut, date_penalite__lte=date_fin
        ).annotate(mois=TruncMonth('date_penalite')).values('mois').annotate(total_pen=Sum('montant_penalite')).order_by('mois')
        for item in pen_mensuel:
            mois_key = item['mois'].strftime('%Y-%m')
            if mois_key not in monthly_summary_data: monthly_summary_data[mois_key] = {'ca': Decimal(0), 'comm': Decimal(0), 'pen': Decimal(0)}
            monthly_summary_data[mois_key]['pen'] += item['total_pen'] or Decimal(0)
            
        for mois_key in sorted(monthly_summary_data.keys()):
            data = monthly_summary_data[mois_key]
            balance_mois = data['ca'] + data['comm'] - data['pen']
            ws_monthly.append([mois_key, data['ca'], data['comm'], data['pen'], balance_mois])
        _format_excel_sheet(ws_monthly, headers_monthly, currency_columns_indices=[2, 3, 4, 5])


    # 8. Save workbook and return response
    wb.save(response)
    return response


@login_required
def export_ca_report_view(request):
    # 1. Récupération et analyse des filtres
    date_debut_str = request.GET.get('date_debut')
    date_fin_str = request.GET.get('date_fin')
    agent_id_str = request.GET.get('agent')
    machine_id_str = request.GET.get('machine')
    groupby = request.GET.get('groupby', 'jour') # défaut 'jour'

    # Dates par défaut et parsing
    try:
        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date() if date_debut_str else (timezone.now() - timedelta(days=30)).date()
    except ValueError:
        date_debut = (timezone.now() - timedelta(days=30)).date()
    try:
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date() if date_fin_str else timezone.now().date()
    except ValueError:
        date_fin = timezone.now().date()

    # Construction des filtres pour le titre du rapport
    filter_display_texts = [f"Période : du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}"]
    
    # 2. Requête de base ChiffreAffaire
    ca_queryset = ChiffreAffaire.objects.filter(date_chiffre_affaire__range=[date_debut, date_fin])

    if agent_id_str and agent_id_str != "0" and agent_id_str.isdigit():
        ca_queryset = ca_queryset.filter(agent_enregistreur_id=int(agent_id_str))
        try:
            agent_obj = Agent.objects.get(id=int(agent_id_str))
            filter_display_texts.append(f"Agent : {agent_obj.nom_agent} {agent_obj.prenom_agent}")
        except Agent.DoesNotExist:
            filter_display_texts.append(f"Agent ID : {agent_id_str} (non trouvé)")
            
    if machine_id_str and machine_id_str != "0" and machine_id_str.isdigit():
        ca_queryset = ca_queryset.filter(machine_id=int(machine_id_str))
        try:
            machine_obj = Machine.objects.get(id=int(machine_id_str))
            filter_display_texts.append(f"Machine : {machine_obj.numero_terminal} ({machine_obj.nom_point_vente})")
        except Machine.DoesNotExist:
            filter_display_texts.append(f"Machine ID : {machine_id_str} (non trouvée)")


    # Création du classeur Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename_date = timezone.localdate().strftime("%Y%m%d")
    response['Content-Disposition'] = f'attachment; filename="rapport_chiffre_affaires_{filename_date}.xlsx"'
    wb = openpyxl.Workbook()

    # Champs d'agrégation communs
    aggregations = {
        'total_ventes': Coalesce(Sum('ventes_totales'), Decimal('0.00'), output_field=DecimalField(max_digits=15, decimal_places=2)),
        'total_annulations': Coalesce(Sum('annulations_totales'), Decimal('0.00'), output_field=DecimalField(max_digits=15, decimal_places=2)),
        'total_paiements': Coalesce(Sum('paiements_totaux'), Decimal('0.00'), output_field=DecimalField(max_digits=15, decimal_places=2)),
        'total_solde': Coalesce(Sum('solde_total'), Decimal('0.00'), output_field=DecimalField(max_digits=15, decimal_places=2)),
        'total_commission': Coalesce(Sum('montant_commission'), Decimal('0.00'), output_field=DecimalField(max_digits=15, decimal_places=2)),
        'nombre_enregistrements': Count('id')
    }

    # --- Feuille 1: Résumé CA ---
    ws_summary = wb.active
    ws_summary.title = "Résumé CA"
    summary_data = ca_queryset.aggregate(**aggregations)
    
    summary_headers = ["Indicateur", "Valeur"]
    _format_excel_sheet(ws_summary, summary_headers, title_text="Résumé du Chiffre d'Affaires", filter_texts=filter_display_texts, column_widths=[30, 20])
    header_row_summary = ws_summary._current_row # Ligne après les titres/filtres + 1 pour les données
    
    ws_summary.append(["Total Ventes Brutes", summary_data['total_ventes']])
    ws_summary.append(["Total Annulations", summary_data['total_annulations']])
    ws_summary.append(["Total Paiements", summary_data['total_paiements']])
    ws_summary.append(["Solde Net Total", summary_data['total_solde']])
    ws_summary.append(["Total Commissions", summary_data['total_commission']])
    ws_summary.append(["Nombre d'enregistrements", summary_data['nombre_enregistrements']])
    
    # Formatage spécifique pour la feuille de résumé (les valeurs sont en colonne 2)
    for row_num in range(header_row_summary, ws_summary.max_row + 1):
        cell = ws_summary.cell(row=row_num, column=2)
        if isinstance(cell.value, (Decimal, float, int)):
            if ws_summary.cell(row=row_num, column=1).value == "Nombre d'enregistrements":
                cell.number_format = '#,##0'
            else:
                cell.number_format = '#,##0 "FCFA"'


    # --- Feuille 2: Détail CA groupé ---
    ws_detail = wb.create_sheet(title=f"Détail CA par {groupby.capitalize()}")
    detail_headers = []
    detail_data = []
    date_cols_detail, currency_cols_detail, num_cols_detail = [], [], []

    group_by_title_text = f"Détail du Chiffre d'Affaires groupé par {groupby.capitalize()}"

    if groupby == 'jour':
        detail_headers = ["Date", "Ventes", "Annulations", "Paiements", "Solde Net", "Commission", "Nb Enreg."]
        date_cols_detail = [1]
        currency_cols_detail = [2, 3, 4, 5, 6]
        num_cols_detail = [7]
        detail_data = ca_queryset.annotate(group_field=TruncDay('date_chiffre_affaire')) \
            .values('group_field').annotate(**aggregations).order_by('group_field')
        for row in detail_data: ws_detail.append([row['group_field'], row['total_ventes'], row['total_annulations'], row['total_paiements'], row['total_solde'], row['total_commission'], row['nombre_enregistrements']])

    elif groupby == 'semaine': # Simplifié: Année-Semaine
        detail_headers = ["Année", "Semaine", "Ventes", "Annulations", "Paiements", "Solde Net", "Commission", "Nb Enreg."]
        currency_cols_detail = [3, 4, 5, 6, 7]
        num_cols_detail = [1, 2, 8]
        # Note: Django's ExtractWeek might behave differently across database backends or might not be available.
        # Consider using TruncWeek if available and suitable, or custom logic for week calculation.
        # For simplicity, assuming ExtractWeek works as intended here.
        from django.db.models.functions import ExtractWeek # Ensure ExtractWeek is imported if used
        detail_data = ca_queryset.annotate(year=ExtractYear('date_chiffre_affaire'), week=ExtractWeek('date_chiffre_affaire')) \
            .values('year', 'week').annotate(**aggregations).order_by('year', 'week')
        for row in detail_data: ws_detail.append([row['year'], row['week'], row['total_ventes'], row['total_annulations'], row['total_paiements'], row['total_solde'], row['total_commission'], row['nombre_enregistrements']])
            
    elif groupby == 'mois':
        detail_headers = ["Mois", "Ventes", "Annulations", "Paiements", "Solde Net", "Commission", "Nb Enreg."]
        date_cols_detail = [1] # TruncMonth retourne une date
        currency_cols_detail = [2, 3, 4, 5, 6]
        num_cols_detail = [7]
        detail_data = ca_queryset.annotate(group_field=TruncMonth('date_chiffre_affaire')) \
            .values('group_field').annotate(**aggregations).order_by('group_field')
        for row in detail_data: ws_detail.append([row['group_field'], row['total_ventes'], row['total_annulations'], row['total_paiements'], row['total_solde'], row['total_commission'], row['nombre_enregistrements']])

    elif groupby == 'agent':
        detail_headers = ["Agent (Réf)", "Nom", "Prénom", "Ventes", "Annulations", "Paiements", "Solde Net", "Commission", "Nb Enreg."]
        currency_cols_detail = [4, 5, 6, 7, 8]
        num_cols_detail = [9]
        detail_data = ca_queryset.values('agent_enregistreur__reference_agent', 'agent_enregistreur__nom_agent', 'agent_enregistreur__prenom_agent') \
            .annotate(**aggregations).order_by('agent_enregistreur__nom_agent', 'agent_enregistreur__prenom_agent')
        for row in detail_data: ws_detail.append([row['agent_enregistreur__reference_agent'], row['agent_enregistreur__nom_agent'], row['agent_enregistreur__prenom_agent'], row['total_ventes'], row['total_annulations'], row['total_paiements'], row['total_solde'], row['total_commission'], row['nombre_enregistrements']])
            
    elif groupby == 'machine':
        detail_headers = ["Machine (N°)", "Point de Vente", "Ventes", "Annulations", "Paiements", "Solde Net", "Commission", "Nb Enreg."]
        currency_cols_detail = [3, 4, 5, 6, 7]
        num_cols_detail = [8]
        detail_data = ca_queryset.values('machine__numero_terminal', 'machine__nom_point_vente') \
            .annotate(**aggregations).order_by('machine__numero_terminal')
        for row in detail_data: ws_detail.append([row['machine__numero_terminal'], row['machine__nom_point_vente'], row['total_ventes'], row['total_annulations'], row['total_paiements'], row['total_solde'], row['total_commission'], row['nombre_enregistrements']])

    _format_excel_sheet(ws_detail, detail_headers, title_text=group_by_title_text, filter_texts=filter_display_texts,
                        date_column_indices=date_cols_detail, currency_column_indices=currency_cols_detail, number_column_indices=num_cols_detail, wrap_text_header=True)


    # --- Feuille 3: Top 5 Machines (par Solde Net) ---
    ws_top_machines = wb.create_sheet(title="Top 5 Machines")
    top_machines_headers = ["Machine (N°)", "Point de Vente", "Solde Net Total"]
    currency_cols_top_machines = [3]
    
    top_machines_data = ChiffreAffaire.objects.filter(date_chiffre_affaire__range=[date_debut, date_fin]) \
        .values('machine__numero_terminal', 'machine__nom_point_vente') \
        .annotate(total_solde_agg=Coalesce(Sum('solde_total'), Decimal('0.00'))) \
        .order_by('-total_solde_agg')[:5]
    
    for row in top_machines_data: ws_top_machines.append([row['machine__numero_terminal'], row['machine__nom_point_vente'], row['total_solde_agg']])
    _format_excel_sheet(ws_top_machines, top_machines_headers, title_text="Top 5 Machines par Solde Net", filter_texts=filter_display_texts,
                        currency_column_indices=currency_cols_top_machines, wrap_text_header=True)

    # --- Feuille 4: Top 5 Agents (par Solde Net généré) ---
    ws_top_agents = wb.create_sheet(title="Top 5 Agents")
    top_agents_headers = ["Agent (Réf)", "Nom", "Prénom", "Solde Net Total"]
    currency_cols_top_agents = [4]

    top_agents_data = ChiffreAffaire.objects.filter(date_chiffre_affaire__range=[date_debut, date_fin]) \
        .values('agent_enregistreur__reference_agent', 'agent_enregistreur__nom_agent', 'agent_enregistreur__prenom_agent') \
        .annotate(total_solde_agg=Coalesce(Sum('solde_total'), Decimal('0.00'))) \
        .order_by('-total_solde_agg')[:5]

    for row in top_agents_data: ws_top_agents.append([row['agent_enregistreur__reference_agent'], row['agent_enregistreur__nom_agent'], row['agent_enregistreur__prenom_agent'], row['total_solde_agg']])
    _format_excel_sheet(ws_top_agents, top_agents_headers, title_text="Top 5 Agents par Solde Net Généré", filter_texts=filter_display_texts,
                        currency_column_indices=currency_cols_top_agents, wrap_text_header=True)

    wb.save(response)
    return response