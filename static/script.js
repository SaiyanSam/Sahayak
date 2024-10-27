//For Donate Button on Homepage
document.addEventListener("DOMContentLoaded", function() {
    // Add event listeners for all donate buttons
    const donateButtons = document.querySelectorAll(".donate-btn");

    donateButtons.forEach(button => {
        button.addEventListener("click", function() {
            alert("Thank you for showing interest in donating! Donation functionality coming soon.");
        });
    });
});

//For the password matching when new user
document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    const errorMessage = document.getElementById('error-message');

    // Add event listener to the form submission
    registerForm.addEventListener('submit', function(event) {
        // Check if passwords match
        if (password.value !== confirmPassword.value) {
            event.preventDefault();  // Prevent form submission
            errorMessage.textContent = "Passwords do not match!";  // Show error message
            errorMessage.style.color = "red";  // Style the error message
        } else {
            errorMessage.textContent = "";  // Clear error message if passwords match
        }
    });
});
