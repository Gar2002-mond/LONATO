// Scripts pour le projet LONATO

document.addEventListener('DOMContentLoaded', function() {
    // Formatage de la date actuelle
    const currentDateElements = document.querySelectorAll('.current-date');
    if (currentDateElements.length > 0) {
        const now = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const formattedDate = now.toLocaleDateString('fr-FR', options);
        
        currentDateElements.forEach(el => {
            el.textContent = formattedDate;
        });
    }

    // Animation de disparition pour les alertes
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => alert.style.display = 'none', 500);
        });
    }, 5000);

    // Fonctionnalité HTMX pour les modals
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        if (evt.detail.target.id === 'modal') {
            const modal = document.querySelector('.modal');
            if (modal) modal.classList.add('modal-open');
        }
    });

    // Fermeture des modals
    document.body.addEventListener('click', function(evt) {
        if (evt.target.matches('.modal-close')) {
            evt.target.closest('.modal').classList.remove('modal-open');
        }
    });
});