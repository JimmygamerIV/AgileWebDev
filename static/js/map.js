(() => {
  const mapElement = document.getElementById("map");
  const styleToggleButton = document.getElementById("styleToggle");
  const fullscreenToggleButton = document.getElementById("fullscreenToggle");
  const routesToggleButton = document.getElementById("routesToggle");
  const mapBoxElement = document.querySelector(".map-box");
  const classesPanelElement = document.querySelector(".upcoming");
  const classesToggleButton = document.querySelector(".upcoming .toggle-btn");
  const stopSelectingButton = document.getElementById("stopSelectingBtn");
  const classesDataElement = document.getElementById("classesMapData");
  const fixedNowElement = document.getElementById("fixedNowData");
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
  let activeRouteLine = null;
  let selectedEventId = null;
  let viewedDay = null;
  let classesData = [];
  let routesEnabled = true;
  const classDataById = new Map();
  let fixedNow = null;
  const onlineBadgeSvg = `
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <rect x="4.5" y="6" width="15" height="9" rx="1.4" fill="none" stroke="currentColor" stroke-width="2" />
      <path d="M3 18h18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
    </svg>
  `;
  const onlineMarkerSvg = `
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <rect x="4.5" y="6" width="15" height="9" rx="1.4" fill="none" stroke="currentColor" stroke-width="2" />
      <path d="M3 18h18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
    </svg>
  `;
  const goldMarkerSvg = `
    <svg viewBox="0 0 25 41" aria-hidden="true" focusable="false">
      <path
        d="M12.5 0C5.6 0 0 5.6 0 12.5c0 10.5 12.5 28.5 12.5 28.5S25 23 25 12.5C25 5.6 19.4 0 12.5 0z"
        fill="#f2b705"
        stroke="#c99700"
        stroke-width="1"
      />
      <circle cx="12.5" cy="12.5" r="4.5" fill="#ffffff" />
    </svg>
  `;
  const onlineMarkerIcon = L.divIcon({
    className: "online-class-marker",
    html: onlineMarkerSvg,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  });
  const goldMarkerIcon = L.divIcon({
    className: "gold-class-marker",
    html: goldMarkerSvg,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
  });

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

  function updateRoutesToggleLabel() {
    if (!routesToggleButton) {
      return;
    }

    routesToggleButton.textContent = routesEnabled ? "Routes On" : "Routes Off";
    routesToggleButton.setAttribute("aria-pressed", String(routesEnabled));
    routesToggleButton.setAttribute("title", routesEnabled ? "Hide routes" : "Show routes");
  }

  function getNow() {
    return fixedNow ? new Date(fixedNow) : new Date();
  }

  function toggleRoutes() {
    routesEnabled = !routesEnabled;
    updateRoutesToggleLabel();
    if (selectedEventId === null) {
      updateRouteVisualization();
    }
  }

  function updateRouteVisualization() {
    clearRouteLine();

    if (!routesEnabled || selectedEventId !== null) {
      return;
    }

    // If viewing a specific day, redraw routes for that day
    if (viewedDay !== null) {
      const dayClasses = classesData.filter((c) => c && c.date === viewedDay && !isOnlineClass(c));
      const renderableEntries = [];
      for (const classData of dayClasses) {
        const window = getClassWindow(classData);
        if (!window) continue;

        const lat = Number(classData.latitude);
        const lng = Number(classData.longitude);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue;

        renderableEntries.push({ classData, start: window.start, lat, lng });
      }

      renderableEntries.sort((a, b) => a.start - b.start);

      // Find the target (gold) class
      const now = new Date();
      let currentEntry = null;
      let nextEntry = null;
      for (const entry of renderableEntries) {
        const window = getClassWindow(entry.classData);
        if (!window) continue;
        if (window.start <= now && now < window.end) {
          if (!currentEntry || window.start < currentEntry.start) {
            currentEntry = { start: window.start, entry };
          }
          continue;
        }
        if (window.start > now) {
          if (!nextEntry || window.start < nextEntry.start) {
            nextEntry = { start: window.start, entry };
          }
        }
      }

      const targetClass = currentEntry ? currentEntry.entry.classData : nextEntry ? nextEntry.entry.classData : null;
      const targetId = targetClass ? String(targetClass.event_id) : null;
      const blueEntries = targetId
        ? renderableEntries.filter((entry) => String(entry.classData.event_id) !== targetId)
        : renderableEntries;

      const routeCoords = [];
      if (targetClass) {
        const lat = Number(targetClass.latitude);
        const lng = Number(targetClass.longitude);
        routeCoords.push([Number.isFinite(lat) && Number.isFinite(lng) ? lat : fallbackLocation.lat, Number.isFinite(lat) && Number.isFinite(lng) ? lng : fallbackLocation.lng]);
      }
      for (const entry of blueEntries) {
        routeCoords.push([entry.lat, entry.lng]);
      }

      if (routeCoords.length > 1) {
        activeRouteLine = L.polyline(routeCoords, {
          color: "#5f8dff",
          weight: 3,
          opacity: 0.8,
          dashArray: "4 6",
          lineCap: "round",
          lineJoin: "round",
          className: "route-line",
        }).addTo(map);
      }
      return;
    }

    // Otherwise use the active date (default view)
    const renderableEntries = getRenderableClassEntries();

    // Compute the target (gold) class from the single-day renderable entries
    const now = new Date();
    let currentEntry = null;
    let nextEntry = null;
    for (const entry of renderableEntries) {
      const window = getClassWindow(entry.classData);
      if (!window) continue;
      if (window.start <= now && now < window.end) {
        if (!currentEntry || window.start < currentEntry.start) {
          currentEntry = { start: window.start, entry };
        }
        continue;
      }
      if (window.start > now) {
        if (!nextEntry || window.start < nextEntry.start) {
          nextEntry = { start: window.start, entry };
        }
      }
    }

    const targetClass = currentEntry ? currentEntry.entry.classData : nextEntry ? nextEntry.entry.classData : null;
    const targetId = targetClass ? String(targetClass.event_id) : null;
    const blueEntries = targetId
      ? renderableEntries.filter((entry) => String(entry.classData.event_id) !== targetId)
      : renderableEntries;

    const routeCoords = [];
    if (targetClass) {
      const lat = Number(targetClass.latitude);
      const lng = Number(targetClass.longitude);
      routeCoords.push([Number.isFinite(lat) && Number.isFinite(lng) ? lat : fallbackLocation.lat, Number.isFinite(lat) && Number.isFinite(lng) ? lng : fallbackLocation.lng]);
    }
    for (const entry of blueEntries) {
      routeCoords.push([entry.lat, entry.lng]);
    }

    if (routeCoords.length > 1) {
      activeRouteLine = L.polyline(routeCoords, {
        color: "#5f8dff",
        weight: 3,
        opacity: 0.8,
        dashArray: "4 6",
        lineCap: "round",
        lineJoin: "round",
        className: "route-line",
      }).addTo(map);
    }
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

  function parseFixedNow() {
    if (!fixedNowElement) {
      return;
    }

    try {
      const parsed = JSON.parse(fixedNowElement.textContent || "{}");
      if (parsed && parsed.now) {
        fixedNow = parsed.now;
      }
    } catch (_error) {
      fixedNow = null;
    }
  }

  function computeActiveDate() {
    const now = getNow();
    const today = now.toISOString().slice(0, 10);
    const timeNow = now.toTimeString().slice(0, 5);

    const dates = Array.from(new Set(classesData.map((c) => c.date).filter(Boolean))).sort();
    if (!dates.length) {
      return today;
    }

    // Helper to check if a date has any non-online classes
    const hasNonOnlineClasses = (date) => {
      return classesData.some((c) => {
        if (c.date !== date) return false;
        if (isOnlineClass(c)) return false;
        return true;
      });
    };

    // Check if today has remaining non-online classes
    if (dates.includes(today)) {
      const remainingToday = classesData.some((c) => {
        if (c.date !== today) return false;
        if (isOnlineClass(c)) return false;
        if (!c.end_time) return true;
        return c.end_time > timeNow;
      });

      if (remainingToday) {
        return today;
      }
    }

    // Find the first future date that has non-online classes
    for (const d of dates) {
      if (d >= today && hasNonOnlineClasses(d)) {
        return d;
      }
    }

    // If no future date has non-online classes, find any date with non-online classes
    for (const d of dates) {
      if (hasNonOnlineClasses(d)) {
        return d;
      }
    }

    // Fallback: return today if no non-online classes exist anywhere
    return today;
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
    const dayLabel = (function () {
      try {
        if (!classData || !classData.date) return "Unknown";
        const now = getNow();
        const today = now.toISOString().slice(0, 10);
        const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
        if (classData.date === today) return "Today";
        if (classData.date === tomorrow) return "Tomorrow";
        return classData.date;
      } catch (e) {
        return classData.date || "Unknown";
      }
    })();

    return `
      <div>
        <strong>${escapeHtml(classData.event_name || "Untitled")}</strong><br>
        <ul style="margin: 8px 0 0 18px; padding: 0;">
          <li><span style="font-weight: 600;">Day:</span> ${escapeHtml(dayLabel)}</li>
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

  function clearRouteLine() {
    if (!activeRouteLine) {
      return;
    }

    map.removeLayer(activeRouteLine);
    activeRouteLine = null;
  }

  function updateStopSelectingButton() {
    if (!stopSelectingButton) {
      return;
    }

    const isSelecting = selectedEventId !== null;
    const isViewingDay = viewedDay !== null;
    const shouldShow = isSelecting || isViewingDay;

    stopSelectingButton.classList.toggle("visible", shouldShow);
    stopSelectingButton.setAttribute("aria-hidden", String(!shouldShow));

    if (isViewingDay && !isSelecting) {
      stopSelectingButton.setAttribute("title", "Back to today's schedule");
      stopSelectingButton.setAttribute("aria-label", "Back to today's schedule");
    } else {
      stopSelectingButton.setAttribute("title", "Clear selection");
      stopSelectingButton.setAttribute("aria-label", "Clear selection");
    }
  }

  function updateClassHighlights() {
    const selectedId = selectedEventId === null ? "" : String(selectedEventId);
    for (const classItem of classItemElements) {
      classItem.classList.toggle("selected", classItem.dataset.eventId === selectedId);
    }
  }

  // Friend overlays state
  const selectedFriends = new Map();
  const friendOverlays = {}; // friendId -> { markers: [], route: L.polyline|null, color }

  function clearFriendOverlays() {
    for (const fid of Object.keys(friendOverlays)) {
      const layer = friendOverlays[fid];
      if (!layer) continue;
      if (layer.route) {
        map.removeLayer(layer.route);
      }
      for (const m of layer.markers || []) {
        map.removeLayer(m);
      }
    }
    for (const k in friendOverlays) delete friendOverlays[k];
  }

  function removeFriendOverlay(friendId) {
    const layer = friendOverlays[String(friendId)];
    if (!layer) {
      return;
    }

    if (layer.route) {
      map.removeLayer(layer.route);
    }
    for (const marker of layer.markers || []) {
      map.removeLayer(marker);
    }

    delete friendOverlays[String(friendId)];
  }

  // Build a set of user's class keys for collision detection
  function buildUserClassKeySet(activeDate) {
    const keys = new Set();
    for (const c of classesData) {
      if (!c || c.date !== activeDate) continue;
      const key = `${c.event_name || ''}||${c.date || ''}||${c.start_time || ''}||${c.end_time || ''}||${c.location_display || ''}`;
      keys.add(key);
    }
    return keys;
  }

  function getRandomColor() {
    const h = Math.floor(Math.random() * 360);
    return `hsl(${h} 80% 45%)`;
  }

  function escapeAttribute(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function normalizeAvatarUrl(avatarUrl) {
    if (!avatarUrl) {
      return "/static/uploads/default.jpg";
    }

    if (avatarUrl.startsWith("http://") || avatarUrl.startsWith("https://") || avatarUrl.startsWith("/")) {
      return avatarUrl;
    }

    return `/static/uploads/${avatarUrl}`;
  }

  function createFriendAvatarIcon(avatarUrl, color) {
    const safeAvatarUrl = normalizeAvatarUrl(avatarUrl);
    return L.divIcon({
      className: "friend-avatar-marker",
      html: `
        <div class="friend-avatar-marker-ring" style="border-color: ${color};">
          <img class="friend-avatar-marker-image" src="${escapeAttribute(safeAvatarUrl)}" alt="Friend avatar" />
        </div>
      `,
      iconSize: [36, 36],
      iconAnchor: [18, 18],
      popupAnchor: [0, -18],
    });
  }

  function buildFriendPopupHtml(friendMeta, classData) {
    const friendName = friendMeta?.friendName || "Friend";
    return `
      <div>
        <div style="font-size: 12px; font-weight: 700; color: #6b7280; margin-bottom: 4px;">Viewing ${escapeHtml(friendName)}'s upcoming class:</div>
        ${popupHtml(classData)}
      </div>
    `;
  }

  async function fetchFriendClasses(friendId, date) {
    const url = new URL('/api/friends/classes', window.location.origin);
    url.searchParams.set('friend_id', String(friendId));
    if (date) url.searchParams.set('date', date);
    const res = await fetch(url.toString(), { credentials: 'same-origin' });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data.classes) ? data.classes : [];
  }

  function getClassWindowFromObj(classData) {
    if (!classData || !classData.date || !classData.start_time || !classData.end_time) return null;
    const start = new Date(`${classData.date}T${classData.start_time}:00`);
    let end = new Date(`${classData.date}T${classData.end_time}:00`);
    if (end <= start) end = new Date(end.getTime() + 24 * 60 * 60 * 1000);
    return { start, end };
  }

  function computeFriendTargetClass(entries) {
    const now = getNow();
    let currentEntry = null;
    let nextEntry = null;
    for (const entry of entries) {
      const window = getClassWindowFromObj(entry);
      if (!window) continue;
      if (window.start <= now && now < window.end) {
        if (!currentEntry || window.start < currentEntry.start) {
          currentEntry = { start: window.start, entry };
        }
        continue;
      }
      if (window.start > now) {
        if (!nextEntry || window.start < nextEntry.start) {
          nextEntry = { start: window.start, entry };
        }
      }
    }
    return currentEntry ? currentEntry.entry : nextEntry ? nextEntry.entry : null;
  }

  async function renderOverlayForFriend(friendId, friendMeta, color, activeDate, userKeys) {
    const existing = friendOverlays[String(friendId)];
    if (existing) {
      if (existing.route) map.removeLayer(existing.route);
      for (const m of existing.markers || []) map.removeLayer(m);
    }

    const classes = await fetchFriendClasses(friendId, activeDate);
    if (!classes || classes.length === 0) return;

    const now = getNow();
    const renderable = [];
    for (const c of classes) {
      const window = getClassWindowFromObj(c);
      if (!window) continue;
      if (window.end <= now) continue;
      const lat = Number(c.latitude);
      const lng = Number(c.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue;
      renderable.push(Object.assign({ lat, lng }, c));
    }

    if (!renderable.length) return;

    const targetClass = computeFriendTargetClass(renderable);
    const targetId = targetClass ? String(targetClass.event_id) : null;
    const avatarIcon = createFriendAvatarIcon(friendMeta?.avatarUrl, color);

    const routeCoords = [];
    const markers = [];

    for (const entry of renderable) {
      const key = `${entry.event_name || ''}||${entry.date || ''}||${entry.start_time || ''}||${entry.end_time || ''}||${entry.location_display || ''}`;
      routeCoords.push([entry.lat, entry.lng]);

      if (userKeys && userKeys.has(key)) {
        continue;
      }

      const isTarget = targetId && String(entry.event_id) === targetId;
      const marker = L.marker([entry.lat, entry.lng], {
        icon: avatarIcon,
        zIndexOffset: isTarget ? 1200 : 800,
      }).addTo(map).bindPopup(buildFriendPopupHtml(friendMeta, entry));
      markers.push(marker);
    }

    let route = null;
    if (routeCoords.length > 1) {
      route = L.polyline(routeCoords, { color: color, weight: 3, opacity: 0.9 }).addTo(map);
    }

    friendOverlays[String(friendId)] = { markers, route, color };
  }

  async function updateFriendOverlays() {
    if (selectedFriends.size === 0) return;
    const activeDate = computeActiveDate();
    const userKeys = buildUserClassKeySet(activeDate);

    for (const [fid, friendMeta] of selectedFriends.entries()) {
      const id = String(fid);
      if (friendOverlays[id]) {
        continue;
      }

      const color = friendMeta?.color || getRandomColor();
      await renderOverlayForFriend(id, friendMeta, color, activeDate, userKeys);
    }

    for (const overlayFriendId of Object.keys(friendOverlays)) {
      if (!selectedFriends.has(overlayFriendId)) {
        removeFriendOverlay(overlayFriendId);
      }
    }
  }

  function wireFriendListSelection() {
    const list = document.querySelectorAll('.friend-on-campus');
    if (!list) return;
    list.forEach((el) => {
      const fid = el.getAttribute('data-friend-id');
      if (!fid) return;
      el.addEventListener('click', (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const key = String(fid);
        const selected = el.classList.toggle('selected');
        if (selected) {
          const avatarImg = el.querySelector("img.friend-avatar");
          const friendNameEl = el.querySelector(".friend-name");
          const accentColor = getRandomColor();
          selectedFriends.set(key, {
            friendId: key,
            avatarUrl: avatarImg ? avatarImg.getAttribute("src") : "/static/uploads/default.jpg",
            friendName: friendNameEl ? friendNameEl.textContent.trim() : "Friend",
            color: accentColor,
          });
          el.style.setProperty("--friend-accent", accentColor);
          updateFriendOverlays().catch(() => {});
        } else {
          selectedFriends.delete(key);
          el.style.removeProperty("--friend-accent");
          removeFriendOverlay(key);
        }
      });
      el.addEventListener('keydown', (ev) => {
        if (ev.key !== 'Enter' && ev.key !== ' ') return;
        ev.preventDefault();
        el.click();
      });
    });
  }

  function isOnlineClass(classData) {
    const searchableText = `${classData?.event_name || ""} ${classData?.location_display || ""} ${classData?.building_name || ""}`.toLowerCase();
    return /\bonline\b|\bvirtual\b|\bremote\b|\bzoom\b|\bteams\b|\bwebex\b|\bcollaborate\b/.test(searchableText);
  }

  function decorateOnlineClasses() {
    if (!classItemElements.length) {
      return;
    }

    for (const classItem of classItemElements) {
      const eventId = classItem.dataset.eventId;
      if (!eventId) {
        continue;
      }

      const classData = classDataById.get(String(eventId));
      if (!classData || !isOnlineClass(classData)) {
        continue;
      }

      classItem.classList.add("has-online-icon", "is-online");
      if (classItem.querySelector(".event-online-icon")) {
        continue;
      }

      const icon = document.createElement("span");
      icon.className = "event-online-icon";
      icon.setAttribute("title", "Online class");
      icon.setAttribute("aria-label", "Online class");
      icon.innerHTML = onlineBadgeSvg;
      classItem.appendChild(icon);
    }
  }

  function renderFriendAttendees(classItem, classData) {
    if (!classItem || !classData) {
      return;
    }

    const existing = classItem.querySelector(".event-attendees");
    if (existing) {
      existing.remove();
    }

    const attendees = Array.isArray(classData.friend_attendees) ? classData.friend_attendees : [];
    if (attendees.length === 0) {
      classItem.classList.remove("has-attendees");
      return;
    }

    classItem.classList.add("has-attendees");

    const wrapper = document.createElement("div");
    wrapper.className = "event-attendees";

    const label = document.createElement("div");
    label.className = "event-attendees-label";
    label.textContent = `${attendees.length} friend${attendees.length === 1 ? "" : "s"} attending`;

    const avatars = document.createElement("div");
    avatars.className = "event-attendees-avatars";

    const baseCount = 5;
    const visibleCount = attendees.length > baseCount ? baseCount : attendees.length;

    for (let i = 0; i < visibleCount; i += 1) {
      const attendee = attendees[i] || {};
      const avatar = attendee.avatar || "default.jpg";
      const img = document.createElement("img");
      img.className = "event-attendee-avatar";
      img.src = `/static/uploads/${avatar}`;
      img.alt = attendee.username ? `${attendee.username}'s avatar` : "Friend avatar";
      avatars.appendChild(img);
    }

    if (attendees.length > baseCount) {
      const overflowCount = attendees.length - baseCount;
      const overflowAttendee = attendees[Math.min(baseCount, attendees.length - 1)] || {};
      const overflowAvatar = overflowAttendee.avatar || "default.jpg";

      const overflow = document.createElement("div");
      overflow.className = "event-attendee-avatar is-overflow";
      overflow.style.setProperty("--avatar-url", `url('/static/uploads/${overflowAvatar}')`);

      const overflowText = document.createElement("span");
      overflowText.className = "event-attendee-overflow-text";
      overflowText.textContent = `+${overflowCount}`;
      overflow.appendChild(overflowText);

      avatars.appendChild(overflow);
    }

    wrapper.appendChild(label);
    wrapper.appendChild(avatars);
    classItem.appendChild(wrapper);
  }

  function decorateFriendAttendees() {
    if (!classItemElements.length) {
      return;
    }

    for (const classItem of classItemElements) {
      const eventId = classItem.dataset.eventId;
      if (!eventId) {
        continue;
      }

      const classData = classDataById.get(String(eventId));
      renderFriendAttendees(classItem, classData);
    }
  }

  function addMarkerForClass(classData, options = {}) {
    const { openPopup = false, allowOnline = false } = options;
    const isOnline = isOnlineClass(classData);

    if (isOnline && !allowOnline) {
      return null;
    }

    if (isOnline) {
      const marker = L.marker([fallbackLocation.lat, fallbackLocation.lng], { icon: onlineMarkerIcon })
        .addTo(map)
        .bindPopup(`${popupHtml(classData)}<div style="margin-top: 6px; font-size: 12px;">Map coordinates unavailable for this class.</div>`);
      activeMarkers.push(marker);

      if (openPopup) {
        marker.openPopup();
        map.setView([fallbackLocation.lat, fallbackLocation.lng], 17);
      }

      return marker;
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

  function getCurrentOrNextClassData(options = {}) {
    const { includeOnline = true } = options;
    const now = getNow();
    let currentClass = null;
    let nextClass = null;

    for (const classData of classesData) {
      if (!includeOnline && isOnlineClass(classData)) {
        continue;
      }

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

  function getRenderableClassEntries() {
    const entries = [];
    const activeDate = computeActiveDate();

    for (const classData of classesData) {
      if (!classData || classData.date !== activeDate) {
        continue;
      }
      if (isOnlineClass(classData)) {
        continue;
      }

      const window = getClassWindow(classData);
      if (!window) {
        continue;
      }

      const lat = Number(classData.latitude);
      const lng = Number(classData.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
        continue;
      }

      entries.push({ classData, start: window.start, lat, lng });
    }

    entries.sort((a, b) => a.start - b.start);
    console.debug("[map activeDate]", { activeDate, entriesCount: entries.length });
    return entries;
  }

  function renderDefaultMapView() {
    viewedDay = null;
    updateStopSelectingButton();
    clearMarkers();
    clearRouteLine();

    const renderableEntries = getRenderableClassEntries();

    // Compute the target (gold) class from the single-day renderable entries
    const now = getNow();
    let currentEntry = null;
    let nextEntry = null;
    for (const entry of renderableEntries) {
      const window = getClassWindow(entry.classData);
      if (!window) continue;
      if (window.start <= now && now < window.end) {
        if (!currentEntry || window.start < currentEntry.start) {
          currentEntry = { start: window.start, entry };
        }
        continue;
      }
      if (window.start > now) {
        if (!nextEntry || window.start < nextEntry.start) {
          nextEntry = { start: window.start, entry };
        }
      }
    }

    const targetClass = currentEntry ? currentEntry.entry.classData : nextEntry ? nextEntry.entry.classData : null;
    const targetId = targetClass ? String(targetClass.event_id) : null;
    const blueEntries = targetId
      ? renderableEntries.filter((entry) => String(entry.classData.event_id) !== targetId)
      : renderableEntries;

    let focusLatLng = null;
    let goldMarkerData = null;
    const viewCoords = [];

    if (targetClass) {
      const lat = Number(targetClass.latitude);
      const lng = Number(targetClass.longitude);

      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        goldMarkerData = {
          lat,
          lng,
          popup: popupHtml(targetClass),
        };
      } else {
        goldMarkerData = {
          lat: fallbackLocation.lat,
          lng: fallbackLocation.lng,
          popup: `${popupHtml(targetClass)}<div style="margin-top: 6px; font-size: 12px;">Map coordinates unavailable for this class.</div>`,
        };
      }
    }

    for (const entry of blueEntries) {
      const marker = L.marker([entry.lat, entry.lng])
        .addTo(map)
        .bindPopup(popupHtml(entry.classData));
      activeMarkers.push(marker);
      viewCoords.push([entry.lat, entry.lng]);
    }

    if (goldMarkerData) {
      const marker = L.marker([goldMarkerData.lat, goldMarkerData.lng], { icon: goldMarkerIcon })
        .addTo(map)
        .bindPopup(goldMarkerData.popup);
      activeMarkers.push(marker);
      marker.setZIndexOffset(1000);
      focusLatLng = marker.getLatLng();
      viewCoords.unshift([goldMarkerData.lat, goldMarkerData.lng]);
    }

    if (routesEnabled) {
      const routeCoords = [];
      if (goldMarkerData) {
        routeCoords.push([goldMarkerData.lat, goldMarkerData.lng]);
      }
      for (const entry of blueEntries) {
        routeCoords.push([entry.lat, entry.lng]);
      }

      if (routeCoords.length > 1) {
        activeRouteLine = L.polyline(routeCoords, {
          color: "#5f8dff",
          weight: 3,
          opacity: 0.8,
          dashArray: "4 6",
          lineCap: "round",
          lineJoin: "round",
          className: "route-line",
        }).addTo(map);
      }

      console.debug("[map routes]", {
        routesEnabled,
        targetEventId: targetId,
        routePointCount: routeCoords.length,
        bluePointCount: blueEntries.length,
      });
    }

    if (routesEnabled && viewCoords.length > 1) {
      const bounds = L.latLngBounds(viewCoords);
      map.fitBounds(bounds.pad(0.22), { maxZoom: 16 });
      return;
    }

    if (focusLatLng) {
      map.setView(focusLatLng, 17);
      return;
    }

    if (blueEntries.length > 0) {
      const bounds = L.latLngBounds(blueEntries.map((entry) => [entry.lat, entry.lng]));
      map.fitBounds(bounds.pad(0.2));
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

    // Determine the day's target (gold) class from the single-day entries
    const renderableEntries = getRenderableClassEntries();
    const now = getNow();
    let currentEntry = null;
    let nextEntry = null;
    for (const entry of renderableEntries) {
      const window = getClassWindow(entry.classData);
      if (!window) continue;
      if (window.start <= now && now < window.end) {
        if (!currentEntry || window.start < currentEntry.start) {
          currentEntry = { start: window.start, entry };
        }
        continue;
      }
      if (window.start > now) {
        if (!nextEntry || window.start < nextEntry.start) {
          nextEntry = { start: window.start, entry };
        }
      }
    }

    const targetClass = currentEntry ? currentEntry.entry.classData : nextEntry ? nextEntry.entry.classData : null;
    const targetId = targetClass ? String(targetClass.event_id) : null;
    const isTargetClass = targetId && String(classData.event_id) === targetId && !isOnlineClass(classData);

    selectedEventId = classData.event_id;
    updateClassHighlights();
    updateStopSelectingButton();

    clearMarkers();
    clearRouteLine();
    if (isTargetClass) {
      const lat = Number(classData.latitude);
      const lng = Number(classData.longitude);

      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        const marker = L.marker([lat, lng], { icon: goldMarkerIcon })
          .addTo(map)
          .bindPopup(popupHtml(classData))
          .openPopup();
        activeMarkers.push(marker);
        map.setView([lat, lng], 17);
        return;
      }

      const fallbackMarker = L.marker([fallbackLocation.lat, fallbackLocation.lng], { icon: goldMarkerIcon })
        .addTo(map)
        .bindPopup(`${popupHtml(classData)}<div style="margin-top: 6px; font-size: 12px;">Map coordinates unavailable for this class.</div>`)
        .openPopup();
      activeMarkers.push(fallbackMarker);
      map.setView([fallbackLocation.lat, fallbackLocation.lng], 17);
      return;
    }

    const marker = addMarkerForClass(classData, { openPopup: true, allowOnline: true });
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
    if (selectedEventId === null && viewedDay === null) {
      return;
    }

    selectedEventId = null;
    if (viewedDay !== null) {
      viewedDay = null;
      renderDefaultMapView();
    } else {
      updateClassHighlights();
      updateStopSelectingButton();
      renderDefaultMapView();
    }
  }

  function viewDayOnMap(targetDate) {
    // View all classes for a specific day
    // If day has only online classes, show the first online class
    // Otherwise show the day's map with routes as normal

    viewedDay = targetDate;
    updateStopSelectingButton();

    selectedEventId = null;
    updateClassHighlights();

    clearMarkers();
    clearRouteLine();

    // Get all classes for the target date
    const dayClasses = classesData.filter((c) => c && c.date === targetDate);
    if (!dayClasses.length) {
      map.setView([fallbackLocation.lat, fallbackLocation.lng], 17);
      return;
    }

    // Separate online and non-online classes
    const onlineClasses = dayClasses.filter((c) => isOnlineClass(c));
    const nonOnlineClasses = dayClasses.filter((c) => !isOnlineClass(c));

    // If all classes are online, show first online class and return
    if (nonOnlineClasses.length === 0 && onlineClasses.length > 0) {
      const firstOnline = onlineClasses[0];
      const marker = L.marker([fallbackLocation.lat, fallbackLocation.lng], { icon: onlineMarkerIcon })
        .addTo(map)
        .bindPopup(`${popupHtml(firstOnline)}<div style="margin-top: 6px; font-size: 12px;">Map coordinates unavailable for this class.</div>`)
        .openPopup();
      activeMarkers.push(marker);
      map.setView([fallbackLocation.lat, fallbackLocation.lng], 17);
      return;
    }

    // Otherwise, show the day's non-online classes with routes
    const renderableEntries = [];
    for (const classData of nonOnlineClasses) {
      const window = getClassWindow(classData);
      if (!window) continue;

      const lat = Number(classData.latitude);
      const lng = Number(classData.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue;

      renderableEntries.push({ classData, start: window.start, lat, lng });
    }

    renderableEntries.sort((a, b) => a.start - b.start);

    // Find the target (gold) class
    const now = getNow();
    let currentEntry = null;
    let nextEntry = null;
    for (const entry of renderableEntries) {
      const window = getClassWindow(entry.classData);
      if (!window) continue;
      if (window.start <= now && now < window.end) {
        if (!currentEntry || window.start < currentEntry.start) {
          currentEntry = { start: window.start, entry };
        }
        continue;
      }
      if (window.start > now) {
        if (!nextEntry || window.start < nextEntry.start) {
          nextEntry = { start: window.start, entry };
        }
      }
    }

    const targetClass = currentEntry ? currentEntry.entry.classData : nextEntry ? nextEntry.entry.classData : null;
    const targetId = targetClass ? String(targetClass.event_id) : null;
    const blueEntries = targetId
      ? renderableEntries.filter((entry) => String(entry.classData.event_id) !== targetId)
      : renderableEntries;

    let focusLatLng = null;
    let goldMarkerData = null;
    const viewCoords = [];

    if (targetClass) {
      const lat = Number(targetClass.latitude);
      const lng = Number(targetClass.longitude);

      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        goldMarkerData = { lat, lng, popup: popupHtml(targetClass) };
      } else {
        goldMarkerData = {
          lat: fallbackLocation.lat,
          lng: fallbackLocation.lng,
          popup: `${popupHtml(targetClass)}<div style="margin-top: 6px; font-size: 12px;">Map coordinates unavailable for this class.</div>`,
        };
      }
    }

    for (const entry of blueEntries) {
      const marker = L.marker([entry.lat, entry.lng])
        .addTo(map)
        .bindPopup(popupHtml(entry.classData));
      activeMarkers.push(marker);
      viewCoords.push([entry.lat, entry.lng]);
    }

    if (goldMarkerData) {
      const marker = L.marker([goldMarkerData.lat, goldMarkerData.lng], { icon: goldMarkerIcon })
        .addTo(map)
        .bindPopup(goldMarkerData.popup);
      activeMarkers.push(marker);
      marker.setZIndexOffset(1000);
      focusLatLng = marker.getLatLng();
      viewCoords.unshift([goldMarkerData.lat, goldMarkerData.lng]);
    }

    if (routesEnabled) {
      const routeCoords = [];
      if (goldMarkerData) {
        routeCoords.push([goldMarkerData.lat, goldMarkerData.lng]);
      }
      for (const entry of blueEntries) {
        routeCoords.push([entry.lat, entry.lng]);
      }

      if (routeCoords.length > 1) {
        activeRouteLine = L.polyline(routeCoords, {
          color: "#5f8dff",
          weight: 3,
          opacity: 0.8,
          dashArray: "4 6",
          lineCap: "round",
          lineJoin: "round",
          className: "route-line",
        }).addTo(map);
      }
    }

    if (routesEnabled && viewCoords.length > 1) {
      const bounds = L.latLngBounds(viewCoords);
      map.fitBounds(bounds.pad(0.22), { maxZoom: 16 });
      return;
    }

    if (focusLatLng) {
      map.setView(focusLatLng, 17);
      return;
    }

    if (blueEntries.length > 0) {
      const bounds = L.latLngBounds(blueEntries.map((entry) => [entry.lat, entry.lng]));
      map.fitBounds(bounds.pad(0.2));
      return;
    }

    map.setView([fallbackLocation.lat, fallbackLocation.lng], 17);
  }

  function wireDayGroupClicks() {
    const dayGroupHeaders = document.querySelectorAll(".group-title[data-view-day]");
    for (const header of dayGroupHeaders) {
      const dayValue = header.dataset.viewDay;
      if (!dayValue) continue;

      let targetDate = dayValue;
      if (dayValue === "today") {
        const now = getNow();
        targetDate = now.toISOString().slice(0, 10);
      } else if (dayValue === "tomorrow") {
        const now = getNow();
        const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
        targetDate = tomorrow.toISOString().slice(0, 10);
      }

      header.addEventListener("click", () => {
        viewDayOnMap(targetDate);
      });

      header.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") {
          return;
        }

        event.preventDefault();
        viewDayOnMap(targetDate);
      });
    }
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

  if (routesToggleButton) {
    L.DomEvent.disableClickPropagation(routesToggleButton);
    L.DomEvent.disableScrollPropagation(routesToggleButton);
    routesToggleButton.addEventListener("click", toggleRoutes);
  }

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
  updateRoutesToggleLabel();

  if (classesToggleButton) {
    classesToggleButton.addEventListener("click", toggleClassesPanel);
  }

  parseFixedNow();
  parseClassesData();
  decorateFriendAttendees();
  decorateOnlineClasses();
  wireClassSelection();
  wireDayGroupClicks();
  wireFriendListSelection();
  renderDefaultMapView();
})();
