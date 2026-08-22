// State Management
let currentSession = null;
let activeSessionId = null;

// DOM Elements
const newInterviewBtn = document.getElementById('new-interview-btn');
const recentsList = document.getElementById('recents-list');
const settingsForm = document.getElementById('settings-form');
const roleSelect = document.getElementById('role-select');
const resumeFileInput = document.getElementById('resume-file');
const fileNameDisplay = document.getElementById('file-name-display');
const startBtn = document.getElementById('start-btn');

// View Containers
const viewEmpty = document.getElementById('view-empty');
const viewChat = document.getElementById('view-chat');
const viewReport = document.getElementById('view-report');

// Chat DOM Elements
const chatTitle = document.getElementById('chat-title');
const difficultyBadge = document.getElementById('difficulty-badge');
const statusBadge = document.getElementById('status-badge');
const messagesContainer = document.getElementById('messages-container');
const typingIndicator = document.getElementById('typing-indicator');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

// Report DOM Elements
const reportNewBtn = document.getElementById('report-new-btn');
const statExchanges = document.getElementById('stat-exchanges');
const statAvgScore = document.getElementById('stat-avg-score');
const statVerdict = document.getElementById('stat-verdict');
const hiringCard = document.getElementById('hiring-card');
const reportVerdictReasoning = document.getElementById('report-verdict-reasoning');
const reportSummaryMarkdown = document.getElementById('report-summary-markdown');
const reportQuestionsBreakdown = document.getElementById('report-questions-breakdown');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    fetchConfig();
    fetchRecents();
    setupEventListeners();
});

// Configure marked options
if (window.marked) {
    window.marked.setOptions({
        breaks: true,
        gfm: true
    });
}

// ----------------------------------------
// API Calls
// ----------------------------------------

async function fetchConfig() {
    const defaultRoles = [
        "AI Engineer", 
        "Software Developer", 
        "Data Scientist", 
        "Web Developer", 
        "Frontend Developer", 
        "Backend Developer"
    ];
    
    function populateRoles(roles) {
        roleSelect.innerHTML = '<option value="" disabled selected>Select Position</option>';
        roles.forEach(role => {
            const option = document.createElement('option');
            option.value = role;
            option.textContent = role;
            roleSelect.appendChild(option);
        });
    }

    try {
        const response = await fetch('/api/config');
        if (!response.ok) throw new Error('Failed to load configuration');
        const data = await response.json();
        populateRoles(data.roles || defaultRoles);
    } catch (error) {
        console.error('Error fetching config, using fallback roles:', error);
        populateRoles(defaultRoles);
    }
}

async function fetchRecents() {
    try {
        const response = await fetch('/api/interviews');
        if (!response.ok) throw new Error('Failed to fetch recent interviews');
        const interviews = await response.json();
        
        renderRecentsList(interviews);
    } catch (error) {
        console.error('Error fetching recents:', error);
        recentsList.innerHTML = '<div class="loading-placeholder">Failed to load recent sessions</div>';
    }
}

async function loadSession(sessionId) {
    try {
        showGlobalLoader(true);
        const response = await fetch(`/api/interviews/${sessionId}`);
        if (!response.ok) throw new Error('Failed to load interview details');
        const session = await response.json();
        
        currentSession = session;
        activeSessionId = sessionId;
        
        updateSidebarActiveState(sessionId);
        closeMobileDrawer();
        
        if (session.interview_complete) {
            showView('report');
            renderReport(session);
        } else {
            showView('chat');
            renderChat(session);
        }
    } catch (error) {
        alert('Error loading session: ' + error.message);
        console.error(error);
    } finally {
        showGlobalLoader(false);
    }
}

function closeMobileDrawer() {
    document.querySelector('.sidebar')?.classList.remove('drawer-open');
    document.getElementById('drawer-overlay')?.classList.remove('active');
}

async function deleteSession(sessionId, event) {
    event.stopPropagation();
    event.preventDefault();

    // Optimistically remove the row from the UI immediately
    const row = document.querySelector(`.recent-item[data-id="${sessionId}"]`);
    if (row) row.remove();

    // If the list is now empty, show placeholder
    if (recentsList.querySelectorAll('.recent-item').length === 0) {
        recentsList.innerHTML = '<div class="loading-placeholder">No recent interviews.</div>';
    }

    // If we deleted the open session, go back to empty state
    if (activeSessionId === sessionId) {
        currentSession = null;
        activeSessionId = null;
        showView('empty');
    }

    try {
        const response = await fetch(`/api/interviews/${sessionId}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete interview');
        // Refresh from server to ensure consistency
        fetchRecents();
    } catch (error) {
        console.error('Error deleting session:', error);
        // Re-fetch to restore correct state if API call failed
        fetchRecents();
    }
}

async function startNewInterview(role, resumeFile) {
    try {
        setStartButtonLoading(true);
        
        const formData = new FormData();
        formData.append('role', role);
        if (resumeFile) {
            formData.append('resume', resumeFile);
        }
        
        const response = await fetch('/api/interviews/start', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to start interview');
        }
        
        const session = await response.json();
        currentSession = session;
        activeSessionId = session.session_id;
        
        showView('chat');
        renderChat(session);
        fetchRecents();
        closeMobileDrawer();
        
        // Reset file upload
        resumeFileInput.value = '';
        fileNameDisplay.textContent = 'Attach Resume';
    } catch (error) {
        alert('Error starting interview: ' + error.message);
        console.error(error);
    } finally {
        setStartButtonLoading(false);
    }
}

async function submitUserAnswer(answerText) {
    if (!answerText.trim() || !activeSessionId) return;
    
    // Clear textbox immediately when data is sent
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Disable inputs & show indicator
    chatInput.disabled = true;
    sendBtn.disabled = true;
    typingIndicator.classList.remove('hidden');
    
    // Add user message locally for instant response feel
    appendUserMessage(answerText);
    scrollToBottom();
    
    try {
        const response = await fetch('/api/interviews/answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: activeSessionId,
                answer: answerText
            })
        });
        
        if (!response.ok) throw new Error('Server evaluation failed');
        const session = await response.json();
        currentSession = session;
        
        // Re-render Chat or trigger completion dashboard
        if (session.interview_complete) {
            // Render the completion message first, then redirect to report
            renderChat(session);
            setTimeout(() => {
                showView('report');
                renderReport(session);
                fetchRecents();
            }, 3000); // Give user 3 seconds to read the transition completion notice
        } else {
            renderChat(session);
        }
    } catch (error) {
        alert('Evaluation Error: ' + error.message);
        console.error(error);
    } finally {
        typingIndicator.classList.add('hidden');
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

// ----------------------------------------
// Event Listeners Setup
// ----------------------------------------

function setupEventListeners() {
    // Mobile drawer toggle
    const menuToggle = document.getElementById('menu-toggle');
    const drawerOverlay = document.getElementById('drawer-overlay');
    const sidebar = document.querySelector('.sidebar');

    function toggleDrawer(open) {
        if (!sidebar || !drawerOverlay) return;
        const shouldOpen = open !== undefined ? open : !sidebar.classList.contains('drawer-open');
        sidebar.classList.toggle('drawer-open', shouldOpen);
        drawerOverlay.classList.toggle('active', shouldOpen);
    }

    if (menuToggle) {
        menuToggle.addEventListener('click', () => toggleDrawer());
    }

    if (drawerOverlay) {
        drawerOverlay.addEventListener('click', () => toggleDrawer(false));
    }

    // New Interview Button click
    newInterviewBtn.addEventListener('click', () => {
        currentSession = null;
        activeSessionId = null;
        updateSidebarActiveState(null);
        showView('empty');
        toggleDrawer(false);
    });

    // Start New Interview from Dashboard click
    reportNewBtn.addEventListener('click', () => {
        currentSession = null;
        activeSessionId = null;
        updateSidebarActiveState(null);
        showView('empty');
        toggleDrawer(false);
    });

    // File input change (resume)
    resumeFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.textContent = e.target.files[0].name;
            fileNameDisplay.style.color = 'var(--t1)';
        } else {
            fileNameDisplay.textContent = 'Attach Resume';
            fileNameDisplay.style.color = '';
        }
    });

    // Form submit
    settingsForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const role = roleSelect.value;
        const file = resumeFileInput.files[0];
        if (!role) {
            alert('Please select a position first.');
            return;
        }
        startNewInterview(role, file);
    });

    // Textarea auto-resize & keypress handlers
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight) + 'px';
    });

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const text = chatInput.value;
            if (text.trim() && activeSessionId) {
                chatInput.value = '';
                chatInput.style.height = 'auto';
                submitUserAnswer(text);
            }
        }
    });

    // Send Button click
    sendBtn.addEventListener('click', () => {
        const text = chatInput.value;
        if (text.trim() && activeSessionId) {
            chatInput.value = '';
            chatInput.style.height = 'auto';
            submitUserAnswer(text);
        }
    });
}

// ----------------------------------------
// Rendering Engine
// ----------------------------------------

function renderRecentsList(interviews) {
    recentsList.innerHTML = '';
    if (interviews.length === 0) {
        recentsList.innerHTML = '<div class="loading-placeholder">No recent interviews.</div>';
        return;
    }
    
    interviews.forEach(item => {
        const row = document.createElement('div');
        row.className = `recent-item ${item.session_id === activeSessionId ? 'active' : ''}`;
        row.setAttribute('data-id', item.session_id);
        row.addEventListener('click', () => loadSession(item.session_id));
        
        // Pretty formatting for date
        let displayDate = item.created_at || '';
        if (displayDate.length >= 10) {
            displayDate = displayDate.substring(0, 10);
        }
        
        row.innerHTML = `
            <div class="recent-info">
                <span class="recent-role">📝 ${item.role}</span>
                <span class="recent-date">${displayDate}</span>
            </div>
            <button class="delete-session-btn" title="Delete record">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        `;
        
        // Delete button listener
        const delBtn = row.querySelector('.delete-session-btn');
        delBtn.addEventListener('click', (e) => deleteSession(item.session_id, e));
        
        recentsList.appendChild(row);
    });
}

function updateSidebarActiveState(sessionId) {
    document.querySelectorAll('.recent-item').forEach(el => {
        if (el.getAttribute('data-id') === sessionId) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });
}

function showView(viewName) {
    viewEmpty.classList.remove('active');
    viewChat.classList.remove('active');
    viewReport.classList.remove('active');
    
    if (viewName === 'empty') viewEmpty.classList.add('active');
    if (viewName === 'chat') viewChat.classList.add('active');
    if (viewName === 'report') viewReport.classList.add('active');
}

function renderChat(session) {
    chatTitle.textContent = `Saathi · ${session.role}`;
    difficultyBadge.textContent = session.difficulty;
    
    if (session.interview_complete) {
        statusBadge.textContent = 'Complete';
        statusBadge.className = 'badge status-complete';
    } else {
        statusBadge.textContent = 'Active';
        statusBadge.className = 'badge status-active';
    }
    
    messagesContainer.innerHTML = '';
    
    session.messages.forEach((msg, idx) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${msg.role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = msg.role === 'assistant' ? '<img src="/static/saathi_logo.svg" alt="Saathi" class="avatar-logo-img">' : '<i class="fa-solid fa-user"></i>';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        // Check if there is evaluations feedback context for the assistant message (excluding the first welcome msg)
        let parsedContent = msg.content;
        if (msg.role === 'assistant' && idx > 0) {
            // Find if there is an evaluation for this step
            // Let's format the feedback to look extremely premium in custom containers
            parsedContent = parseAssistantFeedback(msg.content);
        } else {
            parsedContent = window.marked ? window.marked.parse(msg.content) : msg.content;
        }
        
        bubble.innerHTML = parsedContent;
        
        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        messagesContainer.appendChild(msgDiv);
    });
    
    scrollToBottom();
}

function appendUserMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message user';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fa-solid fa-user"></i>';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    
    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    messagesContainer.appendChild(msgDiv);
}

function parseAssistantFeedback(rawText) {
    // Custom beautifier of feedback blocks:
    // **Previous Reply Feedback**:
    // - **Score**: 8/10
    // - **Feedback**: Excellent explanation...
    // - **Improvement**: You could mention...
    // 📈 *Great job! Increasing difficulty...*
    // ---
    // **Question 2**: Explain HTTP requests...
    
    let html = rawText;
    
    // We will parse standard markdown
    if (window.marked) {
        html = window.marked.parse(rawText);
    }
    
    // Inject Custom Badge styles around score text
    const scoreRegex = /Score<\/strong>:\s*(\d+)\/10/i;
    const scoreMatch = html.match(scoreRegex);
    if (scoreMatch) {
        const scoreVal = parseInt(scoreMatch[1]);
        let badgeClass = 'low';
        if (scoreVal >= 8) badgeClass = 'high';
        else if (scoreVal >= 5) badgeClass = 'medium';
        
        const badgeHtml = `<span class="score-badge ${badgeClass}"><i class="fa-solid fa-gauge-high"></i> Score: ${scoreVal}/10</span>`;
        // Replace the whole list element containing Score or prefix it
        html = html.replace(/<strong>Score<\/strong>:\s*\d+\/10/i, `<strong>Score</strong>: ${badgeHtml}`);
    }
    
    return html;
}

function renderReport(session) {
    const evals = session.evaluations || [];
    statExchanges.textContent = evals.length;
    
    // Calculate Average Score
    let avg = 0;
    if (evals.length > 0) {
        const sum = evals.reduce((acc, curr) => acc + (curr.evaluation.score || 0), 0);
        avg = sum / evals.length;
    }
    statAvgScore.textContent = `${avg.toFixed(1)}/10`;
    
    // Hiring Verdict styling
    const verdict = session.hiring_decision || 'Pending';
    statVerdict.textContent = verdict;
    
    // Reset classes
    hiringCard.className = 'stat-card decision-card';
    const cleanVerdict = verdict.toLowerCase().replace(/\s+/g, '-');
    if (cleanVerdict.includes('strong-hire')) hiringCard.classList.add('strong-hire');
    else if (cleanVerdict.includes('leaning-no-hire')) hiringCard.classList.add('leaning-no-hire');
    else if (cleanVerdict.includes('no-hire')) hiringCard.classList.add('no-hire');
    else if (cleanVerdict.includes('hire')) hiringCard.classList.add('hire');
    
    // Verdict Reasoning
    reportVerdictReasoning.textContent = session.verdict_reasoning || 'No summary reasoning provided.';
    
    // Compile Performance Report markdown
    if (session.final_summary) {
        reportSummaryMarkdown.innerHTML = window.marked ? window.marked.parse(session.final_summary) : session.final_summary;
    } else {
        reportSummaryMarkdown.innerHTML = '<p class="loading-placeholder">Performance report summary unavailable.</p>';
    }
    
    // Question breakdown Accordion
    reportQuestionsBreakdown.innerHTML = '';
    if (evals.length === 0) {
        reportQuestionsBreakdown.innerHTML = '<div class="loading-placeholder">No technical evaluations generated.</div>';
        return;
    }
    
    evals.forEach((ev, idx) => {
        const evalData = ev.evaluation || {};
        const scoreVal = evalData.score || 0;
        let scoreClass = 'low';
        if (scoreVal >= 8) scoreClass = 'high';
        else if (scoreVal >= 5) scoreClass = 'medium';
        
        const item = document.createElement('div');
        item.className = 'breakdown-item';
        
        item.innerHTML = `
            <div class="breakdown-header">
                <span class="breakdown-q-title">Q${idx+1}: ${ev.question}</span>
                <div class="breakdown-badges">
                    <span class="score-badge ${scoreClass}">Score: ${scoreVal}/10</span>
                    <i class="fa-solid fa-chevron-down breakdown-toggle-icon"></i>
                </div>
            </div>
            <div class="breakdown-body">
                <div class="breakdown-row">
                    <div class="breakdown-label">Your Answer</div>
                    <div class="breakdown-text">${ev.answer}</div>
                </div>
                <div class="breakdown-row">
                    <div class="breakdown-label">Evaluator Feedback</div>
                    <div class="breakdown-text">${evalData.feedback || 'No feedback provided.'}</div>
                </div>
                <div class="breakdown-row">
                    <div class="breakdown-label">Key Suggestions</div>
                    <div class="breakdown-text">${evalData.suggestions || 'No improvement suggested.'}</div>
                </div>
            </div>
        `;
        
        // Expand/Collapse logic
        item.querySelector('.breakdown-header').addEventListener('click', () => {
            item.classList.toggle('open');
        });
        
        reportQuestionsBreakdown.appendChild(item);
    });
}

// ----------------------------------------
// UI Helpers
// ----------------------------------------

function scrollToBottom() {
    setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 50);
}

function showGlobalLoader(show) {
    // Basic loading feedback
    if (show) {
        document.body.style.cursor = 'wait';
    } else {
        document.body.style.cursor = 'default';
    }
}

function setStartButtonLoading(loading) {
    if (loading) {
        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Initializing...';
    } else {
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Interview';
    }
}
