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
    startTypingCycle();
    
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
