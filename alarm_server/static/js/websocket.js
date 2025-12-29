/**
 * WebSocket client for real-time alarm synchronization
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start with 1 second
        this.heartbeatInterval = null;
        this.isConnected = false;
    }

    connect(token) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws?token=${token}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            updateBrowserStatus(true);  // Browser is connected
            this.startHeartbeat();
        };

        this.ws.onmessage = (event) => {
            this.handleMessage(JSON.parse(event.data));
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            updateBrowserStatus(false);  // Browser is disconnected
            this.stopHeartbeat();
            this.attemptReconnect();
        };
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.stopHeartbeat();
        this.isConnected = false;
        updateBrowserStatus(false);
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket is not connected');
        }
    }

    handleMessage(message) {
        console.log('WebSocket message received:', message.type);

        switch (message.type) {
            case 'AUTH_SUCCESS':
                // Update alarm client status from initial connection
                if (message.data && 'alarm_client_connected' in message.data) {
                    updateClientStatus(message.data.alarm_client_connected);
                }
                // Request current state after successful authentication
                this.send({
                    type: 'REQUEST_STATE',
                    timestamp: new Date().toISOString()
                });
                break;

            case 'AUTH_FAILED':
                // Token expired or invalid - logout user
                console.error('Authentication failed:', message.data?.reason);
                showToast('Session expired. Please log in again.');
                this.disconnect();
                // Trigger logout (defined in app.js)
                if (typeof handleLogout === 'function') {
                    handleLogout();
                }
                break;

            case 'CLIENT_STATUS_UPDATE':
                // Server notified us about alarm client status change
                if (message.data && 'alarm_client_connected' in message.data) {
                    updateClientStatus(message.data.alarm_client_connected);
                    const status = message.data.alarm_client_connected ? 'connected' : 'disconnected';
                    showToast(`Alarm client ${status}`);
                }
                break;

            case 'STATE_SYNC':
                // Update local state with server state
                if (message.data && message.data.alarms) {
                    state.alarms = message.data.alarms;
                    renderAlarms();
                    showToast('Alarms synced');
                }
                break;

            case 'SET_ALARM':
                // Server pushed alarm update
                handleAlarmUpdate(message.data, 'SET_ALARM');
                break;

            case 'DELETE_ALARM':
                // Server pushed alarm deletion
                handleAlarmUpdate(message.data, 'DELETE_ALARM');
                break;

            case 'PONG':
                // Heartbeat response
                break;

            default:
                console.warn('Unknown message type:', message.type);
        }
    }

    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({
                    type: 'HEARTBEAT',
                    timestamp: new Date().toISOString()
                });
            }
        }, 30000); // Send heartbeat every 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            showToast('Connection lost. Please refresh the page.');
            return;
        }

        this.reconnectAttempts++;
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

        setTimeout(() => {
            if (state.token) {
                this.connect(state.token);
            }
        }, this.reconnectDelay);

        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 60000);
    }
}

// Initialize WebSocket client
function initWebSocket() {
    window.wsClient = new WebSocketClient();
    window.wsClient.connect(state.token);
}
