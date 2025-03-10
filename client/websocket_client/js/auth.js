// auth.js

// Function to check if the user is logged in by checking the JWT token
function getAuthToken() {
    return localStorage.getItem('jwt_token');
}

// Function to handle logout
function logout() {
    // Remove the JWT token from localStorage to logout the user
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('key');

    localStorage.removeItem('secretkey');
    localStorage.removeItem('apikey');
    localStorage.removeItem('passphrase');
    
    // Redirect to login page
    window.location.href = "auth.html"; // Change this to your login page URL
    console.log(`${hostname}`)
    const response =  fetch(`http://${hostname}:5000/logout?username=${localStorage.getItem('username')}`)
    localStorage.removeItem('username');

}

// Function to update the navbar based on whether the user is logged in
function updateNavbar() {
    const token = getAuthToken();
    const logoutLink = document.getElementById('logout-link');
    const loginLink = document.getElementById('login-link');
    const logoutButton = document.querySelector('.logout-btn');

    if (token) {
        // User is logged in, show logout link and hide login link
        loginLink.style.display = 'none';
        logoutLink.style.display = 'inline-block';
        
        // Change logout button color to green for logged-in state
        logoutButton.classList.remove('logout-btn-logged-out');
        logoutButton.classList.add('logout-btn-logged-in');
    } else {
        // User is not logged in, show login link and hide logout link
        loginLink.style.display = 'inline-block';
        logoutLink.style.display = 'none';
        
        // Change logout button color to red for logged-out state
        logoutButton.classList.remove('logout-btn-logged-in');
        logoutButton.classList.add('logout-btn-logged-out');
    }
}

// Call the updateNavbar function to set the initial state when the page loads
updateNavbar();
