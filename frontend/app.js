// Auto-detect API base URL
const API_BASE_URL = window.location.origin + '/api';

let currentThreadId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadThreads();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('newThreadBtn').addEventListener('click', startNewThread);
    document.getElementById('messageInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

async function loadThreads() {
    try {
        const response = await fetch(`${API_BASE_URL}/threads`);
        const data = await response.json();
        displayThreads(data.threads);
    } catch (error) {
        console.error('Error loading threads:', error);
    }
}

function displayThreads(threads) {
    const threadsList = document.getElementById('threadsList');
    threadsList.innerHTML = '';
    
    if (threads.length === 0) {
        threadsList.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">No threads yet</p>';
        return;
    }
    
    threads.forEach(thread => {
        const threadItem = document.createElement('div');
        threadItem.className = 'thread-item';
        if (thread.id === currentThreadId) {
            threadItem.classList.add('active');
        }
        
        threadItem.innerHTML = `
            <h3>${thread.title}</h3>
            <p>${new Date(thread.updated_at).toLocaleDateString()}</p>
            <button class="delete-thread" onclick="deleteThread('${thread.id}', event)">×</button>
        `;
        
        threadItem.addEventListener('click', () => loadThread(thread.id));
        threadsList.appendChild(threadItem);
    });
}

async function loadThread(threadId) {
    currentThreadId = threadId;
    try {
        const response = await fetch(`${API_BASE_URL}/threads/${threadId}`);
        const data = await response.json();
        displayMessages(data.messages);
        loadThreads(); // Refresh to highlight active thread
    } catch (error) {
        console.error('Error loading thread:', error);
    }
}

function displayMessages(messages) {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = '';
    
    if (messages.length === 0) {
        messagesContainer.innerHTML = '<div class="welcome-message"><h2>Start the conversation</h2></div>';
        return;
    }
    
    messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-role">${message.role === 'user' ? 'You' : 'Assistant'}</div>
                <div>${escapeHtml(message.content)}</div>
            </div>
        `;
        messagesContainer.appendChild(messageDiv);
    });
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const prompt = input.value.trim();
    
    if (!prompt) return;
    
    // Disable input
    input.disabled = true;
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="loading"></span>';
    
    // Show user message immediately
    if (currentThreadId) {
        // If thread exists, we'll reload it after response
    } else {
        // Clear welcome message
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer.querySelector('.welcome-message')) {
            messagesContainer.innerHTML = '';
        }
        
        // Show user message
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-role">You</div>
                <div>${escapeHtml(prompt)}</div>
            </div>
        `;
        messagesContainer.appendChild(messageDiv);
    }
    
    // Show loading indicator
    const messagesContainer = document.getElementById('chatMessages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.id = 'loading-message';
    loadingDiv.innerHTML = `
        <div class="message-content">
            <div class="message-role">Assistant</div>
            <div><span class="loading"></span> Thinking...</div>
        </div>
    `;
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                thread_id: currentThreadId
            })
        });
        
        const data = await response.json();
        currentThreadId = data.thread_id;
        
        // Remove loading indicator
        const loading = document.getElementById('loading-message');
        if (loading) loading.remove();
        
        // Reload thread to show all messages
        await loadThread(currentThreadId);
        
        // Clear input
        input.value = '';
        
    } catch (error) {
        console.error('Error sending message:', error);
        const loading = document.getElementById('loading-message');
        if (loading) {
            loading.innerHTML = `
                <div class="message-content">
                    <div class="message-role">Assistant</div>
                    <div>Error: ${error.message}</div>
                </div>
            `;
        }
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = 'Send';
    }
}

function startNewThread() {
    currentThreadId = null;
    document.getElementById('messageInput').value = '';
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = '<div class="welcome-message"><h2>New Conversation</h2><p>Start typing to begin a new conversation.</p></div>';
    loadThreads();
}

async function deleteThread(threadId, event) {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this thread?')) return;
    
    try {
        await fetch(`${API_BASE_URL}/threads/${threadId}`, {
            method: 'DELETE'
        });
        
        if (currentThreadId === threadId) {
            startNewThread();
        } else {
            loadThreads();
        }
    } catch (error) {
        console.error('Error deleting thread:', error);
        alert('Error deleting thread');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
