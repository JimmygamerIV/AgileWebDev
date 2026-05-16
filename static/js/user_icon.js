
const SUN_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
const MOON_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);

    const checkbox = document.getElementById('theme-toggle-checkbox');
    const icon = document.getElementById('theme-icon');
    const label = document.getElementById('theme-label');

    const isLight = theme === 'light';
    if (checkbox) checkbox.checked = isLight;
    if (icon)     icon.innerHTML = isLight ? SUN_ICON : MOON_ICON;
    if (label)    label.textContent = isLight ? 'Light Mode' : 'Dark Mode';
}

document.addEventListener('DOMContentLoaded', function () {
    applyTheme(localStorage.getItem('theme') || 'dark');

    const themeToggleItem = document.getElementById('theme-toggle-item');
    if (themeToggleItem) {
        themeToggleItem.addEventListener('click', function (e) {
            e.stopPropagation();
            const checkbox = document.getElementById('theme-toggle-checkbox');
            if (!checkbox) return;
            if (e.target.type !== 'checkbox') checkbox.checked = !checkbox.checked;
            const newTheme = checkbox.checked ? 'light' : 'dark';
            localStorage.setItem('theme', newTheme);
            applyTheme(newTheme);
        });
    }
});

document.addEventListener('click', function (event) {
    const dropdownMenu = document.getElementById('dropdown-menu');
    if (!dropdownMenu) return;

    const isAvatarClick = event.target.closest('#avatar-btn');
    const isThemeToggle = event.target.closest('#theme-toggle-item');

    if (isAvatarClick) {
        event.preventDefault();
        dropdownMenu.classList.toggle('show');
    } else if (!isThemeToggle) {
        dropdownMenu.classList.remove('show');
    }
});
