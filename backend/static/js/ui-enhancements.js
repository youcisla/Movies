// Enhanced UI/UX JavaScript Functionality for MovieRec

class UIEnhancements {
    constructor() {
        this.init();
    }

    init() {
        this.setupLazyLoading();
        this.setupSmoothScrolling();
        this.setupSearchEnhancements();
        this.setupCardInteractions();
        this.setupLoadingStates();
        this.setupToastNotifications();
        this.setupParallaxEffects();
        this.setupAnimationObserver();
    }

    // Lazy Loading for Images
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('skeleton-loader');
                        img.classList.add('animate-fade-in');
                        observer.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                img.classList.add('skeleton-loader');
                imageObserver.observe(img);
            });
        }
    }

    // Enhanced Smooth Scrolling
    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const href = this.getAttribute('href');
                
                // Check if href is valid (not just '#' or empty)
                if (href && href !== '#' && href.length > 1) {
                    try {
                        const target = document.querySelector(href);
                        if (target) {
                            target.scrollIntoView({
                                behavior: 'smooth',
                                block: 'start'
                            });
                        }
                    } catch (error) {
                        console.warn('Invalid selector:', href);
                    }
                }
            });
        });
    }

    // Enhanced Search Functionality
    setupSearchEnhancements() {
        const searchInput = document.querySelector('.search-input');
        const searchSuggestions = document.getElementById('searchSuggestions');
        let searchTimeout;

        if (searchInput && searchSuggestions) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();

                if (query.length >= 2) {
                    searchTimeout = setTimeout(() => {
                        this.fetchSearchSuggestions(query, searchSuggestions);
                    }, 300);
                } else {
                    searchSuggestions.classList.remove('show');
                }
            });

            searchInput.addEventListener('focus', () => {
                searchInput.parentElement.classList.add('search-focused');
            });

            searchInput.addEventListener('blur', (e) => {
                setTimeout(() => {
                    searchInput.parentElement.classList.remove('search-focused');
                    searchSuggestions.classList.remove('show');
                }, 200);
            });

            // Close suggestions when clicking outside
            document.addEventListener('click', (e) => {
                if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
                    searchSuggestions.classList.remove('show');
                }
            });
        }
    }

    // Fetch Search Suggestions
    async fetchSearchSuggestions(query, container) {
        try {
            const response = await fetch(`/movies/api/search-suggestions/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                container.innerHTML = data.suggestions.map(suggestion => 
                    `<div class="suggestion-item" onclick="window.location.href='${suggestion.url}'">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-film me-2 text-muted"></i>
                            <div>
                                <div class="fw-semibold">${suggestion.title}</div>
                                <small class="text-muted">${suggestion.year || ''}</small>
                            </div>
                        </div>
                    </div>`
                ).join('');
                container.classList.add('show');
            } else {
                container.classList.remove('show');
            }
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            container.classList.remove('show');
        }
    }

    // Enhanced Card Interactions
    setupCardInteractions() {
        document.querySelectorAll('.movie-card').forEach(card => {
            // Add tilt effect on mouse move
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / centerY * 5;
                const rotateY = (centerX - x) / centerX * 5;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(20px)`;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)';
            });

            // Add ripple effect on click
            card.addEventListener('click', this.createRippleEffect);
        });
    }

    // Create Ripple Effect
    createRippleEffect(e) {
        const button = e.currentTarget;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple-effect');
        
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    // Loading States Management
    setupLoadingStates() {
        // Show loading state for forms
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    const originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Chargement...';
                    submitBtn.disabled = true;
                    
                    // Re-enable after 5 seconds as fallback
                    setTimeout(() => {
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                    }, 5000);
                }
            });
        });

        // Show loading state for AJAX requests
        this.setupAjaxLoadingStates();
    }

    // AJAX Loading States
    setupAjaxLoadingStates() {
        document.querySelectorAll('[data-ajax]').forEach(element => {
            element.addEventListener('click', async (e) => {
                e.preventDefault();
                const url = element.getAttribute('data-ajax');
                const target = element.getAttribute('data-target');
                
                if (url && target) {
                    const targetElement = document.querySelector(target);
                    if (targetElement) {
                        // Show loading skeleton
                        targetElement.innerHTML = this.createLoadingSkeleton();
                        
                        try {
                            const response = await fetch(url);
                            const html = await response.text();
                            targetElement.innerHTML = html;
                            
                            // Trigger animation
                            targetElement.classList.add('animate-fade-in-up');
                        } catch (error) {
                            targetElement.innerHTML = '<div class="alert alert-danger">Erreur de chargement</div>';
                        }
                    }
                }
            });
        });
    }

    // Create Loading Skeleton
    createLoadingSkeleton() {
        return `
            <div class="loading-card">
                <div class="skeleton-loader skeleton-image"></div>
                <div class="skeleton-loader skeleton-title"></div>
                <div class="skeleton-loader skeleton-text"></div>
                <div class="skeleton-loader skeleton-text" style="width: 60%;"></div>
            </div>
        `;
    }

    // Toast Notifications
    setupToastNotifications() {
        window.showToast = (message, type = 'info', duration = 5000) => {
            const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
            const toast = this.createToast(message, type);
            
            toastContainer.appendChild(toast);
            
            // Trigger animation
            setTimeout(() => toast.classList.add('show'), 100);
            
            // Auto remove
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        };
    }

    // Create Toast Container
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        container.style.marginTop = '80px';
        document.body.appendChild(container);
        return container;
    }

    // Create Toast Element
    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-header">
                <i class="fas fa-${this.getToastIcon(type)} me-2"></i>
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        return toast;
    }

    // Get Toast Icon
    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Parallax Effects
    setupParallaxEffects() {
        const parallaxElements = document.querySelectorAll('[data-parallax]');
        
        if (parallaxElements.length > 0) {
            window.addEventListener('scroll', () => {
                const scrollTop = window.pageYOffset;
                
                parallaxElements.forEach(element => {
                    const speed = element.getAttribute('data-parallax') || 0.5;
                    const yPos = -(scrollTop * speed);
                    element.style.transform = `translateY(${yPos}px)`;
                });
            });
        }
    }

    // Animation Observer
    setupAnimationObserver() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const animationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const animationType = element.getAttribute('data-animation') || 'fade-in-up';
                    
                    element.classList.add(`animate-${animationType}`);
                    animationObserver.unobserve(element);
                }
            });
        }, observerOptions);

        // Observe elements with animation attributes
        document.querySelectorAll('[data-animation]').forEach(element => {
            animationObserver.observe(element);
        });

        // Auto-observe common elements
        document.querySelectorAll('.card, .movie-card, .feature-card').forEach(element => {
            element.setAttribute('data-animation', 'fade-in-up');
            animationObserver.observe(element);
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new UIEnhancements();
});

// Utility Functions
const Utils = {
    // Debounce function
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Throttle function
    throttle: (func, limit) => {
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
    },

    // Format number with commas
    formatNumber: (num) => {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },

    // Get CSRF Token
    getCSRFToken: () => {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }
};

// Export for global use
window.UIEnhancements = UIEnhancements;
window.Utils = Utils;
