(() => {
    const profileForms = document.querySelectorAll(".profile-form");
    profileForms.forEach(form => {
        form.addEventListener("submit", () => {
            const submitBtn = form.querySelector(".save-profile-btn");
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = "Saving...";
                submitBtn.style.opacity = "0.7";
            }
        });
    });

    window.addEventListener("DOMContentLoaded", () => {
        if (window.backendStatus) {
            const { error, success } = window.backendStatus;
            if (error) {
                alert(`Error: ${error}`); 
            } else if (success) {
                alert(`Success: ${success}`);
            }
        }
    });


    const toggleButtons = document.querySelectorAll(".toggle-password-btn");
    toggleButtons.forEach(btn => {
        btn.addEventListener("click", () => {

            const passwordInput = btn.previousElementSibling;
            
            if (passwordInput && passwordInput.tagName === "INPUT") {
                if (passwordInput.type === "password") {
                    passwordInput.type = "text";
                    btn.textContent = "Hide";
                } else {
                    passwordInput.type = "password";
                    btn.textContent = "Show";
                }
            }
        });
    });

    const avatarTrigger = document.getElementById("avatarTrigger");
    const avatarModal = document.getElementById("avatarModal");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const selectNewBtn = document.getElementById("selectNewBtn");
    const fileInputSelector = document.getElementById("fileInputSelector");
    const imageToCrop = document.getElementById("imageToCrop");
    const saveCroppedBtn = document.getElementById("saveCroppedBtn");
    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");

    let cropperInstance = null;


    if (avatarTrigger) {
        avatarTrigger.addEventListener("click", () => {
            avatarModal.style.display = "flex";

            const currentSrc = document.getElementById("currentAvatarImg").src;
            initCropper(currentSrc);
        });
    }


    if (closeModalBtn) {
        closeModalBtn.addEventListener("click", () => {
            avatarModal.style.display = "none";
            if (cropperInstance) {
                cropperInstance.destroy();
                cropperInstance = null;
            }
        });
    }


    if (selectNewBtn && fileInputSelector) {
        selectNewBtn.addEventListener("click", () => fileInputSelector.click());
        
        fileInputSelector.addEventListener("change", (e) => {
            const files = e.target.files;
            if (files && files.length > 0) {
                const reader = new FileReader();
                reader.onload = (event) => {

                    initCropper(event.target.result);
                };
                reader.readAsDataURL(files[0]);
            }
        });
    }


    function initCropper(imageSrc) {
        if (cropperInstance) {
            cropperInstance.destroy();
        }
        imageToCrop.src = imageSrc;
        

        cropperInstance = new Cropper(imageToCrop, {
            aspectRatio: 1,      
            viewMode: 1,         
            dragMode: 'move',    
            background: false,
            autoCropArea: 0.8,
        });
    }


    if (zoomInBtn && zoomOutBtn) {
        zoomInBtn.addEventListener("click", () => cropperInstance?.zoom(0.1));
        zoomOutBtn.addEventListener("click", () => cropperInstance?.zoom(-0.1));
    }


    if (saveCroppedBtn) {
        saveCroppedBtn.addEventListener("click", () => {
            if (!cropperInstance) return;


            saveCroppedBtn.disabled = true;
            saveCroppedBtn.textContent = "Uploading...";


            const canvas = cropperInstance.getCroppedCanvas({
                width: 300,
                height: 300
            });


            const base64Data = canvas.toDataURL("image/png");

            const csrfTokenElement = document.querySelector('input[name="csrf_token"]');
            const csrfToken = csrfTokenElement ? csrfTokenElement.value : '';


            fetch("/profile/avatar/upload_base64", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken, 
                    "X-CSRF-Token": csrfToken
                },
                body: JSON.stringify({ image: base64Data })
            })
            .then(res => {
                if (!res.ok) {

                    throw new Error(`HTTP status ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                if (data.status === "success") {
                    document.getElementById("currentAvatarImg").src = data.avatar_url + "?t=" + new Date().getTime();
                    avatarModal.style.display = "none";
                    alert("Avatar updated successfully!");
                } else {
                    alert("Failed: " + data.message);
                }
            })
            .catch((err) => {

                alert('Network error or Security block: ${err.message}');
            })
            .finally(() => {
                saveCroppedBtn.disabled = false;
                saveCroppedBtn.textContent = "Save Avatar";
            });
        });
    }
})();