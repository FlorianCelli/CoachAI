document.addEventListener('DOMContentLoaded', function() {
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const messageInput = document.getElementById('message-input');
  const newConversationBtn = document.getElementById('new-conversation-btn');
  const conversationItems = document.querySelectorAll('.conversation-item');
  const imageUploadBtn = document.getElementById('image-upload-btn');
  const imageInput = document.getElementById('image-input');
  const imagePreviewContainer = document.getElementById('image-preview-container');
  const imagePreview = document.getElementById('image-preview');
  const removeImageBtn = document.getElementById('remove-image-btn');
  
  let currentImageData = null;
  
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
  
  // Image upload button click
  if (imageUploadBtn) {
    imageUploadBtn.addEventListener('click', function() {
      imageInput.click();
    });
  }
  
  // Handle image selection
  if (imageInput) {
    imageInput.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
          // Store the image data
          currentImageData = e.target.result;
          
          // Show the preview
          imagePreview.src = currentImageData;
          imagePreviewContainer.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
      }
    });
  }
  
  // Remove image button
  if (removeImageBtn) {
    removeImageBtn.addEventListener('click', function() {
      // Clear the image data
      currentImageData = null;
      imageInput.value = '';
      
      // Hide the preview
      imagePreviewContainer.classList.add('hidden');
      imagePreview.src = '';
    });
  }
  
  // Chat form submit
  if (chatForm) {
    chatForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const message = messageInput.value.trim();
      if (!message && !currentImageData) return;  // Require either message or image
      
      const conversationId = document.querySelector('input[name="conversation_id"]')?.value;
      
      // Disable form while sending
      const submitButton = chatForm.querySelector('button[type="submit"]');
      messageInput.disabled = true;
      submitButton.disabled = true;
      imageUploadBtn.disabled = true;
      
      // Store current image data for use in request
      const imageToSend = currentImageData;
      
      // Clear image preview immediately
      if (imagePreviewContainer) {
        imagePreviewContainer.classList.add('hidden');
      }
      if (imagePreview) {
        imagePreview.src = '';
      }
      
      // Add loading indicator
      submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      
      // Add user message to UI immediately
      let messageContent = message;
      if (imageToSend) {
        // If there's an image, add it to the message content
        messageContent = `<div class="user-message-content">
          <div class="user-image">
            <img src="${imageToSend}" alt="User uploaded image" class="uploaded-image">
          </div>
          ${message ? `<div class="user-text">${message}</div>` : ''}
        </div>`;
      }
      
      addMessage(messageContent, 'user', formatTime(new Date()));
      messageInput.value = '';
      messageInput.style.height = 'auto'; // Reset textarea height
      
      // Clear the image data reference to prevent reuse
      currentImageData = null;
      
      // Add typing indicator
      const typingIndicator = addTypingIndicator();
      
      // IMPORTANT: Envoyer la requête AVEC texte ET image en UNE SEULE fois
      console.log("Envoi d'une requête UNIQUE avec " + 
                 (message ? "texte" : "pas de texte") + 
                 " et " + 
                 (imageToSend ? "image" : "pas d'image"));
      
      fetch('/chat/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
          message: message,
          conversation_id: conversationId || null,
          image_data: imageToSend
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
            return; // Avoid adding message twice
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
        imageUploadBtn.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        messageInput.focus();
        
        // Make sure image input is cleared
        if (imageInput) {
          imageInput.value = '';
        }
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
    
    // Format images
    const images = contentElement.querySelectorAll('img');
    images.forEach(img => {
      img.classList.add('ai-response-image');
      img.addEventListener('click', function() {
        // Create lightbox for image
        const lightbox = document.createElement('div');
        lightbox.className = 'lightbox';
        lightbox.innerHTML = `
          <div class="lightbox-content">
            <img src="${img.src}" alt="Full size image">
            <span class="close-lightbox">&times;</span>
          </div>
        `;
        document.body.appendChild(lightbox);
        
        // Add close functionality
        lightbox.querySelector('.close-lightbox').addEventListener('click', function() {
          lightbox.remove();
        });
        lightbox.addEventListener('click', function(e) {
          if (e.target === lightbox) {
            lightbox.remove();
          }
        });
      });
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
