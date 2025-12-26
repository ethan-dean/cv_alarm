/**
 * Main application logic for CV Alarm frontend
 */

// Global state
const state = {
    token: null,
    alarms: [],
    editingAlarmId: null
};

// API Configuration
const API_BASE = window.location.origin;
const API_URL = `${API_BASE}/api`;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    // Check for existing token
    const savedToken = localStorage.getItem('alarm_token');
    if (savedToken) {
        state.token = savedToken;
        showAlarmScreen();
        loadAlarms();
        initWebSocket();
    } else {
        showLoginScreen();
    }

    // Setup event listeners
    setupEventListeners();
});

function setupEventListeners() {
    // Login form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);

    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Add alarm button
    document.getElementById('addAlarmBtn').addEventListener('click', showAddAlarmModal);

    // Modal buttons
    document.getElementById('cancelAlarmBtn').addEventListener('click', hideAlarmModal);
    document.getElementById('saveAlarmBtn').addEventListener('click', handleSaveAlarm);

    // Day pills
    document.querySelectorAll('.day-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            pill.classList.toggle('selected');
            pill.classList.toggle('bg-gray-200');
            pill.classList.toggle('text-gray-700');
        });
    });
}

// Authentication
async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            throw new Error('Invalid credentials');
        }

        const data = await response.json();
        state.token = data.access_token;
        localStorage.setItem('alarm_token', state.token);

        showAlarmScreen();
        loadAlarms();
        initWebSocket();
    } catch (error) {
        showError('loginError', 'Invalid username or password');
    }
}

function handleLogout() {
    state.token = null;
    state.alarms = [];
    localStorage.removeItem('alarm_token');

    if (window.wsClient) {
        window.wsClient.disconnect();
    }

    showLoginScreen();
}

// Alarm CRUD operations
async function loadAlarms() {
    try {
        const response = await fetch(`${API_URL}/alarms`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load alarms');
        }

        state.alarms = await response.json();
        renderAlarms();
    } catch (error) {
        showToast('Failed to load alarms');
        console.error(error);
    }
}

async function createAlarm(alarmData) {
    try {
        const response = await fetch(`${API_URL}/alarms`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify(alarmData)
        });

        if (!response.ok) {
            throw new Error('Failed to create alarm');
        }

        const newAlarm = await response.json();
        state.alarms.push(newAlarm);
        renderAlarms();
        showToast('Alarm created');
    } catch (error) {
        showToast('Failed to create alarm');
        console.error(error);
    }
}

async function updateAlarm(alarmId, alarmData) {
    try {
        const response = await fetch(`${API_URL}/alarms/${alarmId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify(alarmData)
        });

        if (!response.ok) {
            throw new Error('Failed to update alarm');
        }

        const updatedAlarm = await response.json();
        const index = state.alarms.findIndex(a => a.id === alarmId);
        if (index !== -1) {
            state.alarms[index] = updatedAlarm;
        }
        renderAlarms();
        showToast('Alarm updated');
    } catch (error) {
        showToast('Failed to update alarm');
        console.error(error);
    }
}

async function deleteAlarm(alarmId) {
    if (!confirm('Are you sure you want to delete this alarm?')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/alarms/${alarmId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to delete alarm');
        }

        state.alarms = state.alarms.filter(a => a.id !== alarmId);
        renderAlarms();
        showToast('Alarm deleted');
    } catch (error) {
        showToast('Failed to delete alarm');
        console.error(error);
    }
}

async function toggleAlarm(alarmId, enabled) {
    try {
        const response = await fetch(`${API_URL}/alarms/${alarmId}/toggle`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ enabled })
        });

        if (!response.ok) {
            throw new Error('Failed to toggle alarm');
        }

        const updatedAlarm = await response.json();
        const index = state.alarms.findIndex(a => a.id === alarmId);
        if (index !== -1) {
            state.alarms[index] = updatedAlarm;
        }
        renderAlarms();
    } catch (error) {
        showToast('Failed to toggle alarm');
        console.error(error);
    }
}

// Helper functions
function showLoginScreen() {
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('alarmScreen').classList.add('hidden');
}

function showAlarmScreen() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('alarmScreen').classList.remove('hidden');
}

function showError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
}

function getDayName(dayIndex) {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days[dayIndex];
}

function getRepeatText(repeatDays) {
    if (repeatDays.length === 0) {
        return 'Never';
    }
    if (repeatDays.length === 7) {
        return 'Every day';
    }
    if (repeatDays.length === 5 && repeatDays.every(d => d < 5)) {
        return 'Weekdays';
    }
    if (repeatDays.length === 2 && repeatDays.includes(5) && repeatDays.includes(6)) {
        return 'Weekends';
    }
    return repeatDays.map(d => getDayName(d)).join(', ');
}
