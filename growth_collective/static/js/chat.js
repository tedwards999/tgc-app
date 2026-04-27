(function () {
  'use strict';

  var root = document.getElementById('chat-root');
  if (!root) return;

  var roomSlug = root.dataset.roomSlug;
  var messagesEl = document.getElementById('chat-messages');
  var emptyEl = document.getElementById('chat-empty');
  var form = document.getElementById('chat-form');
  var input = document.getElementById('chat-input');
  var sendBtn = document.getElementById('chat-send');
  var statusEl = document.getElementById('chat-status');
  var indicatorEl = document.getElementById('chat-indicator');

  var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  var wsUrl = protocol + '//' + window.location.host + '/ws/chat/' + roomSlug + '/';

  var socket = new WebSocket(wsUrl);

  socket.onopen = function () {
    indicatorEl.innerHTML = '<span class="chat__dot chat__dot--online"></span> Connected';
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
  };

  socket.onclose = function (event) {
    input.disabled = true;
    sendBtn.disabled = true;
    indicatorEl.innerHTML = '<span class="chat__dot chat__dot--offline"></span> Disconnected';
    if (event.code === 4001) {
      statusEl.textContent = 'You must be logged in to chat.';
    } else if (event.code === 4003) {
      statusEl.textContent = 'You do not have access to this room.';
    } else if (event.code !== 1000) {
      statusEl.textContent = 'Connection lost — refresh to reconnect.';
    }
  };

  socket.onerror = function () {
    indicatorEl.innerHTML = '<span class="chat__dot chat__dot--offline"></span> Error';
  };

  socket.onmessage = function (event) {
    var data = JSON.parse(event.data);
    if (data.type === 'history') {
      if (data.messages.length > 0 && emptyEl) {
        emptyEl.remove();
        emptyEl = null;
      }
      data.messages.forEach(appendMessage);
    } else if (data.type === 'message') {
      if (emptyEl) {
        emptyEl.remove();
        emptyEl = null;
      }
      appendMessage(data);
    }
    scrollToBottom();
  };

  function appendMessage(msg) {
    var el = document.createElement('div');
    el.className = 'chat-message';
    el.dataset.messageId = msg.message_id;
    el.innerHTML =
      '<div class="chat-message__avatar">' + escapeHtml(msg.sender_initials) + '</div>' +
      '<div class="chat-message__body">' +
        '<div class="chat-message__meta">' +
          '<span class="chat-message__name">' + escapeHtml(msg.sender_name) + '</span>' +
          '<time class="chat-message__time">' + formatTime(msg.timestamp) + '</time>' +
        '</div>' +
        '<p class="chat-message__text">' + escapeHtml(msg.body) + '</p>' +
      '</div>';
    messagesEl.appendChild(el);
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function formatTime(iso) {
    var d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(String(str)));
    return div.innerHTML;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var msg = input.value.trim();
    if (!msg || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ message: msg }));
    input.value = '';
  });

  // Send on Enter, new line on Shift+Enter
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit'));
    }
  });
})();
