/* ============================================================
   SocialApp — Chat JavaScript
   WebSocket real-time chat with typing indicators,
   read receipts, and reply support
   ============================================================ */

let socket = null;
let replyToId = null;
let replyContent = null;
let typingTimer = null;
let isTyping = false;

// ── WebSocket Connection ──────────────────────────────────
function connectWebSocket() {
  const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${location.host}/ws/chat/${ROOM_ID}/`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log('WebSocket connected');
    // Send read receipt on connect
    socket.send(JSON.stringify({ type: 'read' }));
    scrollToBottom();
  };

  socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    handleSocketMessage(data);
  };

  socket.onclose = () => {
    console.log('WebSocket closed, reconnecting in 3s...');
    setTimeout(connectWebSocket, 3000);
  };

  socket.onerror = (err) => {
    console.error('WebSocket error:', err);
  };
}

// ── Handle Incoming Messages ──────────────────────────────
function handleSocketMessage(data) {
  switch (data.type) {
    case 'message':
      appendMessage(data);
      // Send read receipt for others' messages
      if (!data.is_own) {
        socket.send(JSON.stringify({ type: 'read' }));
      }
      break;
    case 'typing':
      showTypingIndicator(data.user, data.is_typing);
      break;
    case 'read':
      updateReadReceipts(data.user);
      break;
    case 'status':
      updateUserStatus(data.status, data.last_seen);
      break;
  }
}

// ── Append Message to DOM ─────────────────────────────────
function appendMessage(data) {
  const area = document.getElementById('messagesArea');
  const isOwn = data.is_own || data.sender === CURRENT_USER;

  const replyHtml = data.reply_to ? `
    <div class="msg-reply-preview">
      <span class="fw-500">${data.reply_content || ''}</span>
    </div>` : '';

  const msgHtml = `
    <div class="message-bubble-wrap ${isOwn ? 'own' : 'other'}" id="msg-${data.message_id}">
      ${!isOwn ? `<img src="${data.avatar}" alt="" class="msg-avatar">` : ''}
      <div class="message-bubble">
        ${replyHtml}
        <p class="msg-content">${escapeHtml(data.content)}</p>
        <div class="msg-footer">
          <span class="msg-time">${formatTime(data.created_at)}</span>
          ${isOwn ? '<span class="msg-status"><i class="fas fa-check"></i></span>' : ''}
        </div>
      </div>
      <button class="msg-reply-btn" onclick="setReply('${data.message_id}','${escapeHtml(data.content)}','${data.sender}')">
        <i class="fas fa-reply"></i>
      </button>
    </div>`;

  area.insertAdjacentHTML('beforeend', msgHtml);
  scrollToBottom();

  // Animate in
  const newMsg = area.lastElementChild;
  newMsg.style.opacity = '0';
  newMsg.style.transform = `translateY(10px) ${isOwn ? '' : 'translateX(-10px)'}`;
  requestAnimationFrame(() => {
    newMsg.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
    newMsg.style.opacity = '1';
    newMsg.style.transform = 'none';
  });
}

// ── Send Message ──────────────────────────────────────────
function sendMessage() {
  const input = document.getElementById('messageInput');
  const content = input.value.trim();
  if (!content || !socket || socket.readyState !== WebSocket.OPEN) return;

  socket.send(JSON.stringify({
    type: 'message',
    content,
    reply_to: replyToId,
    reply_content: replyContent,
  }));

  input.value = '';
  cancelReply();
  stopTyping();
}

// ── Key Handlers ──────────────────────────────────────────
function handleMessageKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// ── Typing Indicators ─────────────────────────────────────
function handleTyping() {
  if (!isTyping && socket?.readyState === WebSocket.OPEN) {
    isTyping = true;
    socket.send(JSON.stringify({ type: 'typing', is_typing: true }));
  }
  clearTimeout(typingTimer);
  typingTimer = setTimeout(stopTyping, 2000);
}

function stopTyping() {
  if (isTyping && socket?.readyState === WebSocket.OPEN) {
    isTyping = false;
    socket.send(JSON.stringify({ type: 'typing', is_typing: false }));
  }
  clearTimeout(typingTimer);
}

function showTypingIndicator(user, isTypingNow) {
  const indicator = document.getElementById('typingIndicator');
  const userEl = document.getElementById('typingUser');
  if (!indicator) return;
  if (isTypingNow) {
    if (userEl) userEl.textContent = user;
    indicator.classList.remove('d-none');
    scrollToBottom();
  } else {
    indicator.classList.add('d-none');
  }
}

// ── Read Receipts ─────────────────────────────────────────
function updateReadReceipts(user) {
  // Update the last message's check icon to double-check
  const ownMessages = document.querySelectorAll('.message-bubble-wrap.own .msg-status');
  if (ownMessages.length > 0) {
    const last = ownMessages[ownMessages.length - 1];
    last.innerHTML = '<i class="fas fa-check-double text-info"></i>';
  }
}

// ── User Status Updates ───────────────────────────────────
function updateUserStatus(status, lastSeen) {
  const statusEl = document.getElementById('chatStatus');
  if (!statusEl) return;
  if (status === 'online') {
    statusEl.innerHTML = '<span class="text-success">Online</span>';
  } else {
    statusEl.textContent = lastSeen ? `Last seen ${new Date(lastSeen).toLocaleTimeString()}` : 'Offline';
  }
}

// ── Reply Support ─────────────────────────────────────────
function setReply(msgId, content, sender) {
  replyToId = msgId;
  replyContent = content;
  const bar = document.getElementById('replyBar');
  const nameEl = document.getElementById('replyToName');
  const contentEl = document.getElementById('replyToContent');
  if (bar && nameEl && contentEl) {
    nameEl.textContent = `Reply to ${sender}`;
    contentEl.textContent = content.substring(0, 80);
    bar.classList.remove('d-none');
    document.getElementById('messageInput')?.focus();
  }
}

function cancelReply() {
  replyToId = null;
  replyContent = null;
  document.getElementById('replyBar')?.classList.add('d-none');
}

// ── File Attachment ───────────────────────────────────────
document.getElementById('fileInput')?.addEventListener('change', function() {
  const file = this.files[0];
  if (!file) return;
  // In production, upload to server via AJAX and then send message with attachment URL
  // For now, show local preview as a placeholder message
  showToast(`Attaching ${file.name}... (feature requires server-side handling)`);
  this.value = '';
});

// ── Utilities ─────────────────────────────────────────────
function scrollToBottom() {
  const area = document.getElementById('messagesArea');
  if (area) {
    requestAnimationFrame(() => {
      area.scrollTop = area.scrollHeight;
    });
  }
}

function formatTime(isoString) {
  return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── Init ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  connectWebSocket();
  scrollToBottom();

  // Emoji button placeholder
  document.getElementById('emojiBtn')?.addEventListener('click', () => {
    showToast('Emoji picker coming soon!');
  });
});
