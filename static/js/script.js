document.addEventListener("DOMContentLoaded", () => {
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");

    // Check if username and password exist in Local Storage
    const storedUsername = localStorage.getItem("username");
    const storedPassword = localStorage.getItem("password");

    if (storedUsername && storedPassword) {
        // Automatically verify credentials and redirect
        fetch("/auto_login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username: storedUsername, password: storedPassword }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    // Redirect to the appropriate role-based page
                    window.location.href = data.redirect_url;
                }
            });
    }

    // Pre-fill username field if available
    if (storedUsername) {
        usernameInput.value = storedUsername;
    }

    // Save username and password if "Stay Logged In" is checked
    document.querySelector("form").addEventListener("submit", (e) => {
        const stayLoggedIn = document.getElementById("stay_logged_in").checked;
        if (stayLoggedIn) {
            localStorage.setItem("username", usernameInput.value);
            localStorage.setItem("password", passwordInput.value);
        } else {
            localStorage.removeItem("username");
            localStorage.removeItem("password");
        }
    });
});
