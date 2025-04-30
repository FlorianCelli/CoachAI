document.addEventListener('DOMContentLoaded', function() {
  // Mobile menu toggle
  const burger = document.querySelector('.navbar-burger');
  const menu = document.querySelector('.navbar-menu');
  
  if (burger && menu) {
    burger.addEventListener('click', function() {
      menu.classList.toggle('active');
    });
  }
  
  // Flash messages auto-dismiss
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      setTimeout(() => {
        alert.style.display = 'none';
      }, 500);
    }, 5000);
  });
});

/* static/js/chat.js */
document.addEventListener('DOMContentLoaded', function() {
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const messageInput = document.getElementById('message-input');
  const newConversationBtn = document.getElementById('new-conversation-btn');
  const conversationItems = document.querySelectorAll('.conversation-item');
  
  // Scroll to bottom of chat
  if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  
  // New conversation button
  if (newConversationBtn) {
    newConversationBtn.addEventListener('click', function() {
      fetch('/chat/new', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        }
      })
      .then(response => response.json())
      .then(data => {
        window.location.href = data.redirect_url;
      })
      .catch(error => console.error('Error:', error));
    });
  }
  
  // Conversation items click
  if (conversationItems.length > 0) {
    conversationItems.forEach(item => {
      item.addEventListener('click', function() {
        const conversationId = this.getAttribute('data-id');
        window.location.href = `/chat?conversation_id=${conversationId}`;
      });
    });
  }
  
  // Chat form submit
  if (chatForm) {
    chatForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const message = messageInput.value.trim();
      if (!message) return;
      
      const conversationId = document.querySelector('input[name="conversation_id"]').value;
      
      // Disable form while sending
      const submitButton = chatForm.querySelector('button[type="submit"]');
      messageInput.disabled = true;
      submitButton.disabled = true;
      
      // Add loading indicator
      submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      
      // Add user message to UI immediately
      addMessage(message, 'user', formatTime(new Date()));
      messageInput.value = '';
      
      fetch('/chat/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
          message: message,
          conversation_id: conversationId || null
        })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        // If this is a new conversation, update the URL
        if (!conversationId && data.conversation_id) {
          const url = new URL(window.location);
          url.searchParams.set('conversation_id', data.conversation_id);
          window.history.pushState({}, '', url);
          document.querySelector('input[name="conversation_id"]').value = data.conversation_id;
          
          // Update page title if needed
          const headerTitle = document.querySelector('.chat-header h2');
          if (headerTitle && headerTitle.textContent === 'Nouvelle conversation') {
            // Refresh the page to update the sidebar
            window.location.reload();
          }
        }
        
        // Add assistant message to UI
        addMessage(data.assistant_message.content, 'assistant', data.assistant_message.time);
      })
      .catch(error => {
        console.error('Error:', error);
        addMessage('Une erreur est survenue. Veuillez réessayer.', 'assistant', formatTime(new Date()));
      })
      .finally(() => {
        // Re-enable form
        messageInput.disabled = false;
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        messageInput.focus();
      });
    });
  }
  
  // Helper function to add message to chat UI
  function addMessage(content, role, time) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = time;
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  
  // Helper function to format time
  function formatTime(date) {
    return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  }
  
  // Helper function to get CSRF token
  function getCsrfToken() {
    return document.querySelector('input[name="csrf_token"]')?.value || '';
  }
  
  // Make textarea expand/contract based on content
  if (messageInput) {
    messageInput.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Allow Shift+Enter for newlines, Enter to submit
    messageInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
      }
    });
  }
});
