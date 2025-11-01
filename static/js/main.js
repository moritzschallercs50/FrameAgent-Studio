// Main JavaScript file for FrameAgent Studio

// Loading overlay functions
function showLoading(title = 'Processing...', message = 'Please wait while our agents work their magic') {
    const overlay = document.getElementById('loading-overlay');
    const titleEl = document.getElementById('loading-title');
    const messageEl = document.getElementById('loading-message');
    
    if (overlay && titleEl && messageEl) {
        titleEl.textContent = title;
        messageEl.textContent = message;
        overlay.classList.remove('hidden');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
}

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
});

// Escape key to close modals
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (!modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
                document.body.style.overflow = 'auto';
            }
        });
    }
});

// Format text with basic markdown-like parsing
function formatText(text) {
    if (!text) return '';
    
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}

// Parse numbered lists
function parseList(text) {
    if (!text) return '';
    
    const lines = text.split('\n');
    let html = '';
    let inList = false;
    
    lines.forEach(line => {
        const trimmed = line.trim();
        if (/^\d+\./.test(trimmed)) {
            if (!inList) {
                html += '<ol>';
                inList = true;
            }
            html += `<li>${trimmed.replace(/^\d+\.\s*/, '')}</li>`;
        } else if (trimmed) {
            if (inList) {
                html += '</ol>';
                inList = false;
            }
            html += `<p>${trimmed}</p>`;
        }
    });
    
    if (inList) {
        html += '</ol>';
    }
    
    return html;
}

// Auto-save functionality
let autoSaveTimeout = null;

function setupAutoSave(formSelector, saveCallback, delay = 2000) {
    const form = document.querySelector(formSelector);
    if (!form) return;
    
    const inputs = form.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                saveCallback();
            }, delay);
        });
    });
}

// Smooth scroll to element
function smoothScrollTo(element, offset = 0) {
    if (!element) return;
    
    const targetPosition = element.getBoundingClientRect().top + window.pageYOffset - offset;
    
    window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
    });
}

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy:', err);
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification('Copied to clipboard!', 'success');
    } catch (err) {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy', 'error');
    }
    
    document.body.removeChild(textArea);
}

// Show notification (simple toast)
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1'};
        color: white;
        border-radius: 12px;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Add notification animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// Debounce function
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

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Check if element is in viewport
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Animate elements on scroll
function animateOnScroll() {
    const elements = document.querySelectorAll('[data-animate]');
    
    elements.forEach(element => {
        if (isInViewport(element) && !element.classList.contains('animated')) {
            element.classList.add('animated');
            const animation = element.dataset.animate;
            element.style.animation = `${animation} 0.6s ease forwards`;
        }
    });
}

// Initialize scroll animations
if (document.querySelectorAll('[data-animate]').length > 0) {
    window.addEventListener('scroll', throttle(animateOnScroll, 100));
    animateOnScroll(); // Run once on load
}

// Form validation
function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('error');
            
            // Remove error class on input
            input.addEventListener('input', function() {
                this.classList.remove('error');
            }, { once: true });
        }
    });
    
    return isValid;
}

// Export functions to global scope
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.openModal = openModal;
window.closeModal = closeModal;
window.formatText = formatText;
window.parseList = parseList;
window.copyToClipboard = copyToClipboard;
window.showNotification = showNotification;
window.debounce = debounce;
window.throttle = throttle;
window.validateForm = validateForm;

// Log initialization
console.log('FrameAgent Studio - Frontend initialized');

