const WS_URL = `ws://${location.hostname}:8000/ws/events`;
const API_URL = `http://${location.hostname}:8000`;

let ws = null;

function connect() {
    ws = new WebSocket(WS_URL);
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'incident_update') {
            addEvent(data);
            refreshStats();
        }
    };
    ws.onclose = () => setTimeout(connect, 3000);
}

function addEvent(data) {
    const list = document.getElementById('event-list');
    const placeholder = list.querySelector('.placeholder');
    if (placeholder) placeholder.remove();

    const div = document.createElement('div');
    div.className = 'event';
    div.innerHTML = `
        <span class="status ${data.status}">${data.status}</span>
        <span><strong>${data.incident_id?.slice(0, 8)}</strong></span>
        <span>${data.root_cause || data.error || ''}</span>
        <span class="time">${new Date().toLocaleTimeString()}</span>
    `;
    list.prepend(div);
}

async function refreshStats() {
    try {
        const resp = await fetch(`${API_URL}/metrics`);
        const data = await resp.json();
        document.getElementById('total').textContent = data.total || 0;
        document.getElementById('resolved').textContent = data.resolved || 0;
        document.getElementById('failed').textContent = data.failed || 0;
    } catch (e) {
        console.error('Failed to fetch stats');
    }
}

connect();
refreshStats();
setInterval(refreshStats, 10000);
