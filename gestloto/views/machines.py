from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, Q
from django.core.paginator import Paginator
from ..models import Agent, Machine, ChiffreAffaire
from ..forms import MachineForm

@login_required
def machine_list(request):
    machines = Machine.objects.all()
    agents = Agent.objects.all()
    
    # Filtrage par recherche
    q = request.GET.get('q')
    if q:
        machines = machines.filter(
            Q(numero_terminal__icontains=q) | 
            Q(nom_point_vente__icontains=q)
        )
    
    # Filtrage par agent
    agent_id = request.GET.get('agent')
    if agent_id:
        machines = machines.filter(agent_id=agent_id)
    
    # Pagination
    paginator = Paginator(machines, 12)  # 12 machines par page
    page_number = request.GET.get('page')
    machines = paginator.get_page(page_number)
    
    # Statistiques améliorées
    machines_assignees = Machine.objects.filter(agent__isnull=False).count()
    ca_stats = ChiffreAffaire.objects.aggregate(
        ca_moyen=Avg('ventes_totales')
    )
    ca_moyen = ca_stats['ca_moyen'] or 0
    
    context = {
        'machines': machines,
        'agents': agents,
        'machines_assignees': machines_assignees,
        'ca_moyen': int(ca_moyen),
    }
    
    # Si c'est une requête HTMX, on retourne seulement le contenu partiel
    if request.headers.get('HX-Request'):
        return render(request, 'gestloto/machines/machine_content.html', context)
    
    # Sinon, on retourne la page complète
    return render(request, 'gestloto/machines/list.html', context)

@login_required
def machine_detail(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    chiffres_affaires = ChiffreAffaire.objects.filter(machine=machine).order_by('-date_chiffre_affaire')[:15]
    
    # Statistiques de la machine
    stats = ChiffreAffaire.objects.filter(machine=machine).aggregate(
        total_ventes=Sum('ventes_totales'),
        total_solde=Sum('solde_total'),
        total_commission=Sum('montant_commission'),
        moyenne_solde=Avg('solde_total')
    )
    
    context = {
        'machine': machine,
        'chiffres_affaires': chiffres_affaires,
        'stats': stats,
    }
    return render(request, 'gestloto/machines/detail.html', context)

@login_required
def machine_create(request):
    if request.method == 'POST':
        form = MachineForm(request.POST)
        if form.is_valid():
            machine = form.save()
            messages.success(request, f"La machine {machine.numero_terminal} a été créée avec succès.")
            return redirect('machine_list')
    else:
        form = MachineForm()
    
    return render(request, 'gestloto/machines/form.html', {'form': form, 'title': 'Ajouter une machine'})

@login_required
def machine_update(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    if request.method == 'POST':
        form = MachineForm(request.POST, instance=machine)
        if form.is_valid():
            form.save()
            messages.success(request, f"La machine {machine.numero_terminal} a été modifiée avec succès.")
            return redirect('machine_detail', pk=machine.pk)
    else:
        form = MachineForm(instance=machine)
    
    return render(request, 'gestloto/machines/form.html', {'form': form, 'machine': machine, 'title': 'Modifier une machine'})

@login_required
def machine_delete(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    if request.method == 'POST':
        numero = machine.numero_terminal
        machine.delete()
        messages.success(request, f"La machine {numero} a été supprimée.")
        return redirect('machine_list')
    
    return render(request, 'gestloto/machines/delete.html', {'machine': machine})

def get_machine_info_view(request):
    machine_id = request.GET.get('machine') # 'machine' est le nom de votre select
    if not machine_id:
        # Retourne un fragment vide ou un message si aucun ID n'est fourni
        return render(request, 'gestloto/chiffres_affaire/partials/machine_info_empty.html')

    try:
        machine = Machine.objects.select_related('agent').get(id=machine_id)
    except Machine.DoesNotExist:
        # Retourne un fragment vide ou un message d'erreur
        return render(request, 'gestloto/chiffres_affaire/partials/machine_info_empty.html', {'error': 'Machine non trouvée'})
    except ValueError:
         return render(request, 'gestloto/chiffres_affaire/partials/machine_info_empty.html', {'error': 'ID Machine invalide'})


    # Vous pouvez passer la machine à un template partiel pour rendre le HTML
    return render(request, 'gestloto/chiffres_affaire/partials/machine_info_content.html', {'machine': machine})