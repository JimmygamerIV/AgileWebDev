
//console.log("Script loaded successfully!");

const form = document.getElementById('login');
    
if (!form) {
    console.error("ERROR: Could not find the form with id 'signup-form'!");
} else {
    form.addEventListener('submit', async (event) => {
        event.preventDefault(); 
        console.log("Form submit intercepted!");

        const formData = new FormData(event.target);
    
        try {
            const response = await fetch('/signup', {
                method: 'POST',
                body: formData
            });
 
            const result = await response.json();
            console.log("Server response:", result);

            if (response.ok) {
                alert("SUCCESS: " + result.message);
            } else {
                console.log("P1:", formData.get('password'), "P2:", formData.get('confirm_password'));
                alert("OPPS: " + result.message);
            }
        } catch (error) {
            console.error("Fetch error:", error);
            alert("Network error occurred.");
        }
    });
}
