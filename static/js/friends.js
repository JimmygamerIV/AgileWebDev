function showTab(tabName) {
    const tabIds = ["all-friends", "friend-requests", "add-friend"];
    tabIds.forEach((id) => {
        const panel = document.getElementById(id);
        if (panel) {
            panel.classList.add("hidden");
        }
    });

    const tabs = document.querySelectorAll(".tab");
    tabs.forEach((tab) => {
        tab.classList.toggle("active", tab.dataset.tab === tabName);
    });

    const activePanel = document.getElementById(tabName);
    if (activePanel) {
        activePanel.classList.remove("hidden");
    }
}

function getCsrfToken() {
    const tokenInput = document.getElementById("csrfToken");
    return tokenInput ? tokenInput.value : "";
}

function getRequestDot() {
    const requestsTab = document.querySelector('.tab[data-tab="friend-requests"]');
    if (!requestsTab) {
        return null;
    }
    let dot = requestsTab.querySelector(".dot");
    if (!dot) {
        dot = document.createElement("span");
        dot.className = "dot";
        requestsTab.appendChild(dot);
    }
    return dot;
}

function updateRequestDot() {
    const incomingList = document.getElementById("incoming-list");
    const incomingCount = incomingList
        ? incomingList.querySelectorAll(".friend-item").length
        : 0;
    const dot = getRequestDot();
    if (!dot) {
        return;
    }
    dot.classList.toggle("is-hidden", incomingCount === 0);
}

function ensureEmptyMessage(listEl, message) {
    if (!listEl) {
        return;
    }
    const hasItems = listEl.querySelectorAll(".friend-item").length > 0;
    const emptyMessage = listEl.querySelector(".empty-message");

    if (hasItems && emptyMessage) {
        emptyMessage.remove();
        return;
    }

    if (!hasItems && !emptyMessage) {
        const messageEl = document.createElement("p");
        messageEl.className = "empty-message";
        messageEl.style.fontStyle = "italic";
        messageEl.style.color = "#888";
        messageEl.textContent = message;
        listEl.appendChild(messageEl);
    }
}

const FRIENDS_DEBUG = new URLSearchParams(window.location.search).get("debug") === "1";

function logDebug(message, details) {
    if (!FRIENDS_DEBUG) {
        return;
    }
    if (typeof details === "undefined") {
        console.log(`[friends] ${message}`);
        return;
    }
    console.log(`[friends] ${message}`, details);
}

function closeAllMenus(exceptMenu) {
    document.querySelectorAll(".dropdown-menu").forEach((menu) => {
        if (menu !== exceptMenu) {
            menu.classList.remove("is-open");
        }
    });
}

function toggleMenu(button) {
    const menu = button.nextElementSibling;
    if (!menu) {
        return;
    }

    const friendItem = button.closest(".friend-item");
    const favouriteItem = menu.querySelector('[data-action="favourite"]');
    if (friendItem && favouriteItem) {
        const isFavourite = friendItem.classList.contains("is-favourite");
        favouriteItem.textContent = isFavourite ? "Unfavourite friend" : "Favourite friend";
    }

    closeAllMenus(menu);
    menu.classList.toggle("is-open");
    logDebug("menu visibility", {
        open: menu.classList.contains("is-open"),
        display: window.getComputedStyle(menu).display,
    });
}

function wireFriendMenus() {
    const friendsList = document.getElementById("friends-list");
    if (!friendsList) {
        logDebug("friends-list not found");
        return;
    }

    logDebug("wireFriendMenus", {
        buttons: friendsList.querySelectorAll(".three-dots-btn").length,
        menus: friendsList.querySelectorAll(".dropdown-menu").length,
    });

    friendsList.addEventListener("click", (event) => {
        const menuButton = event.target.closest(".three-dots-btn");
        if (menuButton) {
            event.preventDefault();
            event.stopPropagation();
            logDebug("three-dots click", menuButton);
            toggleMenu(menuButton);
            return;
        }

        const menuItem = event.target.closest(".menu-item");
        if (menuItem) {
            event.preventDefault();
            event.stopPropagation();
            logDebug("menu item click", menuItem.dataset.action);

            const friendItem = menuItem.closest(".friend-item");
            const friendId = friendItem ? friendItem.getAttribute("data-friend-id") : null;
            const action = menuItem.dataset.action;

            if (action === "remove") {
                const friendName = friendItem
                    ? friendItem.querySelector(".friend-nickname")?.textContent?.trim()
                    : "Friend";
                openRemoveConfirm(friendId, friendName || "Friend");
            } else if (action === "favourite") {
                favouriteFriend(friendId, friendItem);
            }

            const menu = menuItem.closest(".dropdown-menu");
            if (menu) {
                menu.classList.remove("is-open");
            }
        }
    });

    document.addEventListener("click", (event) => {
        if (!event.target.closest(".friend-actions")) {
            closeAllMenus(null);
        }
    });
}

function filterFriends() {
    const searchInput = document.getElementById("friends-search");
    const filter = (searchInput?.value || "").toLowerCase();
    const friendItems = document.querySelectorAll("#friends-list .friend-item");

    friendItems.forEach((item) => {
        const username = item.getAttribute("data-username") || "";
        item.style.display = username.includes(filter) ? "" : "none";
    });
}

function filterRequests() {
    const searchInput = document.getElementById("requests-search");
    const filter = (searchInput?.value || "").toLowerCase();
    const requestItems = document.querySelectorAll("#friend-requests .friend-item");

    requestItems.forEach((item) => {
        const username = item.getAttribute("data-username") || "";
        item.style.display = username.includes(filter) ? "" : "none";
    });
}

function updateFavouriteVisual(friendItem, isFavourite) {
    if (!friendItem) {
        return;
    }

    const nickname = friendItem.querySelector(".friend-nickname");
    const star = nickname ? nickname.querySelector(".star-icon") : null;

    if (isFavourite) {
        if (!star && nickname) {
            const starEl = document.createElement("span");
            starEl.className = "star-icon";
            starEl.textContent = "⭐";
            nickname.insertBefore(starEl, nickname.firstChild);
        }
        friendItem.classList.add("is-favourite");
    } else {
        if (star) {
            star.remove();
        }
        friendItem.classList.remove("is-favourite");
    }

    sortFriendsList();
}

function sortFriendsList() {
    const list = document.getElementById("friends-list");
    if (!list) {
        return;
    }

    const items = Array.from(list.querySelectorAll(".friend-item"));
    items.sort((a, b) => {
        const aFav = a.classList.contains("is-favourite");
        const bFav = b.classList.contains("is-favourite");
        if (aFav !== bFav) {
            return aFav ? -1 : 1;
        }
        const aName = a.querySelector(".friend-nickname")?.textContent?.toLowerCase() || "";
        const bName = b.querySelector(".friend-nickname")?.textContent?.toLowerCase() || "";
        return aName.localeCompare(bName);
    });

    items.forEach((item) => list.appendChild(item));
}

function favouriteFriend(friendId, friendItem) {
    if (!friendId) {
        return;
    }

    const body = new URLSearchParams({
        friend_id: friendId,
        csrf_token: getCsrfToken(),
    });

    fetch("/favourite_friend", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data && typeof data.is_favourite !== "undefined") {
                updateFavouriteVisual(friendItem, data.is_favourite);
            }
        })
        .catch(() => {
            // Ignore network errors here.
        });
}

function openRemoveConfirm(friendId, friendName) {
    if (!friendId) {
        return;
    }

    if (confirm(`Are you sure you want to remove ${friendName}?`)) {
        removeFriend(friendId);
    }
}

function removeFriend(friendId) {
    const body = new URLSearchParams({
        friend_id: friendId,
        csrf_token: getCsrfToken(),
    });

    fetch("/remove_friend", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
    })
        .then((response) => response.json())
        .then((data) => {
            if (!data || !data.success) {
                return;
            }
            const friendItem = document.querySelector(`[data-friend-id="${friendId}"]`);
            if (friendItem) {
                friendItem.remove();
            }
            const friendsList = document.getElementById("friends-list");
            ensureEmptyMessage(friendsList, "You have no friends added yet.");
        })
        .catch(() => {
            // Ignore network errors here.
        });
}

function createFriendItem(friend) {
    if (!friend || !friend.user_id) {
        return null;
    }

    const item = document.createElement("div");
    item.className = "friend-item";
    item.dataset.username = (friend.username || "").toLowerCase();
    item.dataset.friendId = friend.user_id;

    const profileUrl = `/profile/${encodeURIComponent(friend.username || "")}`;
    const avatar = friend.avatar || "default.jpg";
    const nickname = friend.nickname || friend.username || "";

    item.innerHTML = `
        <img class="avatar" src="/static/uploads/${avatar}" alt="${friend.username}'s avatar" />
        <div class="friend-info">
            <a class="friend-profile-link" href="${profileUrl}">
                <div class="friend-nickname">${nickname}</div>
                <div class="friend-username">@${friend.username}</div>
            </a>
        </div>
        <div class="friend-actions">
            <button class="three-dots-btn" type="button" aria-label="Friend actions">⋯</button>
            <div class="dropdown-menu">
                <button type="button" class="menu-item" data-action="favourite">
                    Favourite friend
                </button>
                <button type="button" class="menu-item remove-item" data-action="remove">
                    Remove friend
                </button>
            </div>
        </div>
    `;

    return item;
}

function createOutgoingRequestItem(request) {
    if (!request || !request.request_id || !request.user) {
        return null;
    }

    const item = document.createElement("div");
    item.className = "friend-item";
    item.dataset.username = (request.user.username || "").toLowerCase();
    item.dataset.requestId = request.request_id;

    const avatar = request.user.avatar || "default.jpg";
    const nickname = request.user.nickname || request.user.username || "";

    item.innerHTML = `
        <img class="avatar" src="/static/uploads/${avatar}" alt="${request.user.username}'s avatar" />
        <div class="friend-info">
            <a class="friend-profile-link" href="/profile/${encodeURIComponent(request.user.username)}">
                <div class="friend-nickname">${nickname}</div>
                <div class="friend-username">@${request.user.username}</div>
            </a>
        </div>
        <div class="request-actions">
            <button type="button" class="cancel-btn">Cancel</button>
        </div>
    `;

    const cancelButton = item.querySelector(".cancel-btn");
    if (cancelButton) {
        cancelButton.addEventListener("click", () => {
            cancelRequest(request.request_id);
        });
    }

    return item;
}

function acceptRequest(requestId, senderId) {
    const body = new URLSearchParams({
        request_id: requestId,
        sender_id: senderId,
        csrf_token: getCsrfToken(),
    });

    fetch("/accept_request", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
    })
        .then((response) => response.json())
        .then((data) => {
            if (!data || !data.success) {
                return;
            }
            const requestItem = document.querySelector(`[data-request-id="${requestId}"]`);
            if (requestItem) {
                requestItem.remove();
            }

            const incomingList = document.getElementById("incoming-list");
            ensureEmptyMessage(incomingList, "No incoming friend requests.");
            updateRequestDot();

            if (data.friend) {
                const friendsList = document.getElementById("friends-list");
                const newFriendItem = createFriendItem(data.friend);
                if (friendsList && newFriendItem) {
                    friendsList.appendChild(newFriendItem);
                    ensureEmptyMessage(friendsList, "You have no friends added yet.");
                    sortFriendsList();
                }
            }
        })
        .catch(() => {
            // Ignore network errors here.
        });
}

function declineRequest(requestId) {
    const body = new URLSearchParams({
        request_id: requestId,
        csrf_token: getCsrfToken(),
    });

    fetch("/reject_request", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
    })
        .then((response) => response.json())
        .then((data) => {
            if (!data || !data.success) {
                return;
            }
            const requestItem = document.querySelector(`[data-request-id="${requestId}"]`);
            if (requestItem) {
                requestItem.remove();
            }
            const incomingList = document.getElementById("incoming-list");
            ensureEmptyMessage(incomingList, "No incoming friend requests.");
            updateRequestDot();
        })
        .catch(() => {
            // Ignore network errors here.
        });
}

function cancelRequest(requestId) {
    const body = new URLSearchParams({
        request_id: requestId,
        csrf_token: getCsrfToken(),
    });

    fetch("/cancel_request", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
    })
        .then((response) => response.json())
        .then((data) => {
            if (!data || !data.success) {
                return;
            }
            const requestItem = document.querySelector(`[data-request-id="${requestId}"]`);
            if (requestItem) {
                requestItem.remove();
            }
            const outgoingList = document.getElementById("outgoing-list");
            ensureEmptyMessage(outgoingList, "No outgoing friend requests.");
        })
        .catch(() => {
            // Ignore network errors here.
        });
}

let selectedUserId = null;
let selectedUserData = null;

function searchUsers() {
    const searchInput = document.getElementById("add-friend-search");
    const query = (searchInput?.value || "").trim();
    const results = document.getElementById("search-results");

    if (!results) {
        return;
    }

    if (query.length < 2) {
        results.innerHTML = '<p style="font-style: italic; color: #888">Search for a user to add as a friend.</p>';
        selectedUserId = null;
        return;
    }

    fetch(`/search_users?q=${encodeURIComponent(query)}`)
        .then((response) => response.json())
        .then((users) => {
            results.innerHTML = "";
            selectedUserId = null;
            selectedUserData = null;

            if (!Array.isArray(users) || users.length === 0) {
                results.innerHTML = '<p style="font-style: italic; color: #888">No users found.</p>';
                return;
            }

            users.forEach((user) => {
                const item = document.createElement("div");
                item.className = "friend-item search-result";
                item.dataset.userId = user.user_id;
                item.innerHTML = `
                    <img class="avatar" src="/static/uploads/${user.avatar}" alt="${user.username}'s avatar" />
                    <div class="friend-info">
                        <div class="friend-nickname">${user.nickname || user.username}</div>
                        <div class="friend-username">@${user.username}</div>
                    </div>
                `;

                item.addEventListener("click", () => {
                    document.querySelectorAll(".search-result").forEach((row) => {
                        row.classList.remove("selected");
                    });
                    item.classList.add("selected");
                    selectedUserId = String(user.user_id);
                    selectedUserData = user;
                });

                results.appendChild(item);
            });
        })
        .catch(() => {
            results.innerHTML = '<p style="font-style: italic; color: #888">Search failed. Try again.</p>';
        });
}

function sendFriendRequest() {
    const searchInput = document.getElementById("add-friend-search");
    const username = (searchInput?.value || "").trim();

    const payload = { csrf_token: getCsrfToken() };
    if (selectedUserId) {
        payload.user_id = selectedUserId;
    } else if (username) {
        payload.username = username;
    } else {
        alert("Enter a username to send a request.");
        return;
    }

    const body = new URLSearchParams(payload);

    fetch("/send_friend_request", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
    })
        .then((response) => response.json())
        .then((data) => {
            if (!data || !data.success) {
                return;
            }
            if (searchInput) {
                searchInput.value = "";
            }
            const results = document.getElementById("search-results");
            if (results) {
                results.innerHTML = '<p style="font-style: italic; color: #888">Friend request sent.</p>';
            }

            const outgoingList = document.getElementById("outgoing-list");
            const requestPayload = {
                request_id: data.request_id,
                user: data.user || selectedUserData,
            };
            const newRequestItem = createOutgoingRequestItem(requestPayload);
            if (outgoingList && newRequestItem) {
                outgoingList.appendChild(newRequestItem);
                ensureEmptyMessage(outgoingList, "No outgoing friend requests.");
            }

            selectedUserId = null;
            selectedUserData = null;
        })
        .catch(() => {
            // Ignore network errors here.
        });
}

function initFriendsPage() {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get("tab") || "all-friends";

    showTab(tab);
    wireFriendMenus();
    sortFriendsList();
    updateRequestDot();
    ensureEmptyMessage(document.getElementById("friends-list"), "You have no friends added yet.");
    ensureEmptyMessage(document.getElementById("incoming-list"), "No incoming friend requests.");
    ensureEmptyMessage(document.getElementById("outgoing-list"), "No outgoing friend requests.");

    logDebug("init complete", { tab });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initFriendsPage);
} else {
    initFriendsPage();
}
