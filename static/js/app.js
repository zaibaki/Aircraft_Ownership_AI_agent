// Utility functions for the aircraft research app

// Format loading messages with dynamic content
function updateLoadingMessage(message, nNumber = '') {
    const element = document.getElementById('loadingDescription');
    if (element) {
        if (nNumber) {
            element.textContent = message.replace('{{n_number}}', nNumber);
        } else {
            element.textContent = message;
        }
    }
}

// Animate elements on scroll
function observeElements() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
            }
        });
    });

    document.querySelectorAll('.observe').forEach(el => {
        observer.observe(el);
    });
}

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    observeElements();
    
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});