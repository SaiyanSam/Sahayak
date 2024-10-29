// Wait until the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function() {
    
    // Handle all donate buttons
    const donateButtons = document.querySelectorAll(".donate-btn");
    donateButtons.forEach(button => {
        button.addEventListener("click", function() {
            alert("Thank you for showing interest in donating! Donation functionality coming soon.");
        });
    });

    // Password matching for new user registration
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        const password = document.getElementById('password');
        const confirmPassword = document.getElementById('confirm_password');
        const errorMessage = document.getElementById('error-message');

        registerForm.addEventListener('submit', function(event) {
            if (password.value !== confirmPassword.value) {
                event.preventDefault();  // Prevent form submission
                errorMessage.textContent = "Passwords do not match!";
                errorMessage.style.color = "red";
                errorMessage.style.fontWeight = "bold";
            } else {
                errorMessage.textContent = "";
            }
        });
    }

    // Alert for "Start a Fundraiser" button on the hero section
    const fundraiserButton = document.querySelector(".hero-btn");
    if (fundraiserButton) {
        fundraiserButton.addEventListener("click", function() {
            alert("Redirecting to fundraiser setup page...");
            window.location.href = '/start-fundraiser'; // Adjust URL as per your route
        });
    }
});
