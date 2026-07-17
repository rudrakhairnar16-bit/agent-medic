const WS_URL = `ws://${location.hostname}:8000/ws/events`;
const API_URL = `http://${location.hostname}:8000`;

let ws = null;

function connect() {
    ws = new WebSocket(WS_URL);
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'incident_update') {
            addEvent(data);
            refreshSummary();
            refreshIncidents();
        }
    };
    ws.onclose = () => setTimeout(connect, 3000);
}

function addEvent(data, persist = true) {
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

    while (list.children.length > 100) {
        list.lastChild.remove();
    }

    if (persist) {
        try {
            const stored = JSON.parse(localStorage.getItem('medic_events') || '[]');
            stored.unshift({ ...data, _ts: Date.now() });
            if (stored.length > 50) stored.length = 50;
            localStorage.setItem('medic_events', JSON.stringify(stored));
        } catch (e) {
            /* localStorage not available */
        }
    }
}

function loadPersistedEvents() {
    try {
        const stored = JSON.parse(localStorage.getItem('medic_events') || '[]');
        stored.forEach(e => addEvent(e, false));
    } catch (e) {
        /* ignore */
    }
}

async function refreshSummary() {
    try {
        const resp = await fetch(`${API_URL}/incidents/stats/summary`);
        const data = await resp.json();
        document.getElementById('total').textContent = data.total || 0;
        document.getElementById('resolved').textContent = data.resolved || 0;
        document.getElementById('failed').textContent = data.failed || 0;
        document.getElementById('open').textContent = data.open || 0;
        document.getElementById('rate').textContent = (data.resolution_rate || 0) + '%';
    } catch (e) {
        console.error('Failed to fetch summary');
    }
}

async function refreshIncidents() {
    try {
        const resp = await fetch(`${API_URL}/incidents?limit=5`);
        const data = await resp.json();
        const list = document.getElementById('recent-list');
        if (!list) return;

        list.innerHTML = '';
        if (!data.incidents || data.incidents.length === 0) {
            list.innerHTML = '<p class="placeholder">No incidents yet</p>';
            return;
        }
        data.incidents.forEach(inc => {
            const div = document.createElement('div');
            div.className = 'event';
            div.innerHTML = `
                <span class="status ${inc.status}">${inc.status}</span>
                <span><strong>${inc.alert_name || 'Unknown'}</strong></span>
                <span>${(inc.message || '').slice(0, 40)}</span>
                <span class="time">${new Date(inc.created_at).toLocaleTimeString()}</span>
            `;
            list.appendChild(div);
        });
    } catch (e) {
        console.error('Failed to fetch incidents');
    }
}

loadPersistedEvents();
connect();
refreshSummary();
refreshIncidents();
setInterval(refreshSummary, 10000);
setInterval(refreshIncidents, 15000);
