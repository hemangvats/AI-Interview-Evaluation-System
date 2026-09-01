// State Management
let currentSession = null;
let activeSessionId = null;

// Auth State Management
let authState = {
    isAuthenticated: false,
    currentUser: null,
    accessToken: localStorage.getItem('saathi_access_token') || null,
    refreshToken: localStorage.getItem('saathi_refresh_token') || null
};

// DOM Elements
const newInterviewBtn = document.getElementById('new-interview-btn');
const recentsList = document.getElementById('recents-list');
const settingsForm = document.getElementById('settings-form');
const roleSelect = document.getElementById('role-select');
const resumeFileInput = document.getElementById('resume-file');
const fileNameDisplay = document.getElementById('file-name-display');
const startBtn = document.getElementById('start-btn');

// Auth DOM Elements
const authModalOverlay = document.getElementById('auth-modal-overlay');
const tabLoginBtn = document.getElementById('tab-login-btn');
const tabRegisterBtn = document.getElementById('tab-register-btn');
const authErrorBanner = document.getElementById('auth-error-banner');
const authLoginForm = document.getElementById('auth-login-form');
const authRegisterForm = document.getElementById('auth-register-form');
const userProfileCard = document.getElementById('user-profile-card');
const userDisplayName = document.getElementById('user-display-name');
const userDisplayEmail = document.getElementById('user-display-email');
const logoutBtn = document.getElementById('logout-btn');

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
const typingLabel = document.querySelector('.typing-label');
const questionProgressLabel = document.getElementById('question-progress-label');
const questionProgressFill = document.getElementById('question-progress-fill');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

// Typing state cycling
const TYPING_STATES = [
    'Saathi is thinking...',
    'Evaluating your response...',
    'Preparing next question...'
];
let _typingCycleTimer = null;

function startTypingCycle() {
    if (!typingLabel) return;
    let idx = 0;
    typingLabel.textContent = TYPING_STATES[0];
    _typingCycleTimer = setInterval(() => {
        idx = (idx + 1) % TYPING_STATES.length;
        typingLabel.style.opacity = '0';
        setTimeout(() => {
            if (typingLabel) typingLabel.textContent = TYPING_STATES[idx];
            typingLabel.style.opacity = '1';
        }, 150);
    }, 2200);
}

function stopTypingCycle() {
    clearInterval(_typingCycleTimer);
    _typingCycleTimer = null;
    if (typingLabel) {
        typingLabel.textContent = TYPING_STATES[0];
        typingLabel.style.opacity = '1';
    }
}

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
    checkAuthSession();
    fetchConfig();
    fetchRecents();
    setupEventListeners();
    setupAuthEventListeners();
    setupLinkedInEventListeners();
    setupGitHubEventListeners();
    setupProfileEventListeners();
});

// Global XSS Sanitization Helper
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

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
        const response = await authenticatedFetch('/api/interviews');
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
        const response = await authenticatedFetch(`/api/interviews/${sessionId}`);
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
        const response = await authenticatedFetch(`/api/interviews/${sessionId}`, { method: 'DELETE' });
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
        
        const response = await authenticatedFetch('/api/interviews/start', {
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
    startTypingCycle();
    
    // Add user message locally for instant response feel
    appendUserMessage(answerText);
    scrollToBottom();
    
    try {
        const response = await authenticatedFetch('/api/interviews/answer', {
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
        stopTypingCycle();
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

    // Dashboard Card Click Listeners
    const dashProfileCard = document.getElementById('dash-card-profile');
    if (dashProfileCard) {
        dashProfileCard.addEventListener('click', openProfileModal);
    }

    const dashLinkedinCard = document.getElementById('dash-card-linkedin');
    if (dashLinkedinCard) {
        dashLinkedinCard.addEventListener('click', openLinkedInModal);
    }

    const dashGithubCard = document.getElementById('dash-card-github');
    if (dashGithubCard) {
        dashGithubCard.addEventListener('click', openGitHubModal);
    }

    // Global Keyboard Handler (Escape key closes modals)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal-overlay:not(.hidden), .auth-modal-overlay:not(.hidden)');
            modals.forEach(m => m.classList.add('hidden'));
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

    // Update setup controls active state
    updateSetupControlsState(viewName);
}

function updateSetupControlsState(viewName) {
    const isSessionActive = (viewName === 'chat' || viewName === 'report');
    const sidebarSetup = document.querySelector('.sidebar-setup');
    
    if (sidebarSetup) {
        sidebarSetup.classList.toggle('session-active', isSessionActive);
    }
    
    if (roleSelect) roleSelect.disabled = isSessionActive;
    if (resumeFileInput) {
        resumeFileInput.disabled = isSessionActive;
        const fileLabel = document.querySelector('.file-label');
        if (fileLabel) {
            fileLabel.classList.toggle('disabled', isSessionActive);
        }
    }
    if (startBtn) {
        startBtn.disabled = isSessionActive;
    }
}

function renderChat(session) {
    // Update compact header
    chatTitle.textContent = session.role || 'Interview';
    difficultyBadge.textContent = session.difficulty || 'Adaptive';

    const personalizedBadge = document.getElementById('personalized-badge');
    if (personalizedBadge) {
        const hasProfile = session.candidate_context && session.candidate_context.has_profile;
        if (hasProfile) {
            personalizedBadge.classList.remove('hidden');
        } else {
            personalizedBadge.classList.add('hidden');
        }
    }

    // Progress bar
    const totalQs = session.total_questions || 15;
    const currentQ = (session.current_q_index != null) ? session.current_q_index + 1 : 1;
    if (questionProgressLabel) {
        questionProgressLabel.textContent = `Question ${currentQ} of ${totalQs}`;
    }
    if (questionProgressFill) {
        const pct = Math.min(100, Math.max(2, (currentQ / totalQs) * 100));
        questionProgressFill.style.width = `${pct}%`;
    }

    // Status badge
    if (session.interview_complete) {
        statusBadge.textContent = 'Complete';
        statusBadge.className = 'status-pill status-complete';
    } else {
        statusBadge.textContent = 'Live';
        statusBadge.className = 'status-pill status-active';
    }

    messagesContainer.innerHTML = '';

    session.messages.forEach((msg, idx) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${msg.role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = msg.role === 'assistant'
            ? '<img src="/static/saathi_logo.svg" alt="Saathi" class="avatar-logo-img">'
            : '<i class="fa-solid fa-user"></i>';

        const senderLabel = document.createElement('div');
        senderLabel.className = 'msg-sender';
        senderLabel.textContent = msg.role === 'assistant' ? 'Saathi' : 'You';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        let parsedContent;
        if (msg.role === 'assistant' && idx > 0) {
            parsedContent = parseAssistantFeedback(msg.content);
        } else {
            parsedContent = window.marked ? window.marked.parse(msg.content) : msg.content;
        }
        bubble.innerHTML = parsedContent;

        const body = document.createElement('div');
        body.className = 'msg-body';
        body.appendChild(senderLabel);
        body.appendChild(bubble);

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(body);
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

    const senderLabel = document.createElement('div');
    senderLabel.className = 'msg-sender';
    senderLabel.textContent = 'You';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;

    const body = document.createElement('div');
    body.className = 'msg-body';
    body.appendChild(senderLabel);
    body.appendChild(bubble);

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(body);
    messagesContainer.appendChild(msgDiv);
}

function parseAssistantFeedback(rawText) {
    // Parse the structured feedback format from server.py:
    // **Previous Reply Feedback**:
    // - **Score**: N/10
    // - **Feedback**: ...
    // - **Improvement**: ...
    // 📈/📉 *Difficulty adjusted...*
    // ---
    // **Question N**: ...

    // --- Extract structured parts using regex on raw text ---
    const scoreMatch = rawText.match(/-\s*\*\*Score\*\*:\s*(\d+(?:\.\d+)?)\/10/i);
    const feedbackMatch = rawText.match(/-\s*\*\*Feedback\*\*:\s*([^\n\-]+(?:\n(?!\s*-)(?!\s*\*\*)[^\n]*)*)/i);
    const improvementMatch = rawText.match(/-\s*\*\*Improvement\*\*:\s*([^\n\-]+(?:\n(?!\s*-)(?!\s*\*\*)[^\n]*)*)/i);
    const diffIncreaseMatch = rawText.match(/📈[^\n]*/i);
    const diffDecreaseMatch = rawText.match(/📉[^\n]*/i);

    // Extract next question — everything after '---'
    const separatorIdx = rawText.indexOf('---');
    const afterSeparator = separatorIdx !== -1 ? rawText.slice(separatorIdx + 3).trim() : '';
    const completionMatch = rawText.match(/🎉[^\n]*/i);

    // --- If no structured feedback found, fall back to markdown rendering ---
    const hasStructuredFeedback = scoreMatch || feedbackMatch || improvementMatch;
    if (!hasStructuredFeedback) {
        return window.marked ? window.marked.parse(rawText) : rawText;
    }

    // --- Build the feedback card ---
    const scoreVal = scoreMatch ? parseFloat(scoreMatch[1]) : null;
    let badgeClass = 'needs-improvement';
    let badgeLabel = 'Needs Work';
    if (scoreVal !== null) {
        if (scoreVal >= 8) { badgeClass = 'excellent'; badgeLabel = 'Excellent'; }
        else if (scoreVal >= 6) { badgeClass = 'strong'; badgeLabel = 'Strong'; }
    }

    const feedbackText = feedbackMatch ? feedbackMatch[1].trim() : '';
    const improvementText = improvementMatch ? improvementMatch[1].trim() : '';

    // Difficulty adjustment banner
    let diffBanner = '';
    if (diffIncreaseMatch) {
        let diffText = diffIncreaseMatch[0].replace(/📈\s*\*?/g, '').replace(/\*$/g, '').trim();
        diffText = diffText.replace(/\*/g, '');
        diffBanner = `<div class="difficulty-adjusted-banner up"><i class="fa-solid fa-arrow-trend-up"></i> ${diffText}</div>`;
    } else if (diffDecreaseMatch) {
        let diffText = diffDecreaseMatch[0].replace(/📉\s*\*?/g, '').replace(/\*$/g, '').trim();
        diffText = diffText.replace(/\*/g, '');
        diffBanner = `<div class="difficulty-adjusted-banner down"><i class="fa-solid fa-arrow-trend-down"></i> ${diffText}</div>`;
    }

    let cardHtml = `<div class="feedback-card">`;

    // Header: Score + badge
    cardHtml += `<div class="feedback-card-header">`;
    cardHtml += `<div class="feedback-score-container">`;
    cardHtml += `<span class="feedback-score-label">Score</span>`;
    cardHtml += `<span class="feedback-score-value">${scoreVal !== null ? scoreVal + '/10' : '—'}</span>`;
    cardHtml += `</div>`;
    cardHtml += `<span class="feedback-badge-tag ${badgeClass}">${badgeLabel}</span>`;
    cardHtml += `</div>`;  // end header

    const cleanFeedback = sanitizeFeedbackText(feedbackText);
    const cleanImprovement = sanitizeFeedbackText(improvementText);

    // Content sections
    cardHtml += `<div class="feedback-card-content">`;

    if (cleanFeedback) {
        let sectionTitle = '<i class="fa-solid fa-check feedback-icon-green"></i> What went well';
        if (scoreVal !== null) {
            if (scoreVal === 0) {
                sectionTitle = '<i class="fa-solid fa-triangle-exclamation feedback-icon-red"></i> Why this scored low';
            } else if (scoreVal <= 3) {
                sectionTitle = '<i class="fa-solid fa-circle-exclamation feedback-icon-amber"></i> Key issue';
            }
        }
        cardHtml += `<div class="feedback-section-item">`;
        cardHtml += `<div class="feedback-section-title">${sectionTitle}</div>`;
        cardHtml += `<div class="feedback-section-body">${cleanFeedback}</div>`;
        cardHtml += `</div>`;
    }

    if (cleanImprovement) {
        cardHtml += `<div class="feedback-section-item">`;
        cardHtml += `<div class="feedback-section-title"><i class="fa-solid fa-arrow-right feedback-icon-amber"></i> Improve</div>`;
        cardHtml += `<div class="feedback-section-body">${cleanImprovement}</div>`;
        cardHtml += `</div>`;
    }

    cardHtml += `</div>`;  // end content

    if (diffBanner) cardHtml += diffBanner;

    cardHtml += `</div>`;  // end feedback-card

    // Append next question or completion message below the card
    let followHtml = '';
    if (completionMatch) {
        followHtml = window.marked ? window.marked.parse(afterSeparator || completionMatch[0]) : (afterSeparator || completionMatch[0]);
    } else if (afterSeparator) {
        followHtml = window.marked ? window.marked.parse(afterSeparator) : afterSeparator;
    }

    return cardHtml + (followHtml ? `<div style="margin-top:16px">${followHtml}</div>` : '');
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
    let verdict = session.hiring_decision;
    if (!verdict || verdict === 'Pending' || verdict === 'Decision Pending') {
        // Fallback to the last evaluation's hiring decision
        if (evals.length > 0) {
            const lastEval = evals[evals.length - 1].evaluation || {};
            if (lastEval.hiring_decision) {
                verdict = lastEval.hiring_decision;
            }
        }
    }
    
    // If still not set or pending, compute a verdict based on average score
    if (!verdict || verdict === 'Pending' || verdict === 'Decision Pending') {
        if (avg >= 8) verdict = 'Strong Hire';
        else if (avg >= 6) verdict = 'Hire';
        else if (avg >= 4) verdict = 'Leaning No Hire';
        else verdict = 'No Hire';
    }
    statVerdict.textContent = verdict;
    
    // Reset classes
    hiringCard.className = 'stat-card decision-card';
    const cleanVerdict = verdict.toLowerCase().replace(/\s+/g, '-');
    if (cleanVerdict.includes('strong-hire')) hiringCard.classList.add('strong-hire');
    else if (cleanVerdict.includes('leaning-no-hire')) hiringCard.classList.add('leaning-no-hire');
    else if (cleanVerdict.includes('no-hire')) hiringCard.classList.add('no-hire');
    else if (cleanVerdict.includes('hire')) hiringCard.classList.add('hire');
    
    // Verdict Reasoning
    let reasoning = session.verdict_reasoning;
    if (!reasoning || reasoning === 'No summary reasoning provided.' || reasoning.trim() === '') {
        if (evals.length > 0) {
            const lastEval = evals[evals.length - 1].evaluation || {};
            if (lastEval.verdict_reasoning) {
                reasoning = lastEval.verdict_reasoning;
            }
        }
    }
    
    // User-friendly fallback if still not provided
    if (!reasoning || reasoning === 'No summary reasoning provided.' || reasoning.trim() === '') {
        if (verdict === 'Strong Hire') {
            reasoning = 'The candidate demonstrated exceptional expertise and clear structured communication throughout the assessment, showing strong mastery of the core competencies required for this position.';
        } else if (verdict === 'Hire') {
            reasoning = 'The candidate met all key technical requirements for the position with solid overall performance and clear reasoning. Ready for team alignment and next interview stage.';
        } else if (verdict === 'Leaning No Hire') {
            reasoning = 'The candidate showed promise and base technical concepts but exhibited some knowledge gaps or conceptual inconsistencies that need further review.';
        } else {
            reasoning = 'The candidate did not meet the core technical expectations for this role. Significant training or conceptual preparation is recommended before re-assessment.';
        }
    }
    reportVerdictReasoning.textContent = reasoning;
    
    // Compile Performance Report markdown
    if (session.final_summary) {
        const rawHtml = window.marked ? window.marked.parse(session.final_summary) : session.final_summary;
        reportSummaryMarkdown.innerHTML = makeReportSectionsCollapsible(rawHtml);
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

    // Load Unified Candidate Insights Report
    loadUnifiedCandidateReport(session.session_id);
}

async function loadUnifiedCandidateReport(sessionId) {
    try {
        const response = await authenticatedFetch(`/api/v1/reports/${sessionId}`);
        if (!response.ok) return;
        const report = await response.json();

        // 1. Candidate Overview Card
        const candOverviewCard = document.getElementById('report-candidate-overview');
        if (candOverviewCard && report.overview) {
            candOverviewCard.classList.remove('hidden');
            document.getElementById('report-cand-name').textContent = report.overview.candidate_name || 'Candidate';
            document.getElementById('report-cand-role').textContent = report.overview.target_role || 'Software Engineer';
            document.getElementById('report-cand-date').textContent = report.overview.interview_date || '';

            const candSourcesDiv = document.getElementById('report-cand-sources');
            if (candSourcesDiv && report.overview.source_status) {
                const st = report.overview.source_status;
                candSourcesDiv.innerHTML = `
                    <span class="source-status-badge ${st.resume === 'available' ? 'available' : ''}"><i class="fa-solid fa-file-pdf"></i> Resume ${st.resume === 'available' ? '✓' : '✗'}</span>
                    <span class="source-status-badge ${st.linkedin === 'available' ? 'available' : ''}"><i class="fa-brands fa-linkedin"></i> LinkedIn ${st.linkedin === 'available' ? '✓' : '✗'}</span>
                    <span class="source-status-badge ${st.github === 'available' ? 'available' : ''}"><i class="fa-brands fa-github"></i> GitHub ${st.github === 'available' ? '✓' : '✗'}</span>
                `;
            }
        }

        // 2. Metric Score Cards (Kept Strictly Separate!)
        if (report.profile_evidence) {
            const pe = report.profile_evidence;
            document.getElementById('stat-resume-ats').textContent = pe.resume_ats_score ? `${pe.resume_ats_score}/100` : '—';
            document.getElementById('stat-linkedin-score').textContent = pe.linkedin_score ? `${pe.linkedin_score}/100` : '—';
            document.getElementById('stat-github-score').textContent = pe.github_score ? `${pe.github_score}/100` : '—';
        }

        // 3. Skill Validation Matrix Table
        const matrixBody = document.getElementById('report-skill-matrix-body');
        const sectionSkillMatrix = document.getElementById('section-skill-matrix');
        if (matrixBody && report.skill_validation && report.skill_validation.length > 0) {
            if (sectionSkillMatrix) sectionSkillMatrix.classList.remove('hidden');
            matrixBody.innerHTML = '';
            report.skill_validation.forEach(item => {
                const tr = document.createElement('tr');
                let statusClass = 'status-not-assessed';
                if (item.status === 'Demonstrated') statusClass = 'status-demonstrated';
                else if (item.status === 'Partially Demonstrated') statusClass = 'status-partially';

                const sourcesHtml = item.profile_sources.map(src => `<span class="source-mini-tag">${src}</span>`).join(' ');
                tr.innerHTML = `
                    <td class="font-weight-600">${item.skill}</td>
                    <td>${sourcesHtml || 'Profile Claim'}</td>
                    <td class="text-sub">${item.interview_evidence}</td>
                    <td><span class="matrix-status-pill ${statusClass}">${item.status}</span></td>
                `;
                matrixBody.appendChild(tr);
            });
        } else if (sectionSkillMatrix) {
            sectionSkillMatrix.classList.add('hidden');
        }

        // 4. Project Validation List
        const projectList = document.getElementById('report-project-matrix-list');
        const sectionProjectMatrix = document.getElementById('section-project-matrix');
        if (projectList && report.project_validation && report.project_validation.length > 0) {
            if (sectionProjectMatrix) sectionProjectMatrix.classList.remove('hidden');
            projectList.innerHTML = '';
            report.project_validation.forEach(prj => {
                const pcard = document.createElement('div');
                pcard.className = 'timeline-item-card';
                let statusClass = 'status-not-assessed';
                if (prj.status === 'Demonstrated') statusClass = 'status-demonstrated';
                else if (prj.status === 'Partially Demonstrated') statusClass = 'status-partially';

                pcard.innerHTML = `
                    <div class="timeline-item-header">
                        <span class="timeline-item-title">${prj.project_title}</span>
                        <span class="matrix-status-pill ${statusClass}">${prj.status}</span>
                    </div>
                    <p class="timeline-item-sub margin-top-4">${prj.interview_evidence}</p>
                `;
                projectList.appendChild(pcard);
            });
        } else if (sectionProjectMatrix) {
            sectionProjectMatrix.classList.add('hidden');
        }

        // 5. Strengths & Gaps
        const demStrengthsList = document.getElementById('report-demonstrated-strengths');
        if (demStrengthsList && report.demonstrated_strengths) {
            demStrengthsList.innerHTML = report.demonstrated_strengths.map(s => `<li><i class="fa-solid fa-circle-check icon-emerald"></i> ${s}</li>`).join('');
        }

        const devGapsList = document.getElementById('report-development-gaps');
        if (devGapsList && report.development_gaps) {
            devGapsList.innerHTML = report.development_gaps.map(g => `<li><i class="fa-solid fa-circle-exclamation icon-amber"></i> ${g}</li>`).join('');
        }

        // 6. Actionable Recommendations & Future Focus
        const recList = document.getElementById('report-recommendations-list');
        if (recList && report.recommendations) {
            const items = [...report.recommendations, ...(report.future_interview_focus || [])];
            recList.innerHTML = items.map(r => `<li><i class="fa-solid fa-arrow-right icon-emerald"></i> ${r}</li>`).join('');
        }

    } catch (err) {
        console.error('Error fetching unified candidate report:', err);
    }
}

function makeReportSectionsCollapsible(htmlContent) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;
    
    const headings = tempDiv.querySelectorAll('h2');
    if (headings.length === 0) {
        return htmlContent;
    }
    
    const wrapper = document.createElement('div');
    wrapper.className = 'collapsible-report-sections';
    
    // Grab any elements before the first h2
    const firstHeading = headings[0];
    let introSibling = tempDiv.firstElementChild;
    while (introSibling && introSibling !== firstHeading) {
        const nextSibling = introSibling.nextElementSibling;
        wrapper.appendChild(introSibling);
        introSibling = nextSibling;
    }
    
    headings.forEach((heading, idx) => {
        const details = document.createElement('details');
        details.className = 'report-details-section';
        // Open the first section by default (Executive Summary)
        if (idx === 0) {
            details.open = true;
        }
        
        const summary = document.createElement('summary');
        summary.className = 'report-section-summary';
        
        summary.innerHTML = `
            <span class="report-section-title">${heading.innerHTML}</span>
            <i class="fa-solid fa-chevron-down report-section-chevron"></i>
        `;
        
        details.appendChild(summary);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'report-section-content';
        
        let sibling = heading.nextElementSibling;
        while (sibling && sibling.tagName !== 'H2') {
            const nextSibling = sibling.nextElementSibling;
            contentDiv.appendChild(sibling);
            sibling = nextSibling;
        }
        
        details.appendChild(contentDiv);
        wrapper.appendChild(details);
    });
    
    return wrapper.outerHTML;
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

function sanitizeFeedbackText(text) {
    if (!text) return '';
    
    let cleaned = text.trim();
    
    // Handle empty python list string literally
    if (cleaned === '[]' || cleaned === '[""]' || cleaned === "['']") {
        return '';
    }
    
    // Check if it's a JSON or Python list representation like ["A", "B"] or ['A', 'B']
    if (cleaned.startsWith('[') && cleaned.endsWith(']')) {
        try {
            let jsonText = cleaned.replace(/'/g, '"');
            const arr = JSON.parse(jsonText);
            if (Array.isArray(arr)) {
                return arr.map(item => sanitizeFeedbackText(item)).filter(Boolean).join('<br>');
            }
        } catch (e) {
            let content = cleaned.slice(1, -1).trim();
            if (!content) return '';
            const items = content.split(/['"],\s*['"]|",\s*"|',\s*'/).map(item => {
                return item.replace(/^['"]|['"]$/g, '').trim();
            }).filter(Boolean);
            if (items.length > 0) {
                return items.map(item => sanitizeFeedbackText(item)).filter(Boolean).join('<br>');
            }
        }
    }
    
    // Strip bold Markdown **bold** -> bold
    cleaned = cleaned.replace(/\*\*([^*]+)\*\*/g, '$1');
    // Strip italic Markdown *italic* -> italic
    cleaned = cleaned.replace(/\*([^*]+)\*/g, '$1');
    // Strip any residual single/double asterisks
    cleaned = cleaned.replace(/\*/g, '');

    // Split lines and clean leading list bullet characters or numbers
    const lines = cleaned.split('\n').map(line => {
        let l = line.trim();
        // Remove leading bullets or numberings
        l = l.replace(/^[-*•]\s+/, '');
        l = l.replace(/^\d+\.\s+/, '');
        // Remove any residual quotes
        l = l.replace(/^['"]|['"]$/g, '');
        return l.trim();
    }).filter(Boolean);

    if (lines.length > 1) {
        return lines.map(l => `• ${l}`).join('<br>');
    }
    return lines[0] || '';
}

// ----------------------------------------
// Auth & JWT Token Handlers
// ----------------------------------------

async function checkAuthSession() {
    if (!authState.accessToken) {
        showAuthModal(true);
        return;
    }
    try {
        const res = await authenticatedFetch('/api/v1/auth/me');
        if (res.ok) {
            const user = await res.json();
            authState.currentUser = user;
            authState.isAuthenticated = true;
            updateUserUI(user);
            showAuthModal(false);
        } else {
            showAuthModal(true);
        }
    } catch (e) {
        console.error('Auth check error:', e);
        showAuthModal(true);
    }
}

function updateUserUI(user) {
    if (userProfileCard && user) {
        if (userDisplayName) userDisplayName.textContent = user.full_name || 'Candidate';
        if (userDisplayEmail) userDisplayEmail.textContent = user.email || '';
        userProfileCard.classList.remove('hidden');
    } else if (userProfileCard) {
        userProfileCard.classList.add('hidden');
    }
}

function showAuthModal(show) {
    if (authModalOverlay) {
        if (show) {
            authModalOverlay.classList.remove('hidden');
        } else {
            authModalOverlay.classList.add('hidden');
        }
    }
}

function setAuthTokens(access, refresh) {
    authState.accessToken = access;
    authState.refreshToken = refresh;
    if (access) localStorage.setItem('saathi_access_token', access);
    else localStorage.removeItem('saathi_access_token');
    
    if (refresh) localStorage.setItem('saathi_refresh_token', refresh);
    else localStorage.removeItem('saathi_refresh_token');
}

function clearAuthTokens() {
    authState.accessToken = null;
    authState.refreshToken = null;
    authState.currentUser = null;
    authState.isAuthenticated = false;
    localStorage.removeItem('saathi_access_token');
    localStorage.removeItem('saathi_refresh_token');
}

async function authenticatedFetch(url, options = {}) {
    options.headers = options.headers || {};
    if (authState.accessToken) {
        options.headers['Authorization'] = `Bearer ${authState.accessToken}`;
    }
    
    let response = await fetch(url, options);
    
    // Auto refresh token if 401 response received
    if (response.status === 401 && authState.refreshToken) {
        const refreshSuccess = await performTokenRefresh();
        if (refreshSuccess) {
            options.headers['Authorization'] = `Bearer ${authState.accessToken}`;
            response = await fetch(url, options);
        } else {
            logoutUser();
        }
    }
    return response;
}

async function performTokenRefresh() {
    if (!authState.refreshToken) return false;
    try {
        const res = await fetch('/api/v1/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: authState.refreshToken })
        });
        if (!res.ok) return false;
        const tokens = await res.json();
        setAuthTokens(tokens.access_token, tokens.refresh_token);
        return true;
    } catch (e) {
        console.error('Token refresh error:', e);
        return false;
    }
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    hideAuthError();
    const email = document.getElementById('login-email-input').value.trim();
    const password = document.getElementById('login-password-input').value;
    
    const submitBtn = document.getElementById('login-submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Authenticating...';
    
    try {
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Invalid email or password');
        }
        
        const tokens = await response.json();
        setAuthTokens(tokens.access_token, tokens.refresh_token);
        
        await checkAuthSession();
    } catch (err) {
        showAuthError(err.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Sign In</span> <i class="fa-solid fa-arrow-right"></i>';
    }
}

async function handleRegisterSubmit(e) {
    e.preventDefault();
    hideAuthError();
    const fullName = document.getElementById('register-name-input').value.trim();
    const email = document.getElementById('register-email-input').value.trim();
    const password = document.getElementById('register-password-input').value;
    
    if (password.length < 8) {
        showAuthError('Password must be at least 8 characters long.');
        return;
    }
    
    const submitBtn = document.getElementById('register-submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Creating Account...';
    
    try {
        const regResponse = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: fullName, email, password })
        });
        
        if (!regResponse.ok) {
            const err = await regResponse.json();
            throw new Error(err.detail || 'Registration failed');
        }
        
        // Auto-login after registration
        const loginResponse = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (!loginResponse.ok) throw new Error('Account created! Please sign in.');
        
        const tokens = await loginResponse.json();
        setAuthTokens(tokens.access_token, tokens.refresh_token);
        
        await checkAuthSession();
    } catch (err) {
        showAuthError(err.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Create Account</span> <i class="fa-solid fa-user-plus"></i>';
    }
}

function logoutUser() {
    clearAuthTokens();
    updateUserUI(null);
    showAuthModal(true);
}

function showAuthError(msg) {
    if (authErrorBanner) {
        authErrorBanner.textContent = msg;
        authErrorBanner.classList.remove('hidden');
    }
}

function hideAuthError() {
    if (authErrorBanner) {
        authErrorBanner.textContent = '';
        authErrorBanner.classList.add('hidden');
    }
}

function setupAuthEventListeners() {
    if (tabLoginBtn && tabRegisterBtn) {
        tabLoginBtn.addEventListener('click', () => {
            tabLoginBtn.classList.add('active');
            tabRegisterBtn.classList.remove('active');
            authLoginForm.classList.remove('hidden');
            authRegisterForm.classList.add('hidden');
            hideAuthError();
        });
        
        tabRegisterBtn.addEventListener('click', () => {
            tabRegisterBtn.classList.add('active');
            tabLoginBtn.classList.remove('active');
            authRegisterForm.classList.remove('hidden');
            authLoginForm.classList.add('hidden');
            hideAuthError();
        });
    }
    
    if (authLoginForm) {
        authLoginForm.addEventListener('submit', handleLoginSubmit);
    }
    
    if (authRegisterForm) {
        authRegisterForm.addEventListener('submit', handleRegisterSubmit);
    }
    
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logoutUser);
    }
}

/* ── MODAL OPENING HELPER FUNCTIONS ── */
function openLinkedInModal() {
    const modal = document.getElementById('linkedin-modal');
    if (modal) {
        modal.classList.remove('hidden');
        closeMobileDrawer();
    }
}

function openGitHubModal() {
    const modal = document.getElementById('github-modal');
    if (modal) {
        modal.classList.remove('hidden');
        closeMobileDrawer();
    }
}

function openProfileModal() {
    const modal = document.getElementById('profile-modal');
    if (modal) {
        modal.classList.remove('hidden');
        loadCandidateProfile();
        closeMobileDrawer();
    }
}

/* ── LINKEDIN INTEGRATION HANDLERS ── */
function setupLinkedInEventListeners() {
    const openBtn = document.getElementById('open-linkedin-modal');
    const closeBtn = document.getElementById('close-linkedin-modal');
    const modal = document.getElementById('linkedin-modal');
    const form = document.getElementById('linkedin-form');
    const urlInput = document.getElementById('linkedin-url-input');
    const loadingState = document.getElementById('linkedin-loading');
    const errorState = document.getElementById('linkedin-error');
    const errorText = document.getElementById('linkedin-error-text');
    const resultsContainer = document.getElementById('linkedin-results');

    if (openBtn) {
        openBtn.addEventListener('click', openLinkedInModal);
    }

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
        });
    }

    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const profileUrl = urlInput.value.trim();
            if (!profileUrl) return;

            // UI State: Analyzing
            loadingState.classList.remove('hidden');
            errorState.classList.add('hidden');
            resultsContainer.classList.add('hidden');

            try {
                const response = await authenticatedFetch('/api/v1/linkedin/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ profile_url: profileUrl })
                });

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || 'Failed to analyze LinkedIn profile.');
                }

                const data = await response.json();

                // UI State: Success
                document.getElementById('li-overall-score').textContent = data.linkedin_score || 75;
                document.getElementById('li-visibility-score').textContent = data.recruiter_visibility_score || 75;
                document.getElementById('li-headline-review').textContent = data.headline_review || 'No review available.';
                document.getElementById('li-improved-headline').textContent = data.improved_headline || 'N/A';
                document.getElementById('li-about-review').textContent = data.about_review || 'No review available.';
                document.getElementById('li-improved-about').textContent = data.improved_about || 'N/A';

                const suggestionsList = document.getElementById('li-suggestions-list');
                suggestionsList.innerHTML = '';
                (data.optimization_suggestions || []).forEach(s => {
                    const li = document.createElement('li');
                    li.textContent = s;
                    suggestionsList.appendChild(li);
                });

                const keywordsBox = document.getElementById('li-keywords-tags');
                keywordsBox.innerHTML = '';
                (data.missing_keywords || []).forEach(kw => {
                    const tag = document.createElement('span');
                    tag.className = 'keyword-tag';
                    tag.textContent = kw;
                    keywordsBox.appendChild(tag);
                });

                resultsContainer.classList.remove('hidden');
            } catch (err) {
                // UI State: Error
                errorText.textContent = err.message;
                errorState.classList.remove('hidden');
            } finally {
                loadingState.classList.add('hidden');
            }
        });
    }
}

/* ── GITHUB INTEGRATION HANDLERS ── */
function setupGitHubEventListeners() {
    const openBtn = document.getElementById('open-github-modal');
    const closeBtn = document.getElementById('close-github-modal');
    const modal = document.getElementById('github-modal');
    const form = document.getElementById('github-form');
    const usernameInput = document.getElementById('github-username-input');
    const loadingState = document.getElementById('github-loading');
    const errorState = document.getElementById('github-error');
    const errorText = document.getElementById('github-error-text');
    const resultsContainer = document.getElementById('github-results');

    if (openBtn) {
        openBtn.addEventListener('click', openGitHubModal);
    }

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
        });
    }

    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const inputVal = usernameInput.value.trim();
            if (!inputVal) return;

            // UI State: Analyzing
            loadingState.classList.remove('hidden');
            errorState.classList.add('hidden');
            resultsContainer.classList.add('hidden');

            try {
                const response = await authenticatedFetch('/api/v1/github/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: inputVal })
                });

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || 'Failed to analyze GitHub profile.');
                }

                const data = await response.json();

                // UI State: Success
                document.getElementById('gh-overall-score').textContent = data.github_score || 75;
                document.getElementById('gh-depth-score').textContent = data.technical_depth_score || 70;
                document.getElementById('gh-readiness-score').textContent = data.hiring_readiness_score || 70;

                // Languages tags
                const langBox = document.getElementById('gh-languages-tags');
                langBox.innerHTML = '';
                (data.languages_extracted || []).forEach(lang => {
                    const tag = document.createElement('span');
                    tag.className = 'keyword-tag';
                    tag.textContent = lang;
                    langBox.appendChild(tag);
                });

                // Repo highlights
                document.getElementById('gh-best-documented-repo').textContent = data.best_documented_repo || 'N/A';
                document.getElementById('gh-most-active-repo').textContent = data.most_active_repo || 'N/A';
                document.getElementById('gh-largest-project').textContent = data.largest_project || 'N/A';

                // README evaluation
                document.getElementById('gh-readme-eval').textContent = data.readme_evaluations || 'No critique available.';

                // Portfolio recommendations
                const recsList = document.getElementById('gh-recommendations-list');
                recsList.innerHTML = '';
                (data.missing_project_recommendations || []).forEach(r => {
                    const li = document.createElement('li');
                    li.textContent = r;
                    recsList.appendChild(li);
                });

                // Improvement suggestions
                const suggsList = document.getElementById('gh-suggestions-list');
                suggsList.innerHTML = '';
                (data.improvement_suggestions || []).forEach(s => {
                    const li = document.createElement('li');
                    li.textContent = s;
                    suggsList.appendChild(li);
                });

                resultsContainer.classList.remove('hidden');
            } catch (err) {
                // UI State: Error
                errorText.textContent = err.message;
                errorState.classList.remove('hidden');
            } finally {
                loadingState.classList.add('hidden');
            }
        });
    }
}

/* ── UNIFIED CANDIDATE PROFILE HANDLERS ── */
function setupProfileEventListeners() {
    const openBtn = document.getElementById('open-profile-modal');
    const closeBtn = document.getElementById('close-profile-modal');
    const modal = document.getElementById('profile-modal');

    if (openBtn) {
        openBtn.addEventListener('click', openProfileModal);
    }

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
        });
    }

    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    }
}

async function loadCandidateProfile() {
    const loadingState = document.getElementById('profile-loading');
    const contentBox = document.getElementById('profile-content');
    if (!loadingState || !contentBox) return;

    loadingState.classList.remove('hidden');
    contentBox.classList.add('hidden');

    try {
        const response = await authenticatedFetch('/api/v1/profile');
        if (!response.ok) {
            throw new Error('Failed to load candidate profile.');
        }

        const data = await response.json();

        // Update Source Status Badges
        const srcStatus = data.source_status || {};
        updateSourceBadge('resume', srcStatus.resume || 'not_provided');
        updateSourceBadge('linkedin', srcStatus.linkedin || 'not_provided');
        updateSourceBadge('github', srcStatus.github || 'not_provided');

        // Skills with source icons
        const skillsBox = document.getElementById('profile-skills-tags');
        skillsBox.innerHTML = '';
        (data.unified_skills || []).forEach(item => {
            const tag = document.createElement('div');
            tag.className = 'skill-provenance-tag';

            let iconsHtml = '';
            (item.sources || []).forEach(src => {
                if (src === 'resume') iconsHtml += '<i class="fa-solid fa-file-pdf" title="Resume Evidence"></i>';
                if (src === 'linkedin') iconsHtml += '<i class="fa-brands fa-linkedin" title="LinkedIn Evidence"></i>';
                if (src === 'github') iconsHtml += '<i class="fa-brands fa-github" title="GitHub Evidence"></i>';
            });

            tag.innerHTML = `<span>${item.skill}</span><span class="provenance-icons">${iconsHtml}</span>`;
            skillsBox.appendChild(tag);
        });

        // Consistency Report
        const report = data.consistency_report || {};
        document.getElementById('profile-consistency-score').textContent = report.consistency_score || 80;

        const claimsList = document.getElementById('profile-consistent-claims');
        claimsList.innerHTML = '';
        (report.consistent_claims || []).forEach(c => {
            const li = document.createElement('li');
            li.textContent = c;
            claimsList.appendChild(li);
        });

        const missingList = document.getElementById('profile-missing-evidence');
        missingList.innerHTML = '';
        (report.missing_evidence || []).forEach(m => {
            const li = document.createElement('li');
            li.textContent = m;
            missingList.appendChild(li);
        });

        // Experience Timeline
        const expBox = document.getElementById('profile-experience-list');
        expBox.innerHTML = '';
        (data.unified_experience || []).forEach(exp => {
            const card = document.createElement('div');
            card.className = 'timeline-item-card';
            card.innerHTML = `
                <div class="timeline-item-header">
                    <span class="timeline-item-title">${exp.role} @ ${exp.company}</span>
                    <span class="keyword-tag">${exp.dates || 'N/A'}</span>
                </div>
                ${exp.description ? `<p class="timeline-item-sub">${exp.description}</p>` : ''}
            `;
            expBox.appendChild(card);
        });

        // Projects
        const projBox = document.getElementById('profile-projects-list');
        projBox.innerHTML = '';
        (data.unified_projects || []).forEach(p => {
            const card = document.createElement('div');
            card.className = 'timeline-item-card';
            card.innerHTML = `
                <div class="timeline-item-header">
                    <span class="timeline-item-title">${p.title}</span>
                    <span class="keyword-tag">${(p.sources || []).join(', ')}</span>
                </div>
                ${p.description ? `<p class="timeline-item-sub">${p.description}</p>` : ''}
            `;
            projBox.appendChild(card);
        });

        // Strengths & Recommendations
        const strengthsList = document.getElementById('profile-strengths-list');
        strengthsList.innerHTML = '';
        (data.strengths || []).forEach(s => {
            const li = document.createElement('li');
            li.textContent = s;
            strengthsList.appendChild(li);
        });

        const recsList = document.getElementById('profile-recommendations-list');
        recsList.innerHTML = '';
        (data.recommendations || []).forEach(r => {
            const li = document.createElement('li');
            li.textContent = r;
            recsList.appendChild(li);
        });

        contentBox.classList.remove('hidden');
    } catch (err) {
        console.error('Candidate Profile Error:', err);
    } finally {
        loadingState.classList.add('hidden');
    }
}

function updateSourceBadge(sourceKey, status) {
    const badge = document.getElementById(`status-badge-${sourceKey}`);
    const textSpan = document.getElementById(`status-text-${sourceKey}`);
    if (!badge || !textSpan) return;

    textSpan.textContent = status === 'available' ? 'Available ✓' : status.replace('_', ' ');
    if (status === 'available') {
        badge.classList.add('available');
    } else {
        badge.classList.remove('available');
    }
}



