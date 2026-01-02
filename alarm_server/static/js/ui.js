/**
 * UI manipulation functions for CV Alarm
 */

// Render alarms list
function renderAlarms() {
    const alarmsList = document.getElementById('alarmsList');
    alarmsList.innerHTML = '';

    if (state.alarms.length === 0) {
        alarmsList.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                No alarms set. Click "Add Alarm" to create one.
            </div>
        `;
        return;
    }

    state.alarms.forEach(alarm => {
        const card = createAlarmCard(alarm);
        alarmsList.appendChild(card);
    });
}

// Create alarm card element
function createAlarmCard(alarm) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-sm p-4 alarm-card';

    const repeatText = getRepeatText(alarm.repeat_days);

    card.innerHTML = `
        <div class="flex justify-between items-center">
            <div class="flex-1 cursor-pointer" onclick="showEditAlarmModal(${alarm.id})">
                <div class="text-2xl font-semibold ${alarm.enabled ? 'text-gray-900' : 'text-gray-400'}">
                    ${alarm.time}
                </div>
                <div class="text-sm ${alarm.enabled ? 'text-gray-600' : 'text-gray-400'}">
                    ${alarm.label}
                </div>
                <div class="text-xs ${alarm.enabled ? 'text-gray-500' : 'text-gray-400'} mt-1">
                    ${repeatText}
                </div>
            </div>
            <div class="flex items-center gap-3">
                <button onclick="deleteAlarm(${alarm.id}); event.stopPropagation();"
                        class="text-red-500 hover:text-red-600 px-2 py-1 rounded"
                        title="Delete alarm">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                </button>
                <input type="checkbox"
                       class="toggle-checkbox"
                       ${alarm.enabled ? 'checked' : ''}
                       onchange="toggleAlarm(${alarm.id}, this.checked)">
            </div>
        </div>
    `;

    return card;
}

// Modal functions
function showAddAlarmModal() {
    state.editingAlarmId = null;
    document.getElementById('modalTitle').textContent = 'Add Alarm';
    document.getElementById('alarmLabel').value = 'Alarm';
    document.getElementById('alarmTime').value = '';

    // Clear day pills
    document.querySelectorAll('.day-pill').forEach(pill => {
        pill.classList.remove('selected');
        pill.classList.add('bg-gray-200', 'text-gray-700');
    });

    document.getElementById('alarmModal').classList.remove('hidden');
}

function showEditAlarmModal(alarmId) {
    const alarm = state.alarms.find(a => a.id === alarmId);
    if (!alarm) return;

    state.editingAlarmId = alarmId;
    document.getElementById('modalTitle').textContent = 'Edit Alarm';
    document.getElementById('alarmLabel').value = alarm.label;
    document.getElementById('alarmTime').value = alarm.time;

    // Set day pills
    document.querySelectorAll('.day-pill').forEach(pill => {
        const day = parseInt(pill.getAttribute('data-day'));
        if (alarm.repeat_days.includes(day)) {
            pill.classList.add('selected');
            pill.classList.remove('bg-gray-200', 'text-gray-700');
        } else {
            pill.classList.remove('selected');
            pill.classList.add('bg-gray-200', 'text-gray-700');
        }
    });

    document.getElementById('alarmModal').classList.remove('hidden');
}

function hideAlarmModal() {
    document.getElementById('alarmModal').classList.add('hidden');
    state.editingAlarmId = null;
}

// Handle save alarm
async function handleSaveAlarm() {
    const label = document.getElementById('alarmLabel').value;
    const time = document.getElementById('alarmTime').value;

    if (!time) {
        showToast('Please select a time');
        return;
    }

    // Get selected days
    const repeatDays = [];
    document.querySelectorAll('.day-pill.selected').forEach(pill => {
        repeatDays.push(parseInt(pill.getAttribute('data-day')));
    });

    const alarmData = {
        label,
        time,
        repeat_days: repeatDays.sort(),
        enabled: true
    };

    if (state.editingAlarmId) {
        await updateAlarm(state.editingAlarmId, alarmData);
    } else {
        await createAlarm(alarmData);
    }

    hideAlarmModal();
}

// Toast notification
function showToast(message) {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');

    toastMessage.textContent = message;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Update browser connection status indicator
function updateBrowserStatus(isConnected) {
    const indicator = document.getElementById('browserStatus');
    if (isConnected) {
        indicator.classList.remove('offline');
        indicator.classList.add('online');
    } else {
        indicator.classList.remove('online');
        indicator.classList.add('offline');
    }
}

// Update alarm client connection status indicator
function updateClientStatus(isConnected) {
    const indicator = document.getElementById('clientStatus');
    if (isConnected) {
        indicator.classList.remove('offline');
        indicator.classList.add('online');
    } else {
        indicator.classList.remove('online');
        indicator.classList.add('offline');
    }
}

// Handle alarm updates from WebSocket
function handleAlarmUpdate(alarmData, action) {
    if (action === 'SET_ALARM') {
        // Update or add alarm
        const index = state.alarms.findIndex(a => a.id === alarmData.id);
        if (index !== -1) {
            state.alarms[index] = alarmData;
        } else {
            state.alarms.push(alarmData);
        }
    } else if (action === 'DELETE_ALARM') {
        // Remove alarm
        state.alarms = state.alarms.filter(a => a.id !== alarmData.id);
    }
    renderAlarms();
}
