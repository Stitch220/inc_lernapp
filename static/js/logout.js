document.addEventListener("DOMContentLoaded", () => {
    const logoutButton = document.getElementById("logout-button");

    if (logoutButton) {
        logoutButton.addEventListener("click", () => {
            // Remove username and password from Local Storage
            localStorage.removeItem("username");
            localStorage.removeItem("password");

            // Redirect to the login page
            window.location.href = "/";
        });
    }
});
