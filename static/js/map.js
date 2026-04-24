(() => {
  const mapElement = document.getElementById("map");
  const styleToggleButton = document.getElementById("styleToggle");
  const fullscreenToggleButton = document.getElementById("fullscreenToggle");
  const mapBoxElement = document.querySelector(".map-box");
  const classesPanelElement = document.querySelector(".upcoming");
  const classesToggleButton = document.querySelector(".upcoming .toggle-btn");
  const stopSelectingButton = document.getElementById("stopSelectingBtn");
  const classesDataElement = document.getElementById("classesMapData");
  const classItemElements = Array.from(document.querySelectorAll(".event-item[data-event-id]"));

  if (!mapElement || !styleToggleButton || !fullscreenToggleButton || !mapBoxElement || typeof L === "undefined") {
    return;
  }

  // Use Reid Library as the default campus center.
  const fallbackLocation = {
    name: "Reid Library",
    lat: -31.978928653749154,
    lng: 115.81772758275724,
  };

  const map = L.map("map").setView([fallbackLocation.lat, fallbackLocation.lng], 17);
  let activeMarkers = [];
  let selectedEventId = null;
  let classesData = [];
  const classDataById = new Map();

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

  function parseClassesData() {
    if (!classesDataElement) {
      return;
    }

    try {
      const parsed = JSON.parse(classesDataElement.textContent || "[]");
      if (!Array.isArray(parsed)) {
        return;
      }

      classesData = parsed;
      for (const classData of classesData) {
        if (classData && classData.event_id !== undefined && classData.event_id !== null) {
          classDataById.set(String(classData.event_id), classData);
        }
      }
    } catch (_error) {
      classesData = [];
    }
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

  function clearMarkers() {
    for (const marker of activeMarkers) {
      map.removeLayer(marker);
    }
    activeMarkers = [];
  }

  function updateStopSelectingButton() {
    if (!stopSelectingButton) {
      return;
    }

    const isSelecting = selectedEventId !== null;
    stopSelectingButton.classList.toggle("visible", isSelecting);
    stopSelectingButton.setAttribute("aria-hidden", String(!isSelecting));
  }

  function updateClassHighlights() {
    const selectedId = selectedEventId === null ? "" : String(selectedEventId);
    for (const classItem of classItemElements) {
      classItem.classList.toggle("selected", classItem.dataset.eventId === selectedId);
    }
  }

  function isOnlineClass(classData) {
    const searchableText = `${classData?.event_name || ""} ${classData?.location_display || ""} ${classData?.building_name || ""}`.toLowerCase();
    return /\bonline\b|\bvirtual\b|\bremote\b|\bzoom\b|\bteams\b|\bwebex\b|\bcollaborate\b/.test(searchableText);
  }

  function addMarkerForClass(classData, openPopup = false) {
    if (isOnlineClass(classData)) {
      return null;
    }

    const lat = Number(classData.latitude);
    const lng = Number(classData.longitude);

    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      return null;
    }

    const marker = L.marker([lat, lng]).addTo(map).bindPopup(popupHtml(classData));
    activeMarkers.push(marker);

    if (openPopup) {
      marker.openPopup();
      map.setView([lat, lng], 17);
    }

    return marker;
  }

  function getClassWindow(classData) {
    if (!classData || !classData.date || !classData.start_time || !classData.end_time) {
      return null;
    }

    const start = new Date(`${classData.date}T${classData.start_time}:00`);
    let end = new Date(`${classData.date}T${classData.end_time}:00`);

    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
      return null;
    }

    if (end <= start) {
      end = new Date(end.getTime() + 24 * 60 * 60 * 1000);
    }

    return { start, end };
  }

  function getCurrentOrNextClassData() {
    const now = new Date();
    let currentClass = null;
    let nextClass = null;

    for (const classData of classesData) {
      const window = getClassWindow(classData);
      if (!window) {
        continue;
      }

      if (window.start <= now && now < window.end) {
        if (!currentClass || window.start < currentClass.start) {
          currentClass = { start: window.start, classData };
        }
        continue;
      }

      if (window.start > now) {
        if (!nextClass || window.start < nextClass.start) {
          nextClass = { start: window.start, classData };
        }
      }
    }

    if (currentClass) {
      return currentClass.classData;
    }
    if (nextClass) {
      return nextClass.classData;
    }

    return null;
  }

  function renderDefaultClassMarker() {
    clearMarkers();

    const targetClass = getCurrentOrNextClassData();
    if (targetClass) {
      const marker = addMarkerForClass(targetClass, false);
      if (marker) {
        map.setView(marker.getLatLng(), 17);
        return;
      }

      const fallbackMarker = L.marker([fallbackLocation.lat, fallbackLocation.lng])
        .addTo(map)
        .bindPopup(`${popupHtml(targetClass)}<div style="margin-top: 6px; font-size: 12px;">Map coordinates unavailable for this class.</div>`);
      activeMarkers.push(fallbackMarker);
      map.setView([fallbackLocation.lat, fallbackLocation.lng], 17);
      return;
    }

    const fallbackMarker = L.marker([fallbackLocation.lat, fallbackLocation.lng])
        .addTo(map)
        .bindPopup("No current or upcoming classes found.");
    activeMarkers.push(fallbackMarker);
    map.setView([fallbackLocation.lat, fallbackLocation.lng], 17);
  }

  function selectClass(eventId) {
    const classData = classDataById.get(String(eventId));
    if (!classData) {
      return;
    }

    selectedEventId = classData.event_id;
    updateClassHighlights();
    updateStopSelectingButton();

    clearMarkers();
    const marker = addMarkerForClass(classData, true);
    if (marker) {
      return;
    }

    const fallbackMarker = L.marker([fallbackLocation.lat, fallbackLocation.lng])
      .addTo(map)
      .bindPopup(`${popupHtml(classData)}<div style="margin-top: 6px; font-size: 12px;">Map coordinates unavailable for this class.</div>`)
      .openPopup();

    activeMarkers.push(fallbackMarker);
    map.setView([fallbackLocation.lat, fallbackLocation.lng], 17);
  }

  function stopSelecting() {
    if (selectedEventId === null) {
      return;
    }

    selectedEventId = null;
    updateClassHighlights();
    updateStopSelectingButton();
    renderDefaultClassMarker();
  }

  function wireClassSelection() {
    for (const classItem of classItemElements) {
      const eventId = classItem.dataset.eventId;
      if (!eventId) {
        continue;
      }

      classItem.addEventListener("click", () => {
        selectClass(eventId);
      });

      classItem.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") {
          return;
        }

        event.preventDefault();
        selectClass(eventId);
      });
    }

    if (stopSelectingButton) {
      stopSelectingButton.addEventListener("click", stopSelecting);
      L.DomEvent.disableClickPropagation(stopSelectingButton);
      L.DomEvent.disableScrollPropagation(stopSelectingButton);
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
  updateStopSelectingButton();

  if (classesToggleButton) {
    classesToggleButton.addEventListener("click", toggleClassesPanel);
  }

  parseClassesData();
  wireClassSelection();
  renderDefaultClassMarker();
})();
