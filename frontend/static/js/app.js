const state = {
  token: localStorage.getItem("smartchat_token") || "",
  me: null,
  conversations: [],
  activeConversationId: null,
  activeConversation: null,
  notifications: [],
  expandedNotificationGroups: new Set(),
  expandedConversationGroups: new Set(["other"]),
  rules: [],
  automationHistory: [],
  userDirectory: [],
  groupSetupConversationId: null,
  groupMemberPickerConversationId: null,
  groupCreateInFlight: false,
  admin: {
    stats: null,
    users: [],
    spam: [],
    diagnostics: [],
    logs: [],
    automationLogs: [],
  },
  ws: null,
  typingTimer: null,
};

const PROFILE_BIO_LIMIT = 40;
const NOTIFICATION_GROUP_LABELS = {
  urgent: "Pilne",
  announcement: "Ogloszenia",
  offer: "Oferty",
  question: "Pytania",
  private: "Prywatne",
  spam: "Spam",
  system: "Systemowe",
  automation: "Automatyzacje",
  other: "Inne",
};
const NOTIFICATION_GROUP_ORDER = [
  "urgent",
  "spam",
  "announcement",
  "offer",
  "question",
  "private",
  "system",
  "automation",
  "other",
];
const NOTIFICATION_TYPE_LABELS = {
  message: "wiadomosc",
  system: "system",
  automation: "automatyzacja",
};
const CONVERSATION_GROUP_LABELS = {
  private: "Prywatne",
  work: "Sluzbowe",
  other: "Inne",
};
const CONVERSATION_GROUP_ORDER = ["private", "work", "other"];

const elements = {};

document.addEventListener("DOMContentLoaded", () => {
  cacheElements();
  bindEvents();
  updateRuleActivityMode();
  if (state.token) {
    bootstrapApp();
  } else {
    showAuth();
  }
});

function cacheElements() {
  const ids = [
    "auth-screen",
    "app-screen",
    "login-form",
    "register-form",
    "logout-button",
    "refresh-button",
    "conversation-list",
    "conversation-count",
    "conversation-search",
    "message-list",
    "message-form",
    "message-input",
    "conversation-title",
    "conversation-subtitle",
    "typing-indicator",
    "current-user-name",
    "current-user-meta",
    "avatar-badge",
    "notification-list",
    "refresh-notifications-button",
    "profile-form",
    "profile-username",
    "profile-status",
    "profile-bio",
    "profile-bio-hint",
    "profile-bio-count",
    "profile-avatar",
    "profile-visible",
    "profile-web-push",
    "rule-form",
    "rule-trigger-type",
    "rule-always-active",
    "rule-activity-block",
    "rule-activity-hint",
    "rule-schedule-fields",
    "rule-active-from",
    "rule-active-to",
    "rules-list",
    "rules-count",
    "automation-history",
    "refresh-automation-history",
    "open-compose-modal",
    "compose-modal",
    "close-compose-modal",
    "group-member-modal",
    "close-group-member-modal",
    "user-profile-modal",
    "close-user-profile-modal",
    "user-profile-avatar",
    "user-profile-name",
    "user-profile-bio",
    "user-search-form",
    "user-search-input",
    "user-search-results",
    "group-create-form",
    "group-title-input",
    "group-create-button",
    "group-setup-panel",
    "group-setup-heading",
    "group-setup-filter-form",
    "group-setup-filter-input",
    "group-setup-close",
    "group-setup-count",
    "group-setup-results",
    "group-management-panel",
    "group-rename-form",
    "group-rename-input",
    "group-rename-button",
    "group-member-toggle-button",
    "group-member-picker",
    "group-member-search-form",
    "group-member-search-input",
    "group-member-search-results",
    "group-delete-panel",
    "group-delete-button",
    "group-leave-panel",
    "group-leave-button",
    "group-available-count",
    "group-members-count",
    "group-members-list",
    "admin-tab-button",
    "admin-refresh-button",
    "admin-stats",
    "admin-users",
    "admin-spam",
    "admin-diagnostics",
    "admin-logs",
    "message-search-input",
    "run-search-button",
    "search-results",
    "toast-container",
    "app-title",
  ];
  ids.forEach((id) => {
    elements[id] = document.getElementById(id);
  });
  elements.navButtons = [...document.querySelectorAll(".nav-button")];
}

function bindEvents() {
  elements["login-form"].addEventListener("submit", handleLogin);
  elements["register-form"].addEventListener("submit", handleRegister);
  elements["logout-button"].addEventListener("click", handleLogout);
  elements["refresh-button"].addEventListener("click", bootstrapApp);
  elements["message-form"].addEventListener("submit", handleSendMessage);
  elements["message-input"].addEventListener("input", handleTyping);
  elements["conversation-search"].addEventListener("input", renderConversations);
  elements["refresh-notifications-button"].addEventListener("click", loadNotifications);
  elements["profile-form"].addEventListener("submit", saveProfile);
  elements["profile-bio"].addEventListener("input", updateProfileBioHint);
  elements["rule-form"].addEventListener("submit", createRule);
  elements["rule-trigger-type"].addEventListener("change", updateRuleActivityMode);
  elements["rule-always-active"].addEventListener("change", updateRuleActivityMode);
  elements["refresh-automation-history"].addEventListener("click", loadAutomationHistory);
  elements["open-compose-modal"].addEventListener("click", openComposeModal);
  elements["close-compose-modal"].addEventListener("click", closeComposeModal);
  elements["compose-modal"].addEventListener("click", handleComposeModalBackdrop);
  elements["close-group-member-modal"].addEventListener("click", closeGroupMemberPicker);
  elements["group-member-modal"].addEventListener("click", handleGroupMemberModalBackdrop);
  elements["close-user-profile-modal"].addEventListener("click", closeUserProfileModal);
  elements["user-profile-modal"].addEventListener("click", handleUserProfileModalBackdrop);
  document.addEventListener("keydown", handleGlobalKeydown);
  elements["user-search-form"].addEventListener("submit", searchUsers);
  elements["group-create-form"].addEventListener("submit", handleGroupCreateSubmit);
  elements["group-rename-form"].addEventListener("submit", renameGroupConversation);
  elements["group-member-toggle-button"].addEventListener("click", toggleGroupMemberPicker);
  elements["group-member-search-form"].addEventListener("submit", searchUsersForActiveGroup);
  elements["group-delete-button"].addEventListener("click", deleteGroupConversation);
  elements["group-leave-button"].addEventListener("click", leaveGroupConversation);
  elements["admin-refresh-button"].addEventListener("click", loadAdminPanel);
  elements["run-search-button"].addEventListener("click", runGlobalSearch);
  elements.navButtons.forEach((button) =>
    button.addEventListener("click", () => activateView(button.dataset.view)),
  );
  elements["message-list"].addEventListener("click", handleMessageAction);
  elements["rules-list"].addEventListener("click", handleRuleAction);
  elements["notification-list"].addEventListener("click", handleNotificationAction);
  elements["admin-users"].addEventListener("click", handleAdminUserAction);
  elements["user-search-results"].addEventListener("click", handleUserSearchAction);
  elements["group-member-search-results"].addEventListener("click", handleGroupMemberSearchAction);
  elements["group-members-list"].addEventListener("click", handleGroupMemberListAction);
  elements["conversation-list"].addEventListener("click", handleConversationListAction);
}

async function bootstrapApp() {
  try {
    const me = await api("/api/v1/users/me");
    state.me = me;
    elements["app-title"].textContent = `SmartChat | ${me.username}`;
    await Promise.all([
      loadConversations(),
      loadNotifications(),
      loadRules(),
      loadAutomationHistory(),
      loadUserDirectory(),
    ]);
    renderProfile();
    connectWebSocket();
    if (state.me.role === "admin") {
      elements["admin-tab-button"].classList.remove("hidden");
      await loadAdminPanel();
    } else {
      elements["admin-tab-button"].classList.add("hidden");
    }
    showApp();
  } catch (error) {
    console.error(error);
    state.token = "";
    localStorage.removeItem("smartchat_token");
    showToast("Sesja wygasła lub logowanie nie powiodło się.", true);
    showAuth();
  }
}

function showAuth() {
  closeComposeModal();
  closeGroupMemberPicker();
  closeUserProfileModal();
  state.expandedConversationGroups = new Set(["other"]);
  elements["conversation-search"].value = "";
  elements["auth-screen"].classList.remove("hidden");
  elements["app-screen"].classList.add("hidden");
}

function showApp() {
  elements["auth-screen"].classList.add("hidden");
  elements["app-screen"].classList.remove("hidden");
  renderCurrentUser();
  renderGroupSetupPanel();
  renderGroupManagementPanel();
}

function activateView(viewId) {
  document.querySelectorAll(".view-panel").forEach((panel) => panel.classList.remove("active-view"));
  elements.navButtons.forEach((button) => button.classList.remove("active"));
  document.getElementById(viewId).classList.add("active-view");
  document.querySelector(`.nav-button[data-view="${viewId}"]`)?.classList.add("active");
}

function syncModalOpenState() {
  const anyModalOpen =
    !elements["compose-modal"].classList.contains("hidden") ||
    !elements["group-member-modal"].classList.contains("hidden") ||
    !elements["user-profile-modal"].classList.contains("hidden");
  document.body.classList.toggle("modal-open", anyModalOpen);
}

async function openComposeModal() {
  elements["user-search-input"].value = "";
  elements["user-search-results"].innerHTML = "";
  await loadUserDirectory();
  elements["compose-modal"].classList.remove("hidden");
  elements["compose-modal"].setAttribute("aria-hidden", "false");
  syncModalOpenState();
  elements["user-search-input"]?.focus();
}

function closeComposeModal() {
  elements["compose-modal"].classList.add("hidden");
  elements["compose-modal"].setAttribute("aria-hidden", "true");
  elements["user-search-input"].value = "";
  elements["user-search-results"].innerHTML = "";
  syncModalOpenState();
}

function handleComposeModalBackdrop(event) {
  if (event.target === elements["compose-modal"]) {
    closeComposeModal();
  }
}

function handleGroupMemberModalBackdrop(event) {
  if (event.target === elements["group-member-modal"]) {
    closeGroupMemberPicker();
  }
}

function openUserProfileModal(user) {
  if (!user) {
    return;
  }
  if (user.avatar_url) {
    elements["user-profile-avatar"].innerHTML = `<img src="${escapeHtml(user.avatar_url)}" alt="${escapeHtml(user.username)}" />`;
  } else {
    elements["user-profile-avatar"].textContent = getUserInitials(user.username);
  }
  elements["user-profile-name"].textContent = user.username;
  elements["user-profile-bio"].textContent = user.bio?.trim() || "Ten uzytkownik nie uzupelnil jeszcze bio.";
  elements["user-profile-modal"].classList.remove("hidden");
  elements["user-profile-modal"].setAttribute("aria-hidden", "false");
  syncModalOpenState();
}

function closeUserProfileModal() {
  elements["user-profile-modal"].classList.add("hidden");
  elements["user-profile-modal"].setAttribute("aria-hidden", "true");
  syncModalOpenState();
}

function handleUserProfileModalBackdrop(event) {
  if (event.target === elements["user-profile-modal"]) {
    closeUserProfileModal();
  }
}

function handleGlobalKeydown(event) {
  if (event.key !== "Escape") {
    return;
  }
  if (!elements["user-profile-modal"].classList.contains("hidden")) {
    closeUserProfileModal();
    return;
  }
  if (!elements["group-member-modal"].classList.contains("hidden")) {
    closeGroupMemberPicker();
    return;
  }
  if (!elements["compose-modal"].classList.contains("hidden")) {
    closeComposeModal();
  }
}

async function api(url, options = {}) {
  const config = { ...options };
  config.headers = config.headers || {};
  if (!(config.body instanceof FormData)) {
    config.headers["Content-Type"] = config.headers["Content-Type"] || "application/json";
  }
  if (state.token) {
    config.headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(url, config);
  if (response.status === 204) {
    return null;
  }
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = payload?.detail || payload || "Wystąpił błąd.";
    throw new Error(detail);
  }
  return payload;
}

async function handleLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  try {
    const result = await api("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(formData.entries())),
    });
    state.token = result.access_token;
    localStorage.setItem("smartchat_token", state.token);
    showToast("Zalogowano pomyślnie.");
    await bootstrapApp();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  try {
    await api("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(formData.entries())),
    });
    showToast("Konto zostało utworzone. Możesz się zalogować.");
    form.reset();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleLogout() {
  try {
    if (state.token) {
      await api("/api/v1/auth/logout", { method: "POST" });
    }
  } catch (error) {
    console.warn(error);
  }
  if (state.ws) {
    state.ws.close();
  }
  state.token = "";
  state.me = null;
  state.expandedNotificationGroups = new Set();
  state.expandedConversationGroups = new Set(["other"]);
  state.groupSetupConversationId = null;
  state.groupMemberPickerConversationId = null;
  localStorage.removeItem("smartchat_token");
  showAuth();
}

async function loadConversations() {
  const previousActiveId = state.activeConversationId;
  state.conversations = await api("/api/v1/conversations");
  renderConversations();
  if (
    previousActiveId &&
    !state.conversations.some((conversation) => conversation.id === previousActiveId)
  ) {
    clearActiveConversation();
  }
  if (!state.activeConversationId && state.conversations.length > 0) {
    await openConversation(state.conversations[0].id);
  }
}

function renderConversations() {
  const query = elements["conversation-search"].value.trim().toLowerCase();
  const visibleConversations = state.conversations.filter((conversation) => {
    if (!query) {
      return true;
    }
    return getConversationSearchText(conversation).includes(query);
  });

  elements["conversation-count"].textContent = String(visibleConversations.length);
  elements["conversation-list"].innerHTML = "";

  const groups = groupConversationsByCategory(visibleConversations);
  groups.forEach((group) => {
    const groupNode = document.createElement("details");
    groupNode.className = "notification-group conversation-group";
    groupNode.dataset.group = group.key;
    groupNode.open = state.expandedConversationGroups.has(group.key);
    groupNode.innerHTML = `
      <summary class="notification-group-summary">
        <span>${group.label}</span>
        <span class="notification-group-meta">
          <span class="pill">${group.items.length}</span>
        </span>
      </summary>
      <div class="notification-group-content"></div>
    `;

    groupNode.addEventListener("toggle", () => {
      if (groupNode.open) {
        state.expandedConversationGroups.add(group.key);
      } else {
        state.expandedConversationGroups.delete(group.key);
      }
    });

    const groupContent = groupNode.querySelector(".notification-group-content");
    if (group.items.length === 0) {
      const emptyLabel = query
        ? "Brak konwersacji pasujacych do wyszukiwania."
        : "Brak konwersacji w tej kategorii.";
      groupContent.innerHTML = `<div class="empty-state">${emptyLabel}</div>`;
    } else {
      group.items.forEach((conversation) => {
        const title = getConversationTitle(conversation);
        const participants = conversation.participants
          .filter((participant) => participant.user.id !== state.me.id)
          .map((participant) => participant.user.username)
          .join(", ");
        const currentCategory = getConversationGroupKey(conversation);
        const item = document.createElement("article");
        item.className = `conversation-item ${conversation.id === state.activeConversationId ? "active" : ""}`;
        item.innerHTML = `
          <div class="conversation-item-header">
            <div class="conversation-title">
              <span>${title}</span>
              <span class="pill">${conversation.type}</span>
            </div>
            <details class="conversation-menu">
              <summary class="ghost-button conversation-menu-trigger">Przenies</summary>
              <div class="conversation-menu-panel">
                ${renderConversationCategoryActions(conversation.id, currentCategory)}
              </div>
            </details>
          </div>
          <div class="conversation-meta">${participants || "Rozmowa wlasna"}</div>
        `;
        item.addEventListener("click", (event) => {
          if (
            event.target.closest(".conversation-menu") ||
            event.target.closest("[data-action='move-conversation']")
          ) {
            return;
          }
          openConversation(conversation.id);
        });
        groupContent.appendChild(item);
      });
    }

    elements["conversation-list"].appendChild(groupNode);
  });
}

function getConversationSearchText(conversation) {
  const title = getConversationTitle(conversation);
  const participants = conversation.participants
    .filter((participant) => participant.user.id !== state.me?.id)
    .map((participant) => `${participant.user.username} ${participant.user.email || ""}`.trim())
    .join(" ");
  return `${title} ${participants}`.trim().toLowerCase();
}

function renderConversationCategoryActions(conversationId, currentCategory) {
  return CONVERSATION_GROUP_ORDER.map((category) => {
    const label = CONVERSATION_GROUP_LABELS[category] || category;
    const activeClass = category === currentCategory ? " active" : "";
    return `
      <button
        type="button"
        class="conversation-menu-option${activeClass}"
        data-action="move-conversation"
        data-id="${conversationId}"
        data-category="${category}"
      >
        ${label}
      </button>
    `;
  }).join("");
}

function getConversationGroupKey(conversation) {
  const currentParticipant = conversation.participants.find(
    (participant) => participant.user_id === state.me?.id,
  );
  return currentParticipant?.display_category || "other";
}

function groupConversationsByCategory(conversations) {
  const grouped = new Map(CONVERSATION_GROUP_ORDER.map((key) => [key, []]));
  conversations.forEach((conversation) => {
    const key = getConversationGroupKey(conversation);
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key).push(conversation);
  });

  return CONVERSATION_GROUP_ORDER.map((key) => ({
    key,
    label: CONVERSATION_GROUP_LABELS[key] || key,
    items: grouped.get(key) || [],
  }));
}

function getConversationTitle(conversation) {
  if (conversation.title) {
    return conversation.title;
  }
  const otherParticipant = getDirectConversationPeer(conversation);
  return otherParticipant ? otherParticipant.user.username : `Konwersacja #${conversation.id}`;
}

async function handleConversationListAction(event) {
  const moveButton = event.target.closest("[data-action='move-conversation']");
  if (!moveButton) {
    return;
  }

  event.preventDefault();
  event.stopPropagation();

  const conversationId = Number(moveButton.dataset.id);
  const category = moveButton.dataset.category;
  try {
    const updatedConversation = await api(`/api/v1/conversations/${conversationId}/category`, {
      method: "PATCH",
      body: JSON.stringify({ category }),
    });
    updateConversationInState(updatedConversation);
    moveButton.closest("details")?.removeAttribute("open");
    renderConversations();
    showToast(`Przeniesiono konwersacje do kategorii ${CONVERSATION_GROUP_LABELS[category]}.`);
  } catch (error) {
    showToast(error.message, true);
  }
}

function updateConversationInState(updatedConversation) {
  state.conversations = state.conversations.map((conversation) =>
    conversation.id === updatedConversation.id ? updatedConversation : conversation,
  );
  if (state.activeConversation?.id === updatedConversation.id) {
    state.activeConversation = {
      ...state.activeConversation,
      participants: updatedConversation.participants,
      title: updatedConversation.title,
      type: updatedConversation.type,
      created_by_id: updatedConversation.created_by_id,
      updated_at: updatedConversation.updated_at,
      last_message_at: updatedConversation.last_message_at,
    };
  }
}

function getDirectConversationPeer(conversation) {
  if (!conversation) {
    return null;
  }
  return conversation.participants.find((participant) => participant.user.id !== state.me?.id) || null;
}

function getKnownUserById(userId) {
  if (!userId) {
    return null;
  }
  if (state.me?.id === userId) {
    return state.me;
  }
  const directoryUser = state.userDirectory.find((user) => user.id === userId);
  if (directoryUser) {
    return directoryUser;
  }
  const participantUser = state.activeConversation?.participants?.find(
    (participant) => participant.user.id === userId,
  )?.user;
  if (participantUser) {
    return participantUser;
  }
  const sender = state.activeConversation?.messages?.find((message) => message.sender.id === userId)?.sender;
  return sender || null;
}

async function openConversation(conversationId) {
  state.activeConversationId = conversationId;
  state.activeConversation = await api(`/api/v1/conversations/${conversationId}`);
  renderConversations();
  renderActiveConversation();
  await api(`/api/v1/conversations/${conversationId}/read`, { method: "POST" });
}

function renderActiveConversation() {
  const conversation = state.activeConversation;
  if (!conversation) {
    elements["conversation-title"].textContent = "Wybierz konwersację";
    elements["conversation-subtitle"].textContent = "Lista uczestników i statusów pojawi się tutaj.";
    elements["message-list"].innerHTML = `<div class="empty-state">Wybierz rozmowę z listy po lewej stronie.</div>`;
    renderGroupSetupPanel();
    renderGroupManagementPanel();
    return;
  }
  elements["conversation-title"].textContent = getConversationTitle(conversation);
  if (isGroupConversation(conversation)) {
    elements["conversation-subtitle"].textContent = "";
  } else {
    const otherParticipant = getDirectConversationPeer(conversation);
    elements["conversation-subtitle"].textContent = otherParticipant
      ? `Status: ${otherParticipant.user.status}`
      : "";
  }
  renderMessages();
  renderGroupSetupPanel();
  renderGroupManagementPanel();
}

function renderMessages() {
  const list = elements["message-list"];
  list.innerHTML = "";
  const messages = state.activeConversation?.messages || [];
  const groupConversation = isGroupConversation(state.activeConversation);
  if (messages.length === 0) {
    list.innerHTML = `<div class="empty-state">Ta rozmowa nie zawiera jeszcze wiadomości.</div>`;
    return;
  }

  messages.forEach((message) => {
    const row = document.createElement("div");
    const bubble = document.createElement("article");
    const classes = ["message-bubble"];
    const isOwnMessage = message.sender_id === state.me.id;
    const canEdit = canEditMessage(message, state.me);
    const showSender = groupConversation && !isOwnMessage;
    row.className = `message-row ${isOwnMessage ? "self" : "other"}`;
    if (isOwnMessage) classes.push("self");
    if (message.is_spam) classes.push("spam");
    if (message.is_automated) classes.push("automated");
    bubble.className = classes.join(" ");
    bubble.innerHTML = `
      <div class="message-topline">
        ${showSender ? `<strong class="message-author">${escapeHtml(message.sender.username)}</strong>` : ""}
        <span class="message-meta">${formatDateTime(message.created_at)}</span>
      </div>
      <div class="message-body">${escapeHtml(message.content)}</div>
      <div class="message-status-row">
        <span class="status-badge ${message.is_spam ? "spam" : ""}">${message.category}</span>
        ${isOwnMessage ? `<span class="status-badge">${formatMessageStatus(message.status)}</span>` : ""}
        ${message.is_automated ? `<span class="status-badge">auto</span>` : ""}
        ${message.is_edited ? `<span class="status-badge">edytowana</span>` : ""}
      </div>
      <div class="message-meta">${message.spam_reason || message.analysis_metadata.classification_reasons?.join(" ") || ""}</div>
      ${
        canEdit
          ? `<div class="message-actions">
               <button class="ghost-button" data-action="edit-message" data-id="${message.id}">Edytuj</button>
               <button class="ghost-button" data-action="delete-message" data-id="${message.id}">Usuń</button>
             </div>`
          : ""
      }
    `;
    if (!isOwnMessage) {
      row.appendChild(createMessageAvatar(message.sender));
    }
    row.appendChild(bubble);
    list.appendChild(row);
  });
  list.scrollTop = list.scrollHeight;
}

function createMessageAvatar(sender) {
  const avatar = document.createElement("button");
  avatar.type = "button";
  avatar.className = "message-avatar";
  avatar.dataset.action = "open-user-profile";
  avatar.dataset.userId = String(sender.id);
  avatar.setAttribute("aria-label", `Otworz profil uzytkownika ${sender.username}`);
  if (sender.avatar_url) {
    avatar.innerHTML = `<img src="${escapeHtml(sender.avatar_url)}" alt="${escapeHtml(sender.username)}" />`;
  } else {
    avatar.textContent = getUserInitials(sender.username);
  }
  return avatar;
}

async function handleSendMessage(event) {
  event.preventDefault();
  if (!state.activeConversationId) {
    showToast("Najpierw wybierz konwersację.", true);
    return;
  }
  const content = elements["message-input"].value.trim();
  if (!content) return;

  try {
    const message = await api(`/api/v1/conversations/${state.activeConversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
    state.activeConversation.messages.push(message);
    renderMessages();
    elements["message-input"].value = "";
    handleTypingStop();
  } catch (error) {
    showToast(error.message, true);
  }
}

function handleTyping() {
  if (!state.ws || !state.activeConversationId) return;
  state.ws.send(
    JSON.stringify({
      type: "typing",
      conversation_id: state.activeConversationId,
      is_typing: true,
    }),
  );
  clearTimeout(state.typingTimer);
  state.typingTimer = setTimeout(handleTypingStop, 1200);
}

function handleTypingStop() {
  if (!state.ws || !state.activeConversationId) return;
  state.ws.send(
    JSON.stringify({
      type: "typing",
      conversation_id: state.activeConversationId,
      is_typing: false,
    }),
  );
}

async function handleInlineAnalysis() {
  const content = elements["message-input"].value.trim();
  if (!content) {
    showToast("Wpisz treść do analizy.", true);
    return;
  }
  return;
}

async function saveProfile(event) {
  event.preventDefault();
  const bio = elements["profile-bio"].value;
  if (bio.length > PROFILE_BIO_LIMIT) {
    showToast(`Bio moze miec maksymalnie ${PROFILE_BIO_LIMIT} znakow.`, true);
    return;
  }
  try {
    const payload = {
      username: elements["profile-username"].value,
      bio,
      avatar_url: elements["profile-avatar"].value,
      status: elements["profile-status"].value,
      privacy_settings: {
        ...state.me.privacy_settings,
        profile_visible: elements["profile-visible"].value === "true",
      },
      notification_settings: {
        ...state.me.notification_settings,
        web_push: elements["profile-web-push"].value === "true",
      },
    };
    state.me = await api("/api/v1/users/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    await loadUserDirectory();
    renderCurrentUser();
    renderProfile();
    showToast("Profil został zapisany.");
  } catch (error) {
    showToast(error.message, true);
  }
}

function renderProfile() {
  if (!state.me) return;
  elements["profile-username"].value = state.me.username || "";
  elements["profile-status"].value = state.me.status || "offline";
  elements["profile-bio"].value = state.me.bio || "";
  elements["profile-avatar"].value = state.me.avatar_url || "";
  elements["profile-visible"].value = String(state.me.privacy_settings?.profile_visible ?? true);
  elements["profile-web-push"].value = String(state.me.notification_settings?.web_push ?? true);
  updateProfileBioHint();
}

function updateProfileBioHint() {
  const bioLength = elements["profile-bio"].value.length;
  elements["profile-bio-count"].textContent = `${bioLength}/${PROFILE_BIO_LIMIT}`;
  elements["profile-bio-count"].classList.toggle("limit-reached", bioLength >= PROFILE_BIO_LIMIT);
}

async function searchUsers(event) {
  event.preventDefault();
  const query = elements["user-search-input"].value.trim();
  if (!query) return;
  try {
    const result = await api(`/api/v1/users/search?q=${encodeURIComponent(query)}`);
    renderUserSearchResults(result.items);
  } catch (error) {
    showToast(error.message, true);
  }
}

function renderUserSearchResults(users) {
  const visibleUsers = users.filter((user) => user.privacy_settings?.profile_visible !== false);
  elements["user-search-results"].innerHTML = "";
  if (!visibleUsers.length) {
    elements["user-search-results"].innerHTML = `<div class="empty-state">Brak wyników.</div>`;
    return;
  }
  visibleUsers.forEach((user) => {
    const item = document.createElement("article");
    item.className = "list-item";
    item.innerHTML = `
      <div class="conversation-title">
        <span>${user.username}</span>
        <span><span class="status-dot ${user.status}"></span>${user.status}</span>
      </div>
      <div class="conversation-meta">${user.email}</div>
      <div class="list-item-actions">
        <button class="secondary-button" data-action="start-direct" data-user-id="${user.id}">Rozpocznij rozmowę</button>
      </div>
    `;
    elements["user-search-results"].appendChild(item);
  });
}

function handleUserSearchAction(event) {
  const directButton = event.target.closest("[data-action='start-direct']");
  if (directButton) {
    createDirectConversation(Number(directButton.dataset.userId));
  }
}

async function createDirectConversation(userId) {
  try {
    const conversation = await api("/api/v1/conversations", {
      method: "POST",
      body: JSON.stringify({ type: "direct", participant_ids: [userId] }),
    });
    await loadConversations();
    await openConversation(conversation.id);
    activateView("chat-view");
    closeComposeModal();
    showToast("Rozmowa została przygotowana.");
  } catch (error) {
    showToast(error.message, true);
  }
}

function handleGroupCreateSubmit(event) {
  event?.preventDefault?.();
  event?.stopPropagation?.();
  if (state.groupCreateInFlight) {
    return false;
  }
  void createGroupConversation();
  return false;
}

window.handleGroupCreateSubmit = handleGroupCreateSubmit;

async function createGroupConversation() {
  const title = elements["group-title-input"].value.trim();
  if (!title) {
    showToast("Podaj nazwę grupy.", true);
    return;
  }

  state.groupCreateInFlight = true;
  try {
    const conversation = await api("/api/v1/conversations", {
      method: "POST",
      body: JSON.stringify({
        type: "group",
        title,
        participant_ids: [],
      }),
    });
    state.groupSetupConversationId = null;
    elements["group-title-input"].value = "";
    await loadConversations();
    await openConversation(conversation.id);
    activateView("chat-view");
    closeComposeModal();
    await toggleGroupMemberPicker();
    showToast("Czat grupowy zostal utworzony. Dodaj teraz osoby w oknie na srodku.");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    state.groupCreateInFlight = false;
  }
}

function isGroupConversation(conversation) {
  return conversation?.type === "group";
}

function canManageGroup(conversation) {
  return (
    isGroupConversation(conversation) &&
    !!state.me &&
    (conversation.created_by_id === state.me.id || state.me.role === "admin")
  );
}

function isGroupOwner(conversation) {
  return isGroupConversation(conversation) && !!state.me && conversation.created_by_id === state.me.id;
}

function isGroupMemberPickerOpen(conversation) {
  return !!conversation && state.groupMemberPickerConversationId === conversation.id;
}

function closeGroupMemberPicker() {
  state.groupMemberPickerConversationId = null;
  elements["group-member-modal"].classList.add("hidden");
  elements["group-member-modal"].setAttribute("aria-hidden", "true");
  elements["group-member-search-input"].value = "";
  elements["group-member-search-results"].innerHTML = "";
  syncModalOpenState();
}

async function toggleGroupMemberPicker() {
  const conversation = state.activeConversation;
  if (!canManageGroup(conversation)) return;

  if (isGroupMemberPickerOpen(conversation) && !elements["group-member-modal"].classList.contains("hidden")) {
    closeGroupMemberPicker();
    renderGroupManagementPanel();
    return;
  }

  state.groupMemberPickerConversationId = conversation.id;
  await loadUserDirectory();
  elements["group-member-modal"].classList.remove("hidden");
  elements["group-member-modal"].setAttribute("aria-hidden", "false");
  syncModalOpenState();
  renderGroupManagementPanel();
  renderGroupAvailableUsers(elements["group-member-search-input"].value.trim());
  elements["group-member-search-input"]?.focus();
}

function shouldShowGroupSetupPanel() {
  return false;
}

function renderGroupSetupPanel() {
  const panel = elements["group-setup-panel"];
  if (panel) {
    panel.classList.add("hidden");
  }
}

function closeGroupSetupPanel() {
  state.groupSetupConversationId = null;
}

function filterGroupSetupUsers(event) {
  event.preventDefault();
}

function legacyRenderGroupManagementPanel() {
  const panel = elements["group-management-panel"];
  const conversation = state.activeConversation;
  if (!isGroupConversation(conversation)) {
    panel.classList.add("hidden");
    elements["group-available-count"].textContent = "0";
    elements["group-member-search-results"].innerHTML = "";
    elements["group-members-list"].innerHTML = "";
    elements["group-members-count"].textContent = "0";
    return;
  }

  panel.classList.remove("hidden");
  elements["group-members-count"].textContent = String(conversation.participants.length);
  elements["group-rename-input"].value = conversation.title || "";

  const managerMode = canManageGroup(conversation);
  elements["group-rename-input"].disabled = !managerMode;
  elements["group-rename-button"].disabled = !managerMode;
  elements["group-member-search-input"].disabled = !managerMode;
  elements["group-member-search-form"].querySelector("button").disabled = !managerMode;

  if (!managerMode) {
    elements["group-available-count"].textContent = "0";
    elements["group-member-search-results"].innerHTML = `<div class="empty-state">Tylko właściciel grupy lub administrator może dodawać nowych uczestników.</div>`;
  }

  elements["group-members-list"].innerHTML = "";
  conversation.participants.forEach((participant) => {
    const isOwner = conversation.created_by_id === participant.user.id;
    const item = document.createElement("article");
    item.className = "list-item";
    item.innerHTML = `
      <div class="conversation-title">
        <span>${participant.user.username}</span>
        <span><span class="status-dot ${participant.user.status}"></span>${participant.user.status}</span>
      </div>
      <div class="conversation-meta">
        ${participant.user.email} • ${isOwner ? "właściciel grupy" : "uczestnik"}
      </div>
      ${
        managerMode && !isOwner
          ? `<button class="ghost-button" data-action="remove-group-member" data-user-id="${participant.user.id}">Usuń z grupy</button>`
          : ""
      }
    `;
    elements["group-members-list"].appendChild(item);
  });
}

async function renameGroupConversation(event) {
  event.preventDefault();
  const conversation = state.activeConversation;
  if (!isGroupConversation(conversation)) return;
  const title = elements["group-rename-input"].value.trim();
  if (!title) {
    showToast("Nazwa grupy nie może być pusta.", true);
    return;
  }
  try {
    await api(`/api/v1/conversations/${conversation.id}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
    await reloadActiveConversation();
    showToast("Nazwa grupy została zaktualizowana.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function searchUsersForActiveGroup(event) {
  event.preventDefault();
  const conversation = state.activeConversation;
  if (!isGroupConversation(conversation)) return;
  renderGroupAvailableUsers(elements["group-member-search-input"].value.trim());
}

function getAvailableUsersForActiveGroup(filterText = "") {
  const conversation = state.activeConversation;
  const existingIds = new Set((conversation?.participants || []).map((participant) => participant.user.id));
  const normalizedFilter = filterText.trim().toLowerCase();
  return state.userDirectory.filter((user) => {
    if (existingIds.has(user.id)) return false;
    if (!normalizedFilter) return true;
    return (
      user.username.toLowerCase().includes(normalizedFilter) ||
      user.email.toLowerCase().includes(normalizedFilter)
    );
  });
}

function renderGroupAvailableUsers(filterText = "") {
  const users = getAvailableUsersForActiveGroup(filterText);
  elements["group-available-count"].textContent = String(users.length);
  elements["group-member-search-results"].innerHTML = "";
  if (!users.length) {
    elements["group-member-search-results"].innerHTML = `<div class="empty-state">Brak nowych użytkowników do dodania.</div>`;
    return;
  }
  users.forEach((user) => {
    const item = document.createElement("article");
    item.className = "list-item";
    item.innerHTML = `
      <div class="conversation-title">
        <span>${user.username}</span>
        <span><span class="status-dot ${user.status}"></span>${user.status}</span>
      </div>
      <div class="conversation-meta">${user.email}</div>
      <button class="secondary-button" data-action="add-group-member" data-user-id="${user.id}">Dodaj do grupy</button>
    `;
    elements["group-member-search-results"].appendChild(item);
  });
}

async function loadUserDirectory() {
  try {
    const result = await api("/api/v1/users/directory");
    state.userDirectory = result.items.filter((user) => user.privacy_settings?.profile_visible !== false);
    renderGroupSetupPanel();
  } catch (error) {
    state.userDirectory = [];
    showToast(error.message, true);
  }
}

async function handleGroupSetupAction(event) {
  const button = event.target.closest("[data-action='add-group-member']");
  if (!button || !state.activeConversation || !shouldShowGroupSetupPanel()) return;
  const userId = Number(button.dataset.userId);
  try {
    await api(`/api/v1/conversations/${state.activeConversation.id}/participants`, {
      method: "POST",
      body: JSON.stringify({ participant_ids: [userId] }),
    });
    await reloadActiveConversation();
    renderGroupSetupPanel();
    showToast("Dodano użytkownika do nowej grupy.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleGroupMemberSearchAction(event) {
  const button = event.target.closest("[data-action='add-group-member']");
  if (!button || !state.activeConversation) return;
  const userId = Number(button.dataset.userId);
  try {
    await api(`/api/v1/conversations/${state.activeConversation.id}/participants`, {
      method: "POST",
      body: JSON.stringify({ participant_ids: [userId] }),
    });
    elements["group-member-search-input"].value = "";
    elements["group-member-search-results"].innerHTML = "";
    await reloadActiveConversation();
    state.groupMemberPickerConversationId = state.activeConversation?.id ?? null;
    showToast("Dodano użytkownika do grupy.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleGroupMemberListAction(event) {
  const profileButton = event.target.closest("[data-action='open-user-profile']");
  if (profileButton) {
    const userId = Number(profileButton.dataset.userId);
    const user = getKnownUserById(userId);
    if (user) {
      openUserProfileModal(user);
    }
    return;
  }
  const button = event.target.closest("[data-action='remove-group-member']");
  if (!button || !state.activeConversation) return;
  const userId = Number(button.dataset.userId);
  try {
    await api(`/api/v1/conversations/${state.activeConversation.id}/participants/${userId}`, {
      method: "DELETE",
    });
    await reloadActiveConversation();
    showToast("Usunięto uczestnika z grupy.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function createRule(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  const isOffHoursRule = payload.trigger_type === "off_hours";
  const isAlwaysActive = Boolean(elements["rule-always-active"]?.checked);
  payload.enabled = true;
  payload.active_from = isOffHoursRule && !isAlwaysActive ? payload.active_from || null : null;
  payload.active_to = isOffHoursRule && !isAlwaysActive ? payload.active_to || null : null;
  payload.trigger_value = payload.trigger_value || null;
  delete payload.always_active;
  try {
    await api("/api/v1/automation/rules", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    form.reset();
    if (elements["rule-always-active"]) {
      elements["rule-always-active"].checked = true;
    }
    updateRuleActivityMode();
    await loadRules();
    await loadAutomationHistory();
    showToast("Dodano regułę autorespondera.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function loadRules() {
  state.rules = await api("/api/v1/automation/rules");
  renderRules();
}

async function loadAutomationHistory() {
  state.automationHistory = await api("/api/v1/automation/history");
  renderAutomationHistory();
}

function renderRules() {
  elements["rules-count"].textContent = String(state.rules.length);
  elements["rules-list"].innerHTML = "";
  if (state.rules.length === 0) {
    elements["rules-list"].innerHTML = `<div class="empty-state">Brak aktywnych reguł.</div>`;
    return;
  }
  state.rules.forEach((rule) => {
    const item = document.createElement("article");
    item.className = "list-item";
    let activityLabel = "Aktywnosc: stale, do recznego wylaczenia";
    if (rule.trigger_type === "off_hours" && rule.active_from && rule.active_to) {
      activityLabel = `Aktywnosc: poza godzinami ${rule.active_from}-${rule.active_to}`;
    }
    item.innerHTML = `
      <div class="conversation-title">
        <span>${rule.name}</span>
        <span class="pill">${rule.trigger_type}</span>
      </div>
      <div class="conversation-meta">${rule.trigger_value || "bez dodatkowych słów kluczowych"}</div>
      <div class="conversation-meta">${activityLabel}</div>
      <div>${escapeHtml(rule.response_text)}</div>
      <button class="ghost-button" data-action="delete-rule" data-id="${rule.id}">Usuń</button>
    `;
    elements["rules-list"].appendChild(item);
  });
}

function updateRuleActivityMode() {
  const triggerType = elements["rule-trigger-type"]?.value;
  const alwaysActive = Boolean(elements["rule-always-active"]?.checked);
  const isOffHoursRule = triggerType === "off_hours";

  elements["rule-activity-block"]?.classList.toggle("hidden", !isOffHoursRule);
  elements["rule-schedule-fields"]?.classList.toggle("hidden", alwaysActive || !isOffHoursRule);

  if (elements["rule-active-from"]) {
    elements["rule-active-from"].disabled = alwaysActive || !isOffHoursRule;
    if (elements["rule-active-from"].disabled) {
      elements["rule-active-from"].value = "";
    }
  }

  if (elements["rule-active-to"]) {
    elements["rule-active-to"].disabled = alwaysActive || !isOffHoursRule;
    if (elements["rule-active-to"].disabled) {
      elements["rule-active-to"].value = "";
    }
  }

  if (elements["rule-activity-hint"]) {
    elements["rule-activity-hint"].textContent =
      alwaysActive || !isOffHoursRule
        ? "Regula bedzie dzialac stale, az do recznego wylaczenia lub usuniecia."
        : "Podaj godziny aktywnosci, a autoresponder bedzie uruchamiany poza tym zakresem.";
  }
}

function renderAutomationHistory() {
  elements["automation-history"].innerHTML = "";
  if (state.automationHistory.length === 0) {
    elements["automation-history"].innerHTML = `<div class="empty-state">Historia automatyzacji jest pusta.</div>`;
    return;
  }
  state.automationHistory.forEach((item) => {
    const node = document.createElement("article");
    node.className = "list-item";
    node.innerHTML = `
      <div class="conversation-title">
        <span>${item.action_type}</span>
        <span>${formatDateTime(item.created_at)}</span>
      </div>
      <div class="conversation-meta">${JSON.stringify(item.details)}</div>
    `;
    elements["automation-history"].appendChild(node);
  });
}

async function handleRuleAction(event) {
  const button = event.target.closest("[data-action='delete-rule']");
  if (!button) return;
  try {
    await api(`/api/v1/automation/rules/${button.dataset.id}`, { method: "DELETE" });
    await loadRules();
    showToast("Reguła została usunięta.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function loadNotifications() {
  const notifications = await api("/api/v1/notifications");
  state.notifications = deduplicateNotifications(
    notifications.filter((notification) => !notification.is_read),
  );
  renderNotifications();
}

function renderNotifications() {
  elements["notification-list"].innerHTML = "";
  if (state.notifications.length === 0) {
    elements["notification-list"].innerHTML = `<div class="empty-state">Brak powiadomień.</div>`;
    return;
  }
  state.notifications.forEach((notification) => {
    const node = document.createElement("article");
    node.className = "list-item";
    if (notification.conversation_id) {
      node.dataset.conversationId = String(notification.conversation_id);
      node.dataset.notificationId = String(notification.id);
    }
    node.innerHTML = `
      <div class="conversation-title">
        <span>${notification.title}</span>
        <span class="pill">${notification.type}</span>
      </div>
      <div>${escapeHtml(notification.body)}</div>
      <div class="note-meta">${formatDateTime(notification.created_at)}</div>
      ${
        notification.is_read
          ? `<div class="conversation-meta">przeczytane</div>`
          : `<button class="ghost-button" data-action="mark-notification" data-id="${notification.id}">Oznacz jako przeczytane</button>`
      }
    `;
    elements["notification-list"].appendChild(node);
  });
}

async function handleNotificationAction(event) {
  const button = event.target.closest("[data-action='mark-notification']");
  if (button) {
    try {
      await api(`/api/v1/notifications/${button.dataset.id}/read`, { method: "POST" });
      await loadNotifications();
    } catch (error) {
      showToast(error.message, true);
    }
    return;
  }

  const notificationNode = event.target.closest("[data-conversation-id]");
  if (!notificationNode) return;
  try {
    const conversationId = Number(notificationNode.dataset.conversationId);
    const notificationId = Number(notificationNode.dataset.notificationId);
    if (notificationId) {
      await api(`/api/v1/notifications/${notificationId}/read`, { method: "POST" });
    }
    await loadNotifications();
    await loadConversations();
    await openConversation(conversationId);
    activateView("chat-view");
  } catch (error) {
    showToast(error.message, true);
  }
}

function resolveNotificationConversationId(notification) {
  if (notification.conversation_id) {
    return notification.conversation_id;
  }
  if (notification.title !== "Dodano Cię do grupy") {
    return null;
  }
  const match = notification.body.match(/grupy [„"](.+?)[”"]/i);
  if (!match) {
    return null;
  }
  const groupTitle = match[1].trim();
  const conversation = state.conversations.find(
    (item) => item.type === "group" && (item.title || "").trim() === groupTitle,
  );
  return conversation?.id ?? null;
}

function deduplicateNotifications(notifications) {
  const seenConversationIds = new Set();
  return notifications.filter((notification) => {
    const conversationId = resolveNotificationConversationId(notification);
    if (!conversationId) {
      return true;
    }
    if (seenConversationIds.has(conversationId)) {
      return false;
    }
    seenConversationIds.add(conversationId);
    return true;
  });
}

function getNotificationGroupKey(notification) {
  if (notification.message_category) {
    return notification.message_category;
  }
  if (notification.type === "system") {
    return "system";
  }
  if (notification.type === "automation") {
    return "automation";
  }
  return "other";
}

function groupNotificationsByCategory(notifications) {
  const grouped = new Map();
  notifications.forEach((notification) => {
    const key = getNotificationGroupKey(notification);
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key).push(notification);
  });

  const orderedGroups = NOTIFICATION_GROUP_ORDER.filter((key) => grouped.has(key)).map((key) => ({
    key,
    label: NOTIFICATION_GROUP_LABELS[key] || key,
    items: grouped.get(key),
  }));

  grouped.forEach((items, key) => {
    if (!NOTIFICATION_GROUP_ORDER.includes(key)) {
      orderedGroups.push({
        key,
        label: NOTIFICATION_GROUP_LABELS[key] || key,
        items,
      });
    }
  });

  return orderedGroups;
}

function renderNotificationBadges(notification) {
  const typeLabel = NOTIFICATION_TYPE_LABELS[notification.type] || notification.type;
  return `<span class="pill">${escapeHtml(typeLabel)}</span>`;
}

function renderNotifications() {
  elements["notification-list"].innerHTML = "";
  if (state.notifications.length === 0) {
    elements["notification-list"].innerHTML = `<div class="empty-state">Brak nowych powiadomien.</div>`;
    return;
  }
  const groups = groupNotificationsByCategory(state.notifications);
  groups.forEach((group) => {
    const groupNode = document.createElement("details");
    groupNode.className = "notification-group";
    groupNode.dataset.group = group.key;
    groupNode.open = state.expandedNotificationGroups.has(group.key);
    groupNode.innerHTML = `
      <summary class="notification-group-summary">
        <span>${group.label}</span>
        <span class="notification-group-meta">
          <span class="pill">${group.items.length}</span>
        </span>
      </summary>
      <div class="notification-group-content"></div>
    `;

    groupNode.addEventListener("toggle", () => {
      if (groupNode.open) {
        state.expandedNotificationGroups.add(group.key);
      } else {
        state.expandedNotificationGroups.delete(group.key);
      }
    });

    const groupContent = groupNode.querySelector(".notification-group-content");
    group.items.forEach((notification) => {
      const node = document.createElement("article");
      node.className = "list-item notification-item";
      const conversationId = resolveNotificationConversationId(notification);
      if (conversationId) {
        node.dataset.conversationId = String(conversationId);
        node.dataset.notificationId = String(notification.id);
      }
      node.innerHTML = `
        <div class="conversation-title">
          <span>${notification.title}</span>
          <span class="notification-badges">${renderNotificationBadges(notification)}</span>
        </div>
        <div>${escapeHtml(notification.body)}</div>
        <div class="note-meta">${formatDateTime(notification.created_at)}</div>
        <button class="ghost-button" data-action="mark-notification" data-id="${notification.id}">Oznacz jako przeczytane</button>
      `;
      groupContent.appendChild(node);
    });

    elements["notification-list"].appendChild(groupNode);
  });
}

async function loadAdminPanel() {
  if (state.me?.role !== "admin") return;
  const [stats, users, spam, diagnostics, logs, automationLogs] = await Promise.all([
    api("/api/v1/admin/stats"),
    api("/api/v1/admin/users"),
    api("/api/v1/admin/spam"),
    api("/api/v1/admin/diagnostics"),
    api("/api/v1/admin/audit-logs"),
    api("/api/v1/admin/automation-logs"),
  ]);
  state.admin = {
    stats,
    users: users.items,
    spam,
    diagnostics: diagnostics.checks,
    logs,
    automationLogs,
  };
  renderAdmin();
}

function renderAdmin() {
  const statsRoot = elements["admin-stats"];
  statsRoot.innerHTML = "";
  Object.entries(state.admin.stats || {}).forEach(([key, value]) => {
    const card = document.createElement("article");
    card.className = "stats-card";
    card.innerHTML = `<span class="conversation-meta">${key}</span><strong>${value}</strong>`;
    statsRoot.appendChild(card);
  });

  elements["admin-users"].innerHTML = "";
  state.admin.users.forEach((user) => {
    const item = document.createElement("article");
    item.className = "list-item";
    item.innerHTML = `
      <div class="conversation-title">
        <span>${user.username}</span>
        <span class="pill">${user.role}</span>
      </div>
      <div class="conversation-meta">${user.email} • ${user.status}</div>
      <button class="ghost-button" data-action="toggle-block" data-id="${user.id}" data-blocked="${user.is_blocked}">
        ${user.is_blocked ? "Odblokuj" : "Zablokuj"}
      </button>
    `;
    elements["admin-users"].appendChild(item);
  });

  elements["admin-spam"].innerHTML = renderListOrEmpty(
    state.admin.spam.map(
      (message) => `
        <article class="list-item">
          <div class="conversation-title">
            <span>#${message.id} • ${message.sender.username}</span>
            <span class="pill">${message.spam_score}</span>
          </div>
          <div>${escapeHtml(message.content)}</div>
          <div class="conversation-meta">${message.spam_reason || "heurystyka"}</div>
        </article>`,
    ),
    "Brak wiadomości oznaczonych jako spam.",
  );

  elements["admin-diagnostics"].innerHTML = renderListOrEmpty(
    state.admin.diagnostics.map(
      (item) => `
        <article class="list-item">
          <div class="conversation-title">
            <span>${item.name}</span>
            <span class="pill">${item.ok ? "OK" : "ERROR"}</span>
          </div>
          <div class="conversation-meta">${item.details}</div>
        </article>`,
    ),
    "Brak danych diagnostycznych.",
  );

  const mergedLogs = [...state.admin.logs.slice(0, 6), ...state.admin.automationLogs.slice(0, 6)];
  elements["admin-logs"].innerHTML = renderListOrEmpty(
    mergedLogs.map(
      (item) => `
        <article class="list-item">
          <div class="conversation-title">
            <span>${item.event_type || item.action_type}</span>
            <span>${formatDateTime(item.created_at)}</span>
          </div>
          <div class="conversation-meta">${JSON.stringify(item.payload || item.details)}</div>
        </article>`,
    ),
    "Brak logów.",
  );
}

async function handleAdminUserAction(event) {
  const button = event.target.closest("[data-action='toggle-block']");
  if (!button) return;
  try {
    const currentlyBlocked = button.dataset.blocked === "true";
    await api(`/api/v1/admin/users/${button.dataset.id}/block?is_blocked=${!currentlyBlocked}`, {
      method: "POST",
    });
    await loadAdminPanel();
    showToast("Zmieniono status użytkownika.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleMessageAction(event) {
  const profileButton = event.target.closest("[data-action='open-user-profile']");
  if (profileButton) {
    if (!state.activeConversation) {
      return;
    }
    const userId = Number(profileButton.dataset.userId);
    const user = getKnownUserById(userId) || getDirectConversationPeer(state.activeConversation)?.user;
    if (user) {
      openUserProfileModal(user);
    }
    return;
  }
  const editButton = event.target.closest("[data-action='edit-message']");
  if (editButton) {
    const messageId = Number(editButton.dataset.id);
    const message = state.activeConversation.messages.find((item) => item.id === messageId);
    const nextContent = window.prompt("Edytuj wiadomość:", message.content);
    if (nextContent && nextContent !== message.content) {
      try {
        const updated = await api(`/api/v1/conversations/messages/${messageId}`, {
          method: "PATCH",
          body: JSON.stringify({ content: nextContent }),
        });
        state.activeConversation.messages = state.activeConversation.messages.map((item) =>
          item.id === messageId ? updated : item,
        );
        renderMessages();
      } catch (error) {
        showToast(error.message, true);
      }
    }
  }

  const deleteButton = event.target.closest("[data-action='delete-message']");
  if (deleteButton) {
    const messageId = Number(deleteButton.dataset.id);
    try {
      const deleted = await api(`/api/v1/conversations/messages/${messageId}`, { method: "DELETE" });
      state.activeConversation.messages = state.activeConversation.messages.map((item) =>
        item.id === messageId ? deleted : item,
      );
      renderMessages();
    } catch (error) {
      showToast(error.message, true);
    }
  }
}

async function runGlobalSearch() {
  const query = elements["message-search-input"].value.trim();
  if (!query) return;
  try {
    const results = await api(`/api/v1/conversations/messages/search?q=${encodeURIComponent(query)}`);
    elements["search-results"].innerHTML = renderListOrEmpty(
      results.map(
        (message) => `
          <article class="list-item">
            <div class="conversation-title">
              <span>${message.sender.username}</span>
              <span class="pill">${message.category}</span>
            </div>
            <div>${escapeHtml(message.content)}</div>
            <div class="conversation-meta">${formatDateTime(message.created_at)}</div>
          </article>`,
      ),
      "Brak wyników wyszukiwania.",
    );
  } catch (error) {
    showToast(error.message, true);
  }
}

function connectWebSocket() {
  if (!state.token) return;
  if (state.ws) {
    state.ws.close();
  }
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  state.ws = new WebSocket(`${protocol}://${window.location.host}/ws?token=${encodeURIComponent(state.token)}`);
  state.ws.onmessage = async (event) => {
    const payload = JSON.parse(event.data);
    await handleSocketEvent(payload);
  };
  state.ws.onclose = () => {
    if (state.token) {
      setTimeout(connectWebSocket, 2000);
    }
  };
}

async function handleSocketEvent(payload) {
  switch (payload.type) {
    case "message.new":
      await loadConversations();
      if (payload.message.conversation_id === state.activeConversationId && state.activeConversation) {
        const exists = state.activeConversation.messages.some((message) => message.id === payload.message.id);
        if (!exists) {
          state.activeConversation.messages.push(payload.message);
          renderMessages();
        }
      }
      await loadNotifications();
      break;
    case "conversation.updated":
      await loadConversations();
      if (payload.conversation_id === state.activeConversationId) {
        await reloadActiveConversation();
      }
      break;
    case "conversation.removed":
      if (payload.conversation_id === state.activeConversationId) {
        clearActiveConversation();
      }
      await loadConversations();
      await loadNotifications();
      break;
    case "message.updated":
      if (payload.message.conversation_id === state.activeConversationId && state.activeConversation) {
        state.activeConversation.messages = state.activeConversation.messages.map((message) =>
          message.id === payload.message.id ? payload.message : message,
        );
        renderMessages();
      }
      break;
    case "message.deleted":
      if (payload.message.conversation_id === state.activeConversationId && state.activeConversation) {
        state.activeConversation.messages = state.activeConversation.messages.map((message) =>
          message.id === payload.message.id ? payload.message : message,
        );
        renderMessages();
      }
      break;
    case "conversation.typing":
      if (payload.conversation_id === state.activeConversationId) {
        elements["typing-indicator"].textContent = payload.is_typing ? `${payload.username} pisze...` : "";
        if (payload.is_typing) {
          setTimeout(() => {
            elements["typing-indicator"].textContent = "";
          }, 1800);
        }
      }
      break;
    case "message.status":
      if (payload.conversation_id === state.activeConversationId && state.activeConversation) {
        state.activeConversation.messages = state.activeConversation.messages.map((message) =>
          payload.message_ids.includes(message.id) ? { ...message, status: payload.status } : message,
        );
        renderMessages();
      }
      break;
    case "presence.changed":
      updateUserPresence(payload.user_id, payload.status);
      break;
    default:
      console.debug("Nieobsłużone zdarzenie websocket:", payload);
  }
}

function updateUserPresence(userId, status) {
  if (state.me?.id === userId) {
    state.me = { ...state.me, status };
  }
  state.userDirectory = state.userDirectory.map((user) =>
    user.id === userId ? { ...user, status } : user,
  );
  state.conversations = state.conversations.map((conversation) => ({
    ...conversation,
    participants: conversation.participants.map((participant) =>
      participant.user.id === userId
        ? { ...participant, user: { ...participant.user, status } }
        : participant,
    ),
  }));
  if (state.activeConversation) {
    state.activeConversation = {
      ...state.activeConversation,
      participants: state.activeConversation.participants.map((participant) =>
        participant.user.id === userId
          ? { ...participant, user: { ...participant.user, status } }
          : participant,
      ),
    };
  }
  renderCurrentUser();
  renderProfile();
  renderConversations();
  renderActiveConversation();
}

function renderCurrentUser() {
  if (!state.me) return;
  elements["current-user-name"].textContent = state.me.username;
  elements["current-user-meta"].textContent = `${state.me.email} • ${state.me.status}`;
  if (state.me.avatar_url) {
    elements["avatar-badge"].innerHTML = `<img src="${escapeHtml(state.me.avatar_url)}" alt="${escapeHtml(state.me.username)}" />`;
  } else {
    elements["avatar-badge"].textContent = getUserInitials(state.me.username);
  }
}

async function reloadActiveConversation() {
  if (!state.activeConversationId) return;
  if (!state.conversations.some((conversation) => conversation.id === state.activeConversationId)) {
    clearActiveConversation();
    return;
  }
  state.activeConversation = await api(`/api/v1/conversations/${state.activeConversationId}`);
  renderConversations();
  renderActiveConversation();
  if (isGroupConversation(state.activeConversation) && canManageGroup(state.activeConversation)) {
    renderGroupAvailableUsers(elements["group-member-search-input"].value.trim());
  }
}

function clearActiveConversation() {
  state.activeConversationId = null;
  state.activeConversation = null;
  closeGroupMemberPicker();
  renderConversations();
  renderActiveConversation();
}

function renderListOrEmpty(items, emptyLabel) {
  if (!items.length) {
    return `<div class="empty-state">${emptyLabel}</div>`;
  }
  return items.join("");
}

function canEditMessage(message, currentUser) {
  return (
    !!currentUser &&
    message.sender_id === currentUser.id &&
    !message.is_deleted &&
    message.status === "sent"
  );
}

function getUserInitials(username) {
  return String(username || "?")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("")
    .slice(0, 2) || "?";
}

function formatMessageStatus(status) {
  switch (status) {
    case "read":
      return "odczytane";
    case "deleted":
      return "usuniete";
    case "delivered":
    case "sent":
    default:
      return "wyslane";
  }
}

function formatDateTime(value) {
  if (!value) return "brak daty";
  return new Date(value).toLocaleString("pl-PL", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function showToast(message, isError = false) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.style.borderLeft = `4px solid ${isError ? "#bc4545" : "#1e6866"}`;
  toast.textContent = message;
  elements["toast-container"].appendChild(toast);
  setTimeout(() => toast.remove(), 3400);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderGroupManagementPanel() {
  const panel = elements["group-management-panel"];
  const conversation = state.activeConversation;
  const mainHeader = panel.querySelector(".section-header");
  const panelTitle = mainHeader?.querySelector("h3");
  const panelPill = mainHeader?.querySelector(".pill");
  const renameForm = elements["group-rename-form"];
  const memberToggleButton = elements["group-member-toggle-button"];
  const deletePanel = elements["group-delete-panel"];
  const leavePanel = elements["group-leave-panel"];
  const membersHeader = elements["group-members-count"]?.closest(".section-header");

  if (!isGroupConversation(conversation)) {
    closeGroupMemberPicker();
    panel.classList.add("hidden");
    elements["group-available-count"].textContent = "0";
    elements["group-members-list"].innerHTML = "";
    elements["group-members-count"].textContent = "0";
    renameForm.classList.remove("hidden");
    memberToggleButton.classList.add("hidden");
    deletePanel.classList.add("hidden");
    leavePanel.classList.add("hidden");
    membersHeader?.classList.remove("hidden");
    if (panelTitle) panelTitle.textContent = "Zarzadzanie grupa";
    if (panelPill) panelPill.textContent = "czlonkowie";
    return;
  }

  panel.classList.remove("hidden");
  elements["group-members-count"].textContent = String(conversation.participants.length);
  elements["group-rename-input"].value = conversation.title || "";

  const managerMode = canManageGroup(conversation);
  const ownerMode = isGroupOwner(conversation);
  elements["group-rename-input"].disabled = !managerMode;
  elements["group-rename-button"].disabled = !managerMode;
  elements["group-delete-button"].disabled = !ownerMode;
  renameForm.classList.toggle("hidden", !managerMode);
  memberToggleButton.classList.toggle("hidden", !managerMode);
  deletePanel.classList.toggle("hidden", !ownerMode);
  leavePanel.classList.remove("hidden");
  membersHeader?.classList.remove("hidden");
  memberToggleButton.textContent = "Dodaj uzytkownika";

  if (panelTitle) {
    panelTitle.textContent = managerMode ? "Zarzadzanie grupa" : "Uczestnicy grupy";
  }
  if (panelPill) {
    panelPill.textContent = managerMode ? "czlonkowie" : "lista";
  }

  if (!managerMode) {
    closeGroupMemberPicker();
    elements["group-available-count"].textContent = "0";
  }

  elements["group-members-list"].innerHTML = "";
  conversation.participants.forEach((participant) => {
    const isOwner = conversation.created_by_id === participant.user.id;
    const item = document.createElement("article");
    item.className = "list-item";
    item.innerHTML = `
      <button
        type="button"
        class="profile-list-trigger"
        data-action="open-user-profile"
        data-user-id="${participant.user.id}"
        aria-label="Otworz profil uzytkownika ${participant.user.username}"
      >
        <div class="conversation-title">
          <span>${participant.user.username}</span>
          <span><span class="status-dot ${participant.user.status}"></span>${participant.user.status}</span>
        </div>
        <div class="conversation-meta">
          ${participant.user.email} • ${isOwner ? "wlasciciel grupy" : "uczestnik"}
        </div>
      </button>
      ${
        managerMode && !isOwner
          ? `<button class="ghost-button" data-action="remove-group-member" data-user-id="${participant.user.id}">Usun z grupy</button>`
          : ""
      }
    `;
    elements["group-members-list"].appendChild(item);
  });
}

async function deleteGroupConversation() {
  const conversation = state.activeConversation;
  if (!isGroupOwner(conversation)) return;

  const confirmed = window.confirm(
    `Czy na pewno chcesz usunac grupe "${getConversationTitle(conversation)}"?`,
  );
  if (!confirmed) {
    return;
  }

  try {
    await api(`/api/v1/conversations/${conversation.id}`, {
      method: "DELETE",
    });
    if (state.groupSetupConversationId === conversation.id) {
      state.groupSetupConversationId = null;
    }
    clearActiveConversation();
    await loadConversations();
    await loadNotifications();
    showToast("Grupa zostala usunieta.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function leaveGroupConversation() {
  const conversation = state.activeConversation;
  if (!isGroupConversation(conversation)) return;

  const isOwner = isGroupOwner(conversation);
  const participantCount = conversation.participants.length;
  let confirmationMessage = `Czy na pewno chcesz opuscic grupe "${getConversationTitle(conversation)}"?`;
  if (isOwner && participantCount > 1) {
    confirmationMessage =
      `Czy na pewno chcesz opuscic grupe "${getConversationTitle(conversation)}"? Wlasnosc grupy przejdzie na innego uczestnika.`;
  } else if (participantCount === 1) {
    confirmationMessage =
      `Czy na pewno chcesz opuscic grupe "${getConversationTitle(conversation)}"? To zamknie ten czat grupowy.`;
  }

  const confirmed = window.confirm(confirmationMessage);
  if (!confirmed) {
    return;
  }

  try {
    await api(`/api/v1/conversations/${conversation.id}/leave`, {
      method: "DELETE",
    });
    if (state.groupSetupConversationId === conversation.id) {
      state.groupSetupConversationId = null;
    }
    clearActiveConversation();
    await loadConversations();
    await loadNotifications();
    showToast("Opusciles grupe.");
  } catch (error) {
    showToast(error.message, true);
  }
}
