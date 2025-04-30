document.addEventListener('DOMContentLoaded', function() {
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const messageInput = document.getElementById('message-input');
  const newConversationBtn = document.getElementById('new-conversation-btn');
  const conversationItems = document.querySelectorAll('.conversation-item');
  
  // Scroll to bottom of chat
  if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Format any existing HTML content in the assistant messages
    formatExistingMessages();
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
      
      const conversationId = document.querySelector('input[name="conversation_id"]')?.value;
      
      // Disable form while sending
      const submitButton = chatForm.querySelector('button[type="submit"]');
      messageInput.disabled = true;
      submitButton.disabled = true;
      
      // Add loading indicator
      // Replace previous spinner with typing indicator
      submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      
      // Add user message to UI immediately
      addMessage(message, 'user', formatTime(new Date()));
      messageInput.value = '';
      messageInput.style.height = 'auto'; // Reset textarea height
      
      // Add typing indicator
      const typingIndicator = addTypingIndicator();
      
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
        // Remove typing indicator
        if (typingIndicator) {
          typingIndicator.remove();
        }
        
        // If this is a new conversation, update the URL
        if (!conversationId && data.conversation_id) {
          const url = new URL(window.location);
          url.searchParams.set('conversation_id', data.conversation_id);
          window.history.pushState({}, '', url);
          
          if (document.querySelector('input[name="conversation_id"]')) {
            document.querySelector('input[name="conversation_id"]').value = data.conversation_id;
          }
          
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
        
        // Remove typing indicator
        if (typingIndicator) {
          typingIndicator.remove();
        }
        
        // Add error message with system class
        addSystemMessage('Une erreur est survenue. Veuillez réessayer.');
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
    
    // Format HTML content if it's an assistant message
    if (role === 'assistant') {
      formatMessageContent(contentDiv);
    }
    
    // Add fade-in animation
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(10px)';
    
    // Trigger animation
    setTimeout(() => {
      messageDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      messageDiv.style.opacity = '1';
      messageDiv.style.transform = 'translateY(0)';
    }, 10);
    
    return messageDiv;
  }
  
  // Add typing indicator while waiting for response
  function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing';
    
    typingDiv.innerHTML = `
      <div class="message-content">
        <div class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return typingDiv;
  }
  
  // Add system message (for errors)
  function addSystemMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = formatTime(new Date());
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
  }
  
  // Format the HTML content in assistant messages
  function formatMessageContent(contentElement) {
    // Format tables
    const tables = contentElement.querySelectorAll('table');
    tables.forEach(table => {
      table.classList.add('formatted-table');
      
      // Make table scrollable if too wide
      if (table.offsetWidth > contentElement.offsetWidth) {
        const tableWrapper = document.createElement('div');
        tableWrapper.style.overflowX = 'auto';
        table.parentNode.insertBefore(tableWrapper, table);
        tableWrapper.appendChild(table);
      }
      
      // Style table headers
      const headers = table.querySelectorAll('th');
      headers.forEach(header => {
        header.classList.add('table-header');
      });
      
      // Style table cells
      const cells = table.querySelectorAll('td');
      cells.forEach(cell => {
        cell.classList.add('table-cell');
      });
      
      // Style even rows for better readability
      const rows = table.querySelectorAll('tr:nth-child(even)');
      rows.forEach(row => {
        row.classList.add('even-row');
      });
    });
    
    // Format headings
    const headings = contentElement.querySelectorAll('h1, h2, h3, h4, h5, h6');
    headings.forEach(heading => {
      heading.classList.add('content-heading');
    });
    
    // Format lists
    const lists = contentElement.querySelectorAll('ul, ol');
    lists.forEach(list => {
      list.classList.add('content-list');
    });
    
    // Format special sections
    const echauffement = contentElement.querySelectorAll('h4.echauffement, div.echauffement');
    echauffement.forEach(el => {
      if (!el.classList.contains('formatted')) {
        el.classList.add('formatted');
      }
    });
    
    const cardio = contentElement.querySelectorAll('h4.cardio, div.cardio');
    cardio.forEach(el => {
      if (!el.classList.contains('formatted')) {
        el.classList.add('formatted');
      }
    });
    
    const musculation = contentElement.querySelectorAll('h4.musculation, div.musculation');
    musculation.forEach(el => {
      if (!el.classList.contains('formatted')) {
        el.classList.add('formatted');
      }
    });
    
    const recuperation = contentElement.querySelectorAll('h4.recuperation, div.recuperation');
    recuperation.forEach(el => {
      if (!el.classList.contains('formatted')) {
        el.classList.add('formatted');
      }
    });
    
    // Format badges
    const badges = contentElement.querySelectorAll('.badge');
    badges.forEach(badge => {
      if (!badge.classList.contains('formatted')) {
        badge.classList.add('formatted');
      }
    });
  }
  
  // Format existing messages when page loads
  function formatExistingMessages() {
    const assistantMessages = document.querySelectorAll('.message.assistant .message-content');
    assistantMessages.forEach(formatMessageContent);
  }
  
  // Helper function to format time
  function formatTime(date) {
    return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  }
  
  // Helper function to get CSRF token
  function getCsrfToken() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (csrfToken) return csrfToken;
    
    const csrfInput = document.querySelector('input[name="csrf_token"]');
    return csrfInput ? csrfInput.value : '';
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
