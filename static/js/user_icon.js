
document.addEventListener('click', function(event) {
    const dropdownMenu = document.getElementById('dropdown-menu');
    

    if (!dropdownMenu) return; 


    const isAvatarClick = event.target.closest('#avatar-btn');

    if (isAvatarClick) {

        event.preventDefault();
        dropdownMenu.classList.toggle('show');

    } else {

        dropdownMenu.classList.remove('show');
    }
});