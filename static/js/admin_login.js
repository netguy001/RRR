// Admin Login JavaScript
// Your original HTML file didn't contain any JavaScript
// This file is ready for any admin login functionality you want to add
// Loading Screen
window.addEventListener('load', function () {
    const loadingScreen = document.getElementById('loadingScreen');

    // Minimum loading time of 2 seconds for professional feel
    setTimeout(function () {
        loadingScreen.classList.add('fade-out');

        // Remove from DOM after fade animation
        setTimeout(function () {
            if (loadingScreen) {
                loadingScreen.remove();
            }
        }, 500);
    }, 2000); // 2 second minimum loading time
});

document.addEventListener('DOMContentLoaded', function () {
    // Get form elements
    const form = document.querySelector('form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const submitButton = document.querySelector('.btn-submit');

    // You can add form validation, loading states, or other functionality here

    // Example: Add loading state on form submit
    if (form) {
        form.addEventListener('submit', function (e) {
            // Add loading state
            submitButton.textContent = 'Logging in...';
            submitButton.disabled = true;
        });
    }

    // Example: Focus management
    if (usernameInput) {
        usernameInput.focus();
    }

    console.log('Admin login page initialized');
});