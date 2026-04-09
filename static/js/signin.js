document.getElementById('signin-form').addEventListener('submit', async (e) => {
    e.preventDefault(); 

    const formData = new FormData(e.target);
    
    try {
        const response = await fetch('/signin', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
           
            window.location.href = result.redirect; 
        } else {
            alert("Login Failed: " + result.message);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Network error, please try again.");
    }
});