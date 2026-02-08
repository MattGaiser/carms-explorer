const messagesEl = document.getElementById('messages');
const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const statusBar = document.getElementById('agent-status');
const fileInput = document.getElementById('file-input');
const uploadBtn = document.getElementById('upload-btn');
const uploadStatus = document.getElementById('upload-status');
const profileBar = document.getElementById('profile-bar');
const profileFilename = document.getElementById('profile-filename');
const profileSummary = document.getElementById('profile-summary');
const clearProfileBtn = document.getElementById('clear-profile-btn');

let sessionId = null;
let agentAvailable = false;
let sending = false;

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

async function checkAgentStatus() {
    try {
        const res = await fetch('/agent/status');
        const data = await res.json();
        agentAvailable = data.available;

        if (agentAvailable) {
            statusBar.textContent = 'AI Agent connected';
            statusBar.className = 'status-bar available';
            input.disabled = false;
            sendBtn.disabled = false;
            input.placeholder = 'Ask about residency programs...';
            uploadBtn.classList.remove('disabled');
        } else {
            statusBar.textContent = 'AI Agent unavailable — set ANTHROPIC_API_KEY to enable chat. API endpoints still work at /docs';
            statusBar.className = 'status-bar unavailable';
            input.placeholder = 'Agent unavailable (no API key)';
            uploadBtn.classList.add('disabled');
        }
    } catch {
        statusBar.textContent = 'Cannot reach API server';
        statusBar.className = 'status-bar unavailable';
        uploadBtn.classList.add('disabled');
    }
}

function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="message-content">${content}</div>`;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
}

function addToolIndicator(toolName) {
    const existing = messagesEl.querySelector('.current-assistant');
    if (existing) {
        const indicator = document.createElement('div');
        indicator.className = 'tool-indicator';
        const labels = {
            'mcp__carms__search_programs': 'Searching programs...',
            'mcp__carms__filter_programs': 'Filtering programs...',
            'mcp__carms__get_program_detail': 'Loading program details...',
            'mcp__carms__compare_programs': 'Comparing programs...',
            'mcp__carms__list_disciplines': 'Loading disciplines...',
            'mcp__carms__list_schools': 'Loading schools...',
            'mcp__carms__get_analytics': 'Loading analytics...',
        };
        indicator.textContent = labels[toolName] || `Using ${toolName}...`;
        existing.querySelector('.message-content').appendChild(indicator);
    }
}

function formatMarkdown(text) {
    // Escape HTML first, then apply markdown formatting
    const escaped = escapeHtml(text);
    return escaped
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}

function showProfileBar(data) {
    profileFilename.textContent = data.filename;
    const parts = [];
    if (data.disciplines_of_interest && data.disciplines_of_interest.length) {
        parts.push(data.disciplines_of_interest.join(', '));
    }
    if (data.geographic_preferences && data.geographic_preferences.length) {
        parts.push(data.geographic_preferences.join(', '));
    }
    if (data.summary) {
        parts.push(data.summary);
    }
    profileSummary.textContent = parts.length ? ' — ' + parts.join(' | ') : '';
    profileBar.style.display = 'flex';
}

function hideProfileBar() {
    profileBar.style.display = 'none';
    profileFilename.textContent = '';
    profileSummary.textContent = '';
}

async function uploadFile(file) {
    if (!file) return;

    if (file.type !== 'application/pdf') {
        uploadStatus.textContent = 'Only PDF files are accepted.';
        uploadStatus.className = 'upload-status error';
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        uploadStatus.textContent = 'File exceeds 10 MB limit.';
        uploadStatus.className = 'upload-status error';
        return;
    }

    uploadStatus.textContent = 'Analysing document...';
    uploadStatus.className = 'upload-status';
    uploadBtn.classList.add('disabled');

    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) {
        formData.append('session_id', sessionId);
    }

    try {
        const res = await fetch('/agent/upload', {
            method: 'POST',
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Upload failed');
        }

        const data = await res.json();
        sessionId = data.session_id;

        uploadStatus.textContent = '';
        const safeName = escapeHtml(data.filename);

        if (!data.has_content) {
            // No useful profile extracted — show specific reason
            hideProfileBar();
            const safeType = data.document_type ? escapeHtml(data.document_type) : null;

            if (data.is_relevant === false && safeType) {
                // Clearly irrelevant document
                addMessage('assistant',
                    `<p><strong>${safeName}</strong> appears to be a <strong>${safeType}</strong>, ` +
                    'which isn\'t a medical career document (CV, personal statement, cover letter, etc.).</p>' +
                    '<p>Please upload a relevant document, or describe your preferences directly, e.g. ' +
                    '<em>"I\'m interested in family medicine programs in Ontario"</em>.</p>'
                );
            } else if (safeType) {
                // Document type was identified but nothing useful extracted
                addMessage('assistant',
                    `<p>I analysed <strong>${safeName}</strong> (detected as <strong>${safeType}</strong>) ` +
                    'but couldn\'t extract medical career profile details from it.</p>' +
                    '<p>Please upload a CV, personal statement, or cover letter, or describe your preferences directly, e.g. ' +
                    '<em>"I\'m interested in family medicine programs in Ontario"</em>.</p>'
                );
            } else {
                // Couldn't even classify the document
                addMessage('assistant',
                    `<p>I uploaded <strong>${safeName}</strong> but couldn't extract profile details from it. ` +
                    'The document may be scanned, image-based, or in an unsupported format.</p>' +
                    '<p>You can still ask me to find programs by describing your preferences directly, e.g. ' +
                    '<em>"I\'m interested in family medicine programs in Ontario"</em>.</p>'
                );
            }
        } else {
            showProfileBar(data);

            // Show welcome message with extracted info (all values escaped)
            let welcomeParts = [`<p>Profile extracted from <strong>${safeName}</strong>.</p>`];
            if (data.disciplines_of_interest && data.disciplines_of_interest.length) {
                const safe = escapeHtml(data.disciplines_of_interest.join(', '));
                welcomeParts.push(`<p><strong>Disciplines:</strong> ${safe}</p>`);
            }
            if (data.geographic_preferences && data.geographic_preferences.length) {
                const safe = escapeHtml(data.geographic_preferences.join(', '));
                welcomeParts.push(`<p><strong>Location preferences:</strong> ${safe}</p>`);
            }
            if (data.summary) {
                welcomeParts.push(`<p>${escapeHtml(data.summary)}</p>`);
            }
            welcomeParts.push('<p>Send a message like <em>"Find matching programs"</em> and I\'ll use your profile to recommend programs.</p>');
            addMessage('assistant', welcomeParts.join(''));
        }

    } catch (err) {
        uploadStatus.textContent = err.message;
        uploadStatus.className = 'upload-status error';
    }

    uploadBtn.classList.remove('disabled');
    fileInput.value = '';
}

async function sendMessage(message) {
    if (sending) return;
    sending = true;

    addMessage('user', `<p>${escapeHtml(message)}</p>`);

    const assistantDiv = addMessage('assistant', '<div class="typing-indicator"><span></span><span></span><span></span></div>');
    assistantDiv.classList.add('current-assistant');

    input.disabled = true;
    sendBtn.disabled = true;

    let fullText = '';

    try {
        const res = await fetch('/agent/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
            }),
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentEvent = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    currentEvent = line.slice(7).trim();
                    continue;
                }
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (currentEvent === 'result' && data.session_id) {
                            sessionId = data.session_id;
                        } else if (currentEvent === 'error' && data.error) {
                            assistantDiv.querySelector('.message-content').innerHTML =
                                `<p>Error: ${escapeHtml(data.error)}</p>`;
                        } else if (data.text) {
                            fullText += data.text;
                            assistantDiv.querySelector('.message-content').innerHTML =
                                `<p>${formatMarkdown(fullText)}</p>`;
                            messagesEl.scrollTop = messagesEl.scrollHeight;
                        } else if (data.tool) {
                            addToolIndicator(data.tool);
                        }
                    } catch {}
                }
            }
        }

        if (!fullText) {
            assistantDiv.querySelector('.message-content').innerHTML =
                '<p>No response received.</p>';
        }

    } catch (err) {
        assistantDiv.querySelector('.message-content').innerHTML =
            `<p>Connection error: ${escapeHtml(err.message)}</p>`;
    }

    assistantDiv.classList.remove('current-assistant');
    input.disabled = false;
    sendBtn.disabled = false;
    sending = false;
    input.focus();
}

form.addEventListener('submit', (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message || !agentAvailable || sending) return;
    input.value = '';
    sendMessage(message);
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        uploadFile(fileInput.files[0]);
    }
});

clearProfileBtn.addEventListener('click', async () => {
    hideProfileBar();
    if (sessionId) {
        try {
            await fetch(`/agent/session/${sessionId}`, { method: 'DELETE' });
        } catch {}
        sessionId = null;
    }
    addMessage('assistant', '<p>Profile cleared. You can upload a new document or continue chatting.</p>');
});

checkAgentStatus();
