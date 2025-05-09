/* ---------------------------------------------------------------------------
   static/js/chat.js
   Gestion complète de la messagerie : texte + image, création de conversation,
   mise à jour de l’UI, CSRF, sans reload intempestif.
--------------------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {

  /* --------------------------------------------------------------------- */
  /* 1.  Sélecteurs utiles                                                */
  /* --------------------------------------------------------------------- */
  const chatMessages        = document.getElementById('chat-messages');
  const chatForm            = document.getElementById('chat-form');
  const messageInput        = document.getElementById('message-input');
  const newConversationBtn  = document.getElementById('new-conversation-btn');
  const conversationItems   = document.querySelectorAll('.conversation-item');
  const imageUploadBtn      = document.getElementById('image-upload-btn');
  const imageInput          = document.getElementById('image-input');
  const imagePreviewCont    = document.getElementById('image-preview-container');
  const imagePreview        = document.getElementById('image-preview');
  const removeImageBtn      = document.getElementById('remove-image-btn');

  /* --------------------------------------------------------------------- */
  /* 2.  États globaux                                                    */
  /* --------------------------------------------------------------------- */
  let conversationId  = getConversationId();
  let currentImageB64 = null;

  /* --------------------------------------------------------------------- */
  /* 3.  Helpers                                                          */
  /* --------------------------------------------------------------------- */
  function getCsrfToken () {
    const meta  = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.content;
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : '';
  }

  function getConversationId () {
    const hidden = document.querySelector('input[name="conversation_id"]');
    if (hidden && hidden.value) return hidden.value;
    const id = new URLSearchParams(window.location.search).get('conversation_id');
    return id ? id : null;
  }

  function formatTime (d = new Date()) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  /* --------------------------------------------------------------------- */
  /* 4.  UI helpers : addMessage, typing indicator …                       */
  /* --------------------------------------------------------------------- */
  function addMessage (html, role, time) {
    const wrap  = document.createElement('div');
    wrap.className = `message ${role}`;
    wrap.innerHTML = `
      <div class="message-content">${html}</div>
      <div class="message-time">${time}</div>`;
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return wrap;
  }

  function addTyping () {
    return addMessage(`
      <div class="typing-indicator"><span></span><span></span><span></span></div>
    `, 'assistant typing', formatTime());
  }

  /* --------------------------------------------------------------------- */
  /* 5.  Création d’une nouvelle conversation                             */
  /* --------------------------------------------------------------------- */
  async function createConversation () {
    const r = await fetch('/chat/new', {
      method  : 'POST',
      headers : {
        'Content-Type': 'application/json',
        'X-CSRFToken' : getCsrfToken()
      }
    });
    if (!r.ok) throw new Error(await r.text());
    const data = await r.json();
    conversationId = data.conversation_id;

    /* met à jour l’input caché s’il existe */
    let hidden = document.querySelector('input[name="conversation_id"]');
    if (!hidden) {
      hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = 'conversation_id';
      chatForm.appendChild(hidden);
    }
    hidden.value = conversationId;

    /* push l’ID dans l’URL sans recharger */
    const url = new URL(window.location);
    url.searchParams.set('conversation_id', conversationId);
    history.replaceState({}, '', url);
  }

  /* --------------------------------------------------------------------- */
  /* 6.  Envoi du message                                                 */
  /* --------------------------------------------------------------------- */
  async function sendMessage (text) {
    /* Crée la convo si nécessaire */
    if (!conversationId) await createConversation();

    const typing = addTyping();

    const r = await fetch('/chat/send', {
      method  : 'POST',
      headers : {
        'Content-Type': 'application/json',
        'X-CSRFToken' : getCsrfToken(),
        'Accept'      : 'application/json'
      },
      body    : JSON.stringify({
        conversation_id : conversationId,
        message         : text,
        image_data      : currentImageB64
      })
    });

    typing.remove();

    if (!r.ok) {
      addMessage('Une erreur est survenue. Réessaie.', 'system', formatTime());
      return;
    }
    const data = await r.json();
    addMessage(data.assistant_message.content, 'assistant', data.assistant_message.time);
  }

  /* --------------------------------------------------------------------- */
  /* 7.  Gestion formulaire                                               */
  /* --------------------------------------------------------------------- */
  if (chatForm) {
    chatForm.addEventListener('submit', async e => {
      e.preventDefault();
      const text = messageInput.value.trim();
      if (!text && !currentImageB64) return;

      /* Ajoute immédiatement le message côté UI */
      let html = text;
      if (currentImageB64) {
        html = `<div class="user-message-content">
                  <div class="user-image"><img src="${currentImageB64}" class="uploaded-image"></div>
                  ${text ? `<div class="user-text">${text}</div>` : ''}
                </div>`;
      }
      addMessage(html, 'user', formatTime());

      /* reset input + image preview */
      messageInput.value = '';
      if (imagePreviewCont) imagePreviewCont.classList.add('hidden');
      if (imagePreview)    imagePreview.src = '';
      currentImageB64 = null;

      try {
        await sendMessage(text);
      } catch (err) {
        console.error(err);
        addMessage('Une erreur est survenue. Réessaie.', 'system', formatTime());
      }
    });
  }

  /* --------------------------------------------------------------------- */
  /* 8.  Nouveaux boutons / image upload                                   */
  /* --------------------------------------------------------------------- */
  if (newConversationBtn) {
    newConversationBtn.addEventListener('click', async () => {
      await createConversation();
      /* Vide la zone de chat */
      chatMessages.innerHTML = '';
    });
  }

  if (imageUploadBtn && imageInput) {
    imageUploadBtn.addEventListener('click', () => imageInput.click());
    imageInput.addEventListener('change', e => {
      const f = e.target.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = e2 => {
        currentImageB64 = e2.target.result;
        imagePreview.src = currentImageB64;
        imagePreviewCont.classList.remove('hidden');
      };
      reader.readAsDataURL(f);
    });
  }

  if (removeImageBtn) {
    removeImageBtn.addEventListener('click', () => {
      currentImageB64 = null;
      imageInput.value = '';
      imagePreviewCont.classList.add('hidden');
      imagePreview.src = '';
    });
  }

  /* --------------------------------------------------------------------- */
  /* 9.  Mise en forme initiale                                           */
  /* --------------------------------------------------------------------- */
  if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
});

