// JavaScript principal pour MovieRec

// Utilitaires
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Configuration CSRF pour les requêtes AJAX
function setupCSRF() {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
        // Configuration pour fetch
        window.defaultFetchOptions = {
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            }
        };
    }
}

// Gestion des boutons de watchlist
function setupWatchlistButtons() {
    const watchlistButtons = document.querySelectorAll('.watchlist-btn');
    
    watchlistButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const movieId = this.dataset.movieId;
            if (!movieId) return;
            
            // Afficher le loading
            const originalContent = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            this.disabled = true;
            
            fetch(`/movies/movies/${movieId}/watchlist/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Mettre à jour l'interface
                    if (data.in_watchlist) {
                        this.innerHTML = '<i class="fas fa-bookmark"></i>';
                        this.classList.add('btn-warning');
                        this.classList.remove('btn-outline-light');
                        this.title = 'Retirer de ma liste';
                    } else {
                        this.innerHTML = '<i class="fas fa-bookmark"></i>';
                        this.classList.add('btn-outline-light');
                        this.classList.remove('btn-warning');
                        this.title = 'Ajouter à ma liste';
                    }
                    
                    // Notification toast
                    showToast(
                        data.in_watchlist ? 'Film ajouté à votre liste' : 'Film retiré de votre liste',
                        'success'
                    );
                } else {
                    this.innerHTML = originalContent;
                    showToast('Erreur lors de l\'opération', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.innerHTML = originalContent;
                showToast('Erreur lors de l\'opération', 'error');
            })
            .finally(() => {
                this.disabled = false;
            });
        });
    });
}

// Gestion des étoiles de notation
function setupRatingStars() {
    const ratingContainers = document.querySelectorAll('.rating-input');
    
    ratingContainers.forEach(container => {
        const stars = container.querySelectorAll('.star');
        const input = container.querySelector('input[type="hidden"]');
        
        stars.forEach((star, index) => {
            star.addEventListener('click', function() {
                const rating = index + 1;
                if (input) input.value = rating;
                updateStarDisplay(container, rating);
            });
            
            star.addEventListener('mouseenter', function() {
                updateStarDisplay(container, index + 1);
            });
        });
        
        container.addEventListener('mouseleave', function() {
            const currentRating = input ? parseInt(input.value) || 0 : 0;
            updateStarDisplay(container, currentRating);
        });
    });
}

function updateStarDisplay(container, rating) {
    const stars = container.querySelectorAll('.star i');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.className = 'fas fa-star text-warning';
        } else {
            star.className = 'far fa-star text-muted';
        }
    });
}

// Système de notifications toast
function showToast(message, type = 'info') {
    // Créer le conteneur de toasts s'il n'existe pas
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 350px;
        `;
        document.body.appendChild(toastContainer);
    }
    
    // Créer le toast
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    toast.style.cssText = `
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-radius: 8px;
    `;
    
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Supprimer automatiquement après 5 secondes
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

// Recherche en temps réel
function setupLiveSearch() {
    const searchInput = document.querySelector('input[name="q"]');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        
        searchTimeout = setTimeout(() => {
            const query = this.value.trim();
            if (query.length >= 2) {
                // Ici, on pourrait implémenter une recherche AJAX en temps réel
                console.log('Recherche:', query);
            }
        }, 300);
    });
}

// Lazy Loading pour les images
function setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Gestion des formulaires de filtrage
function setupFilterForms() {
    const filterForms = document.querySelectorAll('form[method="get"]');
    
    filterForms.forEach(form => {
        const selects = form.querySelectorAll('select');
        
        selects.forEach(select => {
            select.addEventListener('change', function() {
                // Soumettre le formulaire automatiquement
                form.submit();
            });
        });
    });
}

// Animation des cartes au scroll
function setupScrollAnimations() {
    const cards = document.querySelectorAll('.movie-card, .genre-card');
    
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        cardObserver.observe(card);
    });
}

// Gestion du thème sombre (optionnel)
function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.body.classList.toggle('dark-theme', currentTheme === 'dark');
    
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    setupCSRF();
    setupWatchlistButtons();
    setupRatingStars();
    setupLiveSearch();
    setupLazyLoading();
    setupFilterForms();
    setupScrollAnimations();
    setupThemeToggle();
    
    // Initialiser les tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialiser les popovers Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Gestion des erreurs globales
window.addEventListener('error', function(e) {
    console.error('Erreur JavaScript:', e.error);
    showToast('Une erreur inattendue s\'est produite', 'error');
});

// Gestion des erreurs de requêtes
window.addEventListener('unhandledrejection', function(e) {
    console.error('Erreur de requête:', e.reason);
    showToast('Erreur de connexion au serveur', 'error');
});

// Fonction utilitaire pour les requêtes API
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...window.defaultFetchOptions,
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle utility
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export des fonctions utilitaires pour d'autres scripts
window.MovieRec = {
    getCookie,
    showToast,
    apiRequest,
    debounce,
    throttle
};
