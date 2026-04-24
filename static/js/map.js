(() => {
  const mapElement = document.getElementById("map");
  const styleToggleButton = document.getElementById("styleToggle");
  const fullscreenToggleButton = document.getElementById("fullscreenToggle");
  const mapBoxElement = document.querySelector(".map-box");
  const classesPanelElement = document.querySelector(".upcoming");
  const classesToggleButton = document.querySelector(".upcoming .toggle-btn");

  if (!mapElement || !styleToggleButton || !fullscreenToggleButton || !mapBoxElement || typeof L === "undefined") {
    return;
  }

  // Use the Social Sciences / Student Central area as a sensible campus default.
  const fallbackLocation = {
    name: "Social Sciences / UWA Student Central Building",
    lat: -31.980436934419682,
    lng: 115.81913327444458,
  };

  const map = L.map("map").setView([fallbackLocation.lat, fallbackLocation.lng], 17);
  let classMarker = null;

  // Prevent browser-level page zoom gestures when interacting with the map area.
  mapElement.addEventListener(
    "wheel",
    (event) => {
      if (event.ctrlKey) {
        event.preventDefault();
      }
    },
    { passive: false }
  );

  const layers = {
    white: L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      maxZoom: 20,
      attribution: "© OpenStreetMap contributors © CARTO",
    }),
    default: L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 20,
      attribution: "© OpenStreetMap contributors",
    }),
  };

  let activeStyle = "white";
  let activeLayer = layers[activeStyle];
  activeLayer.addTo(map);

  const maximizeIcon =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>';
  const minimizeIcon =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 14h6v6M20 10h-6V4M14 10l7-7M3 21l7-7"/></svg>';

  function isFullscreen() {
    return document.fullscreenElement === mapBoxElement;
  }

  function updateFullscreenButton() {
    if (isFullscreen()) {
      fullscreenToggleButton.innerHTML = minimizeIcon;
      fullscreenToggleButton.setAttribute("aria-label", "Exit fullscreen map");
      fullscreenToggleButton.setAttribute("title", "Exit fullscreen");
      return;
    }

    fullscreenToggleButton.innerHTML = maximizeIcon;
    fullscreenToggleButton.setAttribute("aria-label", "Enter fullscreen map");
    fullscreenToggleButton.setAttribute("title", "Enter fullscreen");
  }

  async function toggleFullscreen() {
    if (isFullscreen()) {
      await document.exitFullscreen();
      return;
    }

    await mapBoxElement.requestFullscreen();
  }

  function wireZoomControl(selector, zoomAction) {
    const control = mapElement.querySelector(selector);
    if (!control) {
      return;
    }

    control.setAttribute("href", "javascript:void(0)");
    control.setAttribute("tabindex", "-1");
    control.addEventListener("mousedown", (event) => {
      // Prevent focus changes that can scroll the page to the control.
      event.preventDefault();
    });
    control.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      zoomAction();
      control.blur();
    });
  }

  function updateToggleLabel() {
    styleToggleButton.textContent =
      activeStyle === "white" ? "Switch to Detailed View" : "Switch to Simple View";
  }

  function toggleMapStyle() {
    map.removeLayer(activeLayer);

    activeStyle = activeStyle === "white" ? "default" : "white";
    activeLayer = layers[activeStyle];

    activeLayer.addTo(map);
    updateToggleLabel();
  }

  function updateClassesToggleState() {
    if (!classesPanelElement || !classesToggleButton) {
      return;
    }

    const isCollapsed = classesPanelElement.classList.contains("collapsed");
    classesToggleButton.textContent = isCollapsed ? "▲" : "▼";
    classesToggleButton.setAttribute("aria-expanded", String(!isCollapsed));
    classesToggleButton.setAttribute("title", isCollapsed ? "Expand classes" : "Collapse classes");
  }

  function toggleClassesPanel() {
    if (!classesPanelElement) {
      return;
    }

    classesPanelElement.classList.toggle("collapsed");
    updateClassesToggleState();
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function popupHtml(classData) {
    const friendNames = Array.isArray(classData.friend_nicknames) ? classData.friend_nicknames : [];
    const friendsDisplay = friendNames.map((name) => escapeHtml(name)).join(", ");
    const attendeeCount = Number(classData.other_attendees_count || 0);

    const rawFloor = (classData.floor ?? "").toString().trim();
    const normalizedFloor = rawFloor.toLowerCase();
    const hasFloor =
      rawFloor.length > 0 &&
      normalizedFloor !== "null" &&
      normalizedFloor !== "none" &&
      normalizedFloor !== "n/a" &&
      normalizedFloor !== "na" &&
      normalizedFloor !== "unknown";

    const attendanceSummary =
      friendsDisplay.length > 0
        ? `${attendeeCount} friends attending (${friendsDisplay})`
        : `${attendeeCount} friends attending`;

    const floorListItem = hasFloor
      ? `<li><span style="font-weight: 600;">Floor:</span> ${escapeHtml(rawFloor)}</li>`
      : "";

    return `
      <div>
        <strong>${escapeHtml(classData.event_name || "Untitled")}</strong><br>
        <ul style="margin: 8px 0 0 18px; padding: 0;">
          <li><span style="font-weight: 600;">Building:</span> ${escapeHtml(classData.building_name || "Unknown building")}</li>
          ${floorListItem}
          <li><span style="font-weight: 600;">Time:</span> ${escapeHtml(classData.time_display || "Unknown")}</li>
          <li><span style="font-weight: 600;">Room:</span> ${escapeHtml(classData.location_display || "Unknown")}</li>
          <li>${attendanceSummary}</li>
        </ul>
      </div>
    `;
  }

  function setMarker(lat, lng, popupText) {
    if (classMarker) {
      map.removeLayer(classMarker);
    }

    classMarker = L.marker([lat, lng]).addTo(map).bindPopup(popupText);
    map.setView([lat, lng], 17);
  }

  async function loadCurrentClassMarker() {
    try {
      const response = await fetch("/api/map/current-class", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        setMarker(fallbackLocation.lat, fallbackLocation.lng, fallbackLocation.name);
        return;
      }

      const payload = await response.json();
      const classData = payload.class;

      if (!classData) {
        setMarker(
          fallbackLocation.lat,
          fallbackLocation.lng,
          "No current or upcoming classes found."
        );
        return;
      }

      const lat = Number(classData.latitude);
      const lng = Number(classData.longitude);

      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        setMarker(lat, lng, popupHtml(classData));
        return;
      }

      setMarker(
        fallbackLocation.lat,
        fallbackLocation.lng,
        "Current/next class found, but map coordinates were unavailable."
      );
    } catch (_error) {
      setMarker(fallbackLocation.lat, fallbackLocation.lng, fallbackLocation.name);
    }
  }

  L.DomEvent.disableClickPropagation(styleToggleButton);
  L.DomEvent.disableScrollPropagation(styleToggleButton);
  styleToggleButton.addEventListener("click", toggleMapStyle);

  L.DomEvent.disableClickPropagation(fullscreenToggleButton);
  L.DomEvent.disableScrollPropagation(fullscreenToggleButton);
  fullscreenToggleButton.addEventListener("click", () => {
    toggleFullscreen().catch(() => {
      // Ignore fullscreen failures caused by browser restrictions.
    });
  });

  document.addEventListener("fullscreenchange", () => {
    updateFullscreenButton();
    map.invalidateSize();
  });

  wireZoomControl(".leaflet-control-zoom-in", () => map.zoomIn());
  wireZoomControl(".leaflet-control-zoom-out", () => map.zoomOut());

  updateFullscreenButton();
  updateToggleLabel();
  updateClassesToggleState();

  if (classesToggleButton) {
    classesToggleButton.addEventListener("click", toggleClassesPanel);
  }

  loadCurrentClassMarker();
})();
