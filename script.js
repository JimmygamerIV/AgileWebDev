import { UWA_LOCATIONS } from './locations.js';

const LOCATION_NAME = 'Social Sciences Lecture Theatre';
const location = UWA_LOCATIONS[LOCATION_NAME];

const map = L.map('map').setView([location.lat, location.lng], 17);

const layers = {
    white: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 20,
        attribution: '© OpenStreetMap contributors © CARTO'
    }),
    default: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 20,
        attribution: '© OpenStreetMap contributors'
    })
};

let activeStyle = 'white';
let activeLayer = layers[activeStyle];
activeLayer.addTo(map);

const styleToggleButton = document.getElementById('styleToggle');

function updateToggleLabel() {
    styleToggleButton.textContent =
        activeStyle === 'white' ? 'Switch to Default Style' : 'Switch to White Style';
}

function toggleMapStyle() {
    map.removeLayer(activeLayer);

    activeStyle = activeStyle === 'white' ? 'default' : 'white';
    activeLayer = layers[activeStyle];

    activeLayer.addTo(map);
    updateToggleLabel();
}

styleToggleButton.addEventListener('click', toggleMapStyle);
updateToggleLabel();

L.marker([location.lat, location.lng])
    .addTo(map)
    .bindPopup(LOCATION_NAME);