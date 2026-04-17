(() => {
  const deleteModeToggle = document.getElementById("deleteModeToggle");
  const eventsTableBody = document.getElementById("eventsTableBody");

  if (!deleteModeToggle || !eventsTableBody) {
    return;
  }

  const trashIcon =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3.75A2.75 2.75 0 0 0 6.25 6.5V7H4.5a.75.75 0 0 0 0 1.5h.95l.74 10.14A2.75 2.75 0 0 0 8.94 21h6.12a2.75 2.75 0 0 0 2.75-2.36l.74-10.14h.95a.75.75 0 0 0 0-1.5h-1.75v-.5A2.75 2.75 0 0 0 15 3.75H9Zm5.5 3.25h-5V6.5c0-.69.56-1.25 1.25-1.25h2.5c.69 0 1.25.56 1.25 1.25V7Zm-7.25 1.5h9.5l-.72 9.86a1.25 1.25 0 0 1-1.24 1.14H8.71a1.25 1.25 0 0 1-1.24-1.14L7.25 8.5Zm3.25 2a.75.75 0 0 0-.75.75v5.25a.75.75 0 0 0 1.5 0v-5.25a.75.75 0 0 0-.75-.75Zm3 0a.75.75 0 0 0-.75.75v5.25a.75.75 0 0 0 1.5 0v-5.25a.75.75 0 0 0-.75-.75Z"/></svg>';

  function setDeleteMode(isEnabled) {
    document.body.classList.toggle("delete-mode-enabled", isEnabled);
    deleteModeToggle.classList.toggle("active", isEnabled);
    deleteModeToggle.setAttribute("aria-pressed", String(isEnabled));
    deleteModeToggle.textContent = isEnabled ? "Stop deleting" : "Delete events";
  }

  function ensureEmptyState() {
    const eventRows = eventsTableBody.querySelectorAll(".event-row");
    const existingEmptyRow = eventsTableBody.querySelector("[data-empty-row]");

    if (eventRows.length > 0) {
      if (existingEmptyRow) {
        existingEmptyRow.remove();
      }
      return;
    }

    if (!existingEmptyRow) {
      const emptyRow = document.createElement("tr");
      emptyRow.dataset.emptyRow = "true";
      emptyRow.className = "empty-row";
      emptyRow.innerHTML = '<td colspan="6" class="empty-state">No classes imported yet.</td>';
      eventsTableBody.appendChild(emptyRow);
    }
  }

  function createEventRow(event) {
    const row = document.createElement("tr");
    row.className = "event-row";
    row.dataset.eventId = event.event_id;
    row.innerHTML = `
      <td>${event.event_name}</td>
      <td>${event.day_display}</td>
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

  async function loadEventsFromDatabase() {
    console.log("[Events] Fetching events from database...");
    try {
      const response = await fetch("/api/events/me", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        console.error("[Events] Failed to fetch events:", response.status);
        return;
      }

      const data = await response.json();
      console.log("[Events] Fetched", data.events.length, "events from database");
      
      // Clear existing rows
      eventsTableBody.innerHTML = "";
      
      if (data.events.length === 0) {
        ensureEmptyState();
      } else {
        data.events.forEach(event => {
          const row = createEventRow(event);
          eventsTableBody.appendChild(row);
        });
      }

      // Wire up delete buttons
      wireEventDeleteButtons();
    } catch (error) {
      console.error("[Events] Error loading events:", error);
      eventsTableBody.innerHTML = '<tr class="empty-row"><td colspan="6" class="empty-state">Error loading events</td></tr>';
    }
  }

  async function deleteEvent(eventRow, eventId) {
    console.log(`[Delete] Sending DELETE request for event_id: ${eventId}`);
    const response = await fetch(`/api/events/${eventId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    console.log(`[Delete] Response status: ${response.status}`);
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      console.error(`[Delete] Error response:`, payload);
      throw new Error(payload.error || "Unable to delete event.");
    }

    const result = await response.json();
    console.log(`[Delete] Success:`, result);
    
    eventRow.remove();
    ensureEmptyState();
    
    // Re-fetch from database to ensure UI is in sync
    console.log("[Delete] Re-fetching events from database to verify deletion...");
    await loadEventsFromDatabase();
  }

  function wireEventDeleteButtons() {
    eventsTableBody.querySelectorAll(".event-row").forEach((eventRow) => {
      const eventId = eventRow.dataset.eventId;
      const deleteButton = eventRow.querySelector(".event-delete-btn");

      if (!eventId || !deleteButton) {
        return;
      }

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

  deleteModeToggle.addEventListener("click", () => {
    const isEnabled = !document.body.classList.contains("delete-mode-enabled");
    setDeleteMode(isEnabled);
  });

  setDeleteMode(false);
  
  // Load events from database on page load
  loadEventsFromDatabase();
})();
