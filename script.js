document.addEventListener('DOMContentLoaded', function() {
    // Profile dropdown
    const profileDropdown = document.querySelector('.profile-dropdown');
    if (profileDropdown) {
        const dropdownBtn = profileDropdown.querySelector('.profile-dropdown-btn');
        const dropdownContent = profileDropdown.querySelector('.profile-dropdown-content');
        
        dropdownBtn.addEventListener('click', function() {
            dropdownContent.style.display = dropdownContent.style.display === 'block' ? 'none' : 'block';
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {
            if (!profileDropdown.contains(event.target)) {
                dropdownContent.style.display = 'none';
            }
        });
    }
    
    // Flash messages auto-hide
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            setTimeout(() => {
                message.style.opacity = '0';
                message.style.transition = 'opacity 0.5s';
                setTimeout(() => {
                    message.style.display = 'none';
                }, 500);
            }, 3000);
        });
    }
    
    // Post image preview
    const postImageInput = document.getElementById('post-image');
    if (postImageInput) {
        postImageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create preview element
                    let previewContainer = document.querySelector('.post-image-preview');
                    if (!previewContainer) {
                        previewContainer = document.createElement('div');
                        previewContainer.className = 'post-image-preview';
                        previewContainer.style.marginTop = '8px';
                        previewContainer.style.position = 'relative';
                        
                        const postForm = document.querySelector('.post-form');
                        postForm.appendChild(previewContainer);
                    }
                    
                    previewContainer.innerHTML = `
                        <img src="${e.target.result}" alt="Preview" style="width: 100%; border-radius: 8px;">
                        <button type="button" class="remove-preview" style="position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.5); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                    
                    // Add remove button functionality
                    const removeBtn = previewContainer.querySelector('.remove-preview');
                    removeBtn.addEventListener('click', function() {
                        previewContainer.remove();
                        postImageInput.value = '';
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Comment sections toggle
    const commentBtns = document.querySelectorAll('.comment-btn');
    if (commentBtns.length > 0) {
        commentBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const postCard = this.closest('.post-card');
                const commentsSection = postCard.querySelector('.post-comments');
                
                if (commentsSection.style.display === 'block') {
                    commentsSection.style.display = 'none';
                } else {
                    commentsSection.style.display = 'block';
                }
            });
        });
    }
    
    // Initialize like buttons state
    const likeBtns = document.querySelectorAll('.like-btn');
    if (likeBtns.length > 0) {
        // In a real app, you would check if the user has liked each post
        // For this example, we'll just add the functionality without the initial state
    }
    
    // Messages page - select conversation
    const messageContacts = document.querySelectorAll('.message-contact');
    if (messageContacts.length > 0) {
        messageContacts.forEach(contact => {
            contact.addEventListener('click', function() {
                // Remove active class from all contacts
                messageContacts.forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked contact
                this.classList.add('active');
                
                // In a real app, you would load the conversation here
                // For this example, we'll just show a placeholder
                const chatMessages = document.querySelector('.chat-messages');
                if (chatMessages) {
                    // Clear existing messages
                    chatMessages.innerHTML = '';
                    
                    // Add some placeholder messages
                    const messages = [
                        { sender: 'them', content: 'Hi there!', time: '10:30 AM' },
                        { sender: 'me', content: 'Hello! How are you?', time: '10:32 AM' },
                        { sender: 'them', content: 'I\'m doing well, thanks for asking. How about you?', time: '10:33 AM' },
                        { sender: 'me', content: 'I\'m good too. Just working on some projects.', time: '10:35 AM' }
                    ];
                    
                    messages.forEach(msg => {
                        const messageEl = document.createElement('div');
                        messageEl.className = `chat-message ${msg.sender === 'me' ? 'sent' : 'received'}`;
                        
                        messageEl.innerHTML = `
                            ${msg.sender === 'them' ? `<div class="message-sender">${this.querySelector('h3').textContent}</div>` : ''}
                            <div class="message-content">${msg.content}</div>
                            <div class="message-timestamp">${msg.time}</div>
                        `;
                        
                        chatMessages.appendChild(messageEl);
                    });
                }
                
                // Update chat header
                const chatHeader = document.querySelector('.chat-header');
                if (chatHeader) {
                    const contactName = this.querySelector('h3').textContent;
                    chatHeader.querySelector('h2').textContent = contactName;
                }
            });
        });
    }
    
    // Send message in chat
    const chatForm = document.querySelector('.chat-input form');
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const input = this.querySelector('input');
            const message = input.value.trim();
            
            if (message) {
                const chatMessages = document.querySelector('.chat-messages');
                const messageEl = document.createElement('div');
                messageEl.className = 'chat-message sent';
                
                const now = new Date();
                const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                
                messageEl.innerHTML = `
                    <div class="message-content">${message}</div>
                    <div class="message-timestamp">${time}</div>
                `;
                
                chatMessages.appendChild(messageEl);
                
                // Clear input
                input.value = '';
                
                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        });
    }
});