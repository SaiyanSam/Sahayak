document.addEventListener("DOMContentLoaded", function() {
    // Add event listeners for all donate buttons
    const donateButtons = document.querySelectorAll(".donate-btn");

    donateButtons.forEach(button => {
        button.addEventListener("click", function() {
            alert("Thank you for showing interest in donating! Donation functionality coming soon.");
        });
    });
});
