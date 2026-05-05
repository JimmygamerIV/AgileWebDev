(() => {
  const deleteModeToggle = document.getElementById("deleteModeToggle");
  const eventsTableBody = document.getElementById("eventsTableBody");

  if (!deleteModeToggle || !eventsTableBody) {
    return;
  }

  const trashIcon =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3.75A2.75 2.75 0 0 0 6.25 6.5V7H4.5a.75.75 0 0 0 0 1.5h.95l.74 10.14A2.75 2.75 0 0 0 8.94 21h6.12a2.75 2.75 0 0 0 2.75-2.36l.74-10.14h.95a.75.75 0 0 0 0-1.5h-1.75v-.5A2.75 2.75 0 0 0 15 3.75H9Zm5.5 3.25h-5V6.5c0-.69.56-1.25 1.25-1.25h2.5c.69 0 1.25.56 1.25 1.25V7Zm-7.25 1.5h9.5l-.72 9.86a1.25 1.25 0 0 1-1.24 1.14H8.71a1.25 1.25 0 0 1-1.24-1.14L7.25 8.5Zm3.25 2a.75.75 0 0 0-.75.75v5.25a.75.75 0 0 0 1.5 0v-5.25a.75.75 0 0 0-.75-.75Zm3 0a.75.75 0 0 0-.75.75v5.25a.75.75 0 0 0 1.5 0v-5.25a.75.75 0 0 0-.75-.75Z"/></svg>';

// Start of timetable field
  let currentWeekOffset = 0;
  let allCachedEvents = []; 

  const listViewBtn = document.getElementById("listViewBtn");
  const gridViewBtn = document.getElementById("gridViewBtn");
  const listViewContainer = document.getElementById("listViewContainer");
  const gridViewContainer = document.getElementById("gridViewContainer");
  
  const prevWeekBtn = document.getElementById("prevWeekBtn");
  const nextWeekBtn = document.getElementById("nextWeekBtn");
  const currentWeekRangeLabel = document.getElementById("currentWeekRangeLabel");
  const dynamicGridEventsContainer = document.getElementById("dynamicGridEventsContainer");


  function getWeekRangeDates(offset) {
      const today = new Date();
      const dayOfWeek = today.getDay();
      const distanceToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
      
      const targetMonday = new Date(today);
      targetMonday.setDate(today.getDate() + distanceToMonday + offset * 7);
      
      const targetFriday = new Date(targetMonday);
      targetFriday.setDate(targetMonday.getDate() + 4);

      return {
          monday: targetMonday,
          friday: targetFriday,
          mondayStr: formatDate(targetMonday),
          fridayStr: formatDate(targetFriday),
          displayStr: `${targetMonday.toLocaleDateString('en-GB', {day: 'numeric', month: 'short'})} - ${targetFriday.toLocaleDateString('en-GB', {day: 'numeric', month: 'short'})}`
      };
  }

  function formatDate(dateObj) {
      const yyyy = dateObj.getFullYear();
      const mm = String(dateObj.getMonth() + 1).padStart(2, '0');
      const dd = String(dateObj.getDate()).padStart(2, '0');
      return `${yyyy}-${mm}-${dd}`;
  }

  function timeToGridRow(timeStr) {
      if (!timeStr) return 1;
      const hour = parseInt(timeStr.split(":")[0], 10);
      const TIMETABLE_START_HOUR = 8;
      return hour - TIMETABLE_START_HOUR + 1;
  }

  function renderVisualGrid() {
      if (!dynamicGridEventsContainer) return;
      dynamicGridEventsContainer.innerHTML = ""; 

      const range = getWeekRangeDates(currentWeekOffset);
      if (currentWeekRangeLabel) {
          currentWeekRangeLabel.textContent = `📅 Week Range: ${range.displayStr}`;
      }

      const filteredEvents = allCachedEvents.filter(ev => {
          return ev.date >= range.mondayStr && ev.date <= range.fridayStr;
      });

      const dayToColMap = { "Monday": 2, "Tuesday": 3, "Wednesday": 4, "Thursday": 5, "Friday": 6 };
      const collisionMap = {};

      const preparedEvents = filteredEvents.map(ev => {
          const col = dayToColMap[ev.day_display] || dayToColMap[ev.day] || 2; 
          const startRow = timeToGridRow(ev.start_time);
          const endRow = timeToGridRow(ev.end_time);

          return {
              name: ev.event_name,
              location: ev.location,
              col: col,
              startRow: startRow,
              endRow: endRow,
              subColIndex: 0,
              totalSiblings: 1
          };
      });

      preparedEvents.forEach(ev => {
          for (let r = ev.startRow; r < ev.endRow; r++) {
              const slotKey = `${ev.col}_${r}`;
              if (!collisionMap[slotKey]) collisionMap[slotKey] = [];
              collisionMap[slotKey].push(ev);
          }
      });

      Object.values(collisionMap).forEach(evtList => {
          if (evtList.length > 1) {
              evtList.forEach((ev, idx) => {
                  ev.totalSiblings = Math.max(ev.totalSiblings, evtList.length);
                  ev.subColIndex = Math.max(ev.subColIndex, idx);
              });
          }
      });

      const seenIds = new Set();
      preparedEvents.forEach(ev => {
          const uniqueId = `${ev.name}_${ev.col}_${ev.startRow}`;
          if (seenIds.has(uniqueId)) return;
          seenIds.add(uniqueId);

          const widthPercent = 100 / ev.totalSiblings;
          const leftPercent = ev.subColIndex * widthPercent;

          const block = document.createElement("div");
          block.className = "grid-event-block";
          block.style.gridColumn = ev.col;
          block.style.gridRow = `${ev.startRow} / ${ev.endRow}`;
          block.style.width = `${widthPercent}%`;
          block.style.marginLeft = `${leftPercent}%`;

          block.innerHTML = `
              <div class="block-content">
                <span class="block-title" title="${ev.name}">${ev.name}</span>
                <span class="block-loc">📍 ${ev.location || 'Unknown'}</span>
              </div>
          `;
          dynamicGridEventsContainer.appendChild(block);
      });
  }


  async function loadEventsFromDatabase() {
    console.log("[Events] Fetching events from database...");
    try {
      const response = await fetch("/api/events/me", {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        console.error("[Events] Failed to fetch events:", response.status);
        return;
      }

      const data = await response.json();
      allCachedEvents = data.events || [];
      console.log("[Events] Fetched", allCachedEvents.length, "events from database");
      
      eventsTableBody.innerHTML = "";
      if (allCachedEvents.length === 0) {
        ensureEmptyState();
      } else {
        allCachedEvents.forEach(event => {
          const row = createEventRow(event);
          eventsTableBody.appendChild(row);
        });
      }

      if (gridViewContainer && gridViewContainer.style.display === "block") {
          renderVisualGrid();
      }

      wireEventDeleteButtons();
    } catch (error) {
      console.error("[Events] Error loading events:", error);
      eventsTableBody.innerHTML = '<tr class="empty-row"><td colspan="6" class="empty-state">Error loading events</td></tr>';
    }
  }
// end of timetable field


  function setDeleteMode(isEnabled) {
    document.body.classList.toggle("delete-mode-enabled", isEnabled);
    deleteModeToggle.classList.toggle("active", isEnabled);
    deleteModeToggle.setAttribute("aria-pressed", String(isEnabled));
    deleteModeToggle.textContent = isEnabled ? "Stop deleting" : "Delete events";

    const deleteAllBtn = document.getElementById("deleteAllBtn");
    if (deleteAllBtn) {
        deleteAllBtn.style.display = isEnabled ? "inline-block" : "none";
    }
  }

  function ensureEmptyState() {
    const eventRows = eventsTableBody.querySelectorAll(".event-row");
    const existingEmptyRow = eventsTableBody.querySelector("[data-empty-row]");

    if (eventRows.length > 0) {
      if (existingEmptyRow) existingEmptyRow.remove();
      return;
    }

    if (!existingEmptyRow) {
      const emptyRow = document.createElement("tr");
      emptyRow.dataset.emptyRow = "true";
      emptyRow.className = "empty-row";
      emptyRow.innerHTML = '<td colspan="7" class="empty-state">No classes imported yet.</td>';
      eventsTableBody.appendChild(emptyRow);
    }
  }

  function createEventRow(event) {
    const row = document.createElement("tr");
    row.className = "event-row";
    row.dataset.eventId = event.event_id;
    row.innerHTML = `
      <td>${event.event_name}</td>
      <td>${event.day_display || event.day}</td>
      <td>${event.date}</td>
      <td>${event.start_time}</td>
      <td>${event.end_time}</td>
      <td>${event.location}</td>
      <td class="delete-cell">
        <button
          type="button"
          class="event-delete-btn"
          aria-label="Delete ${event.event_name}"
          title="Delete event"
        ></button>
      </td>
    `;
    return row;
  }

  async function deleteEvent(eventRow, eventId) {
    const csrfInput = document.querySelector('input[name="csrf_token"]');
    const csrfToken = csrfInput ? csrfInput.value : "";

    const response = await fetch(`/api/events/${eventId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({})
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || "Unable to delete event.");
    }

    eventRow.remove();
    allCachedEvents = allCachedEvents.filter(ev => String(ev.event_id) !== String(eventId));
    
    ensureEmptyState();
    if (gridViewContainer && gridViewContainer.style.display === "block") {
        renderVisualGrid();
    }
  }

  function wireEventDeleteButtons() {
    eventsTableBody.querySelectorAll(".event-row").forEach((eventRow) => {
      const eventId = eventRow.dataset.eventId;
      const deleteButton = eventRow.querySelector(".event-delete-btn");

      if (!eventId || !deleteButton) return;

      deleteButton.innerHTML = trashIcon;
      deleteButton.addEventListener("click", async () => {
        try {
          deleteButton.disabled = true;
          await deleteEvent(eventRow, eventId);
        } catch (error) {
          window.alert(error instanceof Error ? error.message : "Unable to delete event.");
          deleteButton.disabled = false;
        }
      });
    });
  }


  if (listViewBtn && gridViewBtn && listViewContainer && gridViewContainer) {

      listViewBtn.addEventListener("click", () => {
          listViewBtn.classList.add("active");
          gridViewBtn.classList.remove("active");
          listViewContainer.style.display = "block";
          gridViewContainer.style.display = "none";
      });


      gridViewBtn.addEventListener("click", () => {
          gridViewBtn.classList.add("active");
          listViewBtn.classList.remove("active");
          listViewContainer.style.display = "none";
          gridViewContainer.style.display = "block"; 
          renderVisualGrid();
      });
  }


  if (prevWeekBtn && nextWeekBtn) {
      prevWeekBtn.addEventListener("click", () => {
          currentWeekOffset -= 1;
          renderVisualGrid();
      });

      nextWeekBtn.addEventListener("click", () => {
          currentWeekOffset += 1;
          renderVisualGrid();
      });
  }

  deleteModeToggle.addEventListener("click", () => {
    const isEnabled = !document.body.classList.contains("delete-mode-enabled");
    setDeleteMode(isEnabled);
  });

  const deleteAllBtn = document.getElementById("deleteAllBtn");
  if (deleteAllBtn) {
      deleteAllBtn.addEventListener("click", async () => {
          if (!confirm("Are you sure you want to delete all events?")) return;
          const rows = eventsTableBody.querySelectorAll(".event-row");
          for (const row of rows) {
              const eventId = row.dataset.eventId;
              if (eventId) await deleteEvent(row, eventId);
          }
      });
  }

  setDeleteMode(false);
  loadEventsFromDatabase();
})();