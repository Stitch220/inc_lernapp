document.addEventListener("DOMContentLoaded", () => {
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");

    // Load stored username if available
    const storedUsername = localStorage.getItem("username");
    if (storedUsername) {
        usernameInput.value = storedUsername;
    }

    // Save username if "Stay Logged In" is checked
    document.querySelector("form").addEventListener("submit", (e) => {
        const stayLoggedIn = document.getElementById("stay_logged_in").checked;
        if (stayLoggedIn) {
            localStorage.setItem("username", usernameInput.value);
        } else {
            localStorage.removeItem("username");
        }
    });
});
