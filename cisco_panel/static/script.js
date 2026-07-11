let currentPortName = null;
let allPortsData = [];

document.addEventListener('DOMContentLoaded', function () {
    loadAllPorts();
    setInterval(loadAllPorts, 30000);
});

async function loadAllPorts() {
    showStatusMessage("Loading port status...", "info");

    try {
        const response = await fetch('/api/ports');
        const data = await response.json();

        if (data.success && data.ports) {
            allPortsData = data.ports;

            data.ports.forEach(function (port, index) {
                const portIndex = index + 1;
                const portEl = document.querySelector(`.port[data-index="${portIndex}"]`);
                if (portEl) {
                    portEl.setAttribute('data-port', port.name);
                    portEl.setAttribute('onclick', `openPortModal('${port.name}')`);
                    updatePortColor(portEl, port.status, port.mode);
                }
            });

            hideStatusMessage();
        } else {
            showStatusMessage("Failed to load port status", "error");
        }
    } catch (error) {
        showStatusMessage("Connection error: " + error.message, "error");
    }
}

function updatePortColor(portElement, status, mode) {
    portElement.classList.remove('port-up', 'port-down', 'port-trunk', 'port-unknown');

    if (mode === 'trunk') {
        portElement.classList.add('port-trunk');
    } else if (status === 'up' || status === 'connected') {
        portElement.classList.add('port-up');
    } else if (status === 'down' || status === 'notconnect' || status === 'disabled') {
        portElement.classList.add('port-down');
    } else {
        portElement.classList.add('port-unknown');
    }
}

async function openPortModal(portName) {
    currentPortName = portName;
    const urlPortName = portName.replace('/', '-');

    document.getElementById('modal-port-title').textContent = 'Port Settings — ' + portName;
    document.getElementById('modal-overlay').classList.add('active');
    document.getElementById('modal-loading').style.display = 'block';

    try {
        const response = await fetch(`/api/port/${urlPortName}`);
        const data = await response.json();

        document.getElementById('modal-loading').style.display = 'none';

        if (data.success && data.port) {
            fillModalWithPortInfo(data.port);
        } else {
            alert('Error loading port information');
            closeModal();
        }
    } catch (error) {
        document.getElementById('modal-loading').style.display = 'none';
        alert('Error: ' + error.message);
        closeModal();
    }
}

function fillModalWithPortInfo(port) {
    const statusEl = document.getElementById('port-status-text');
    statusEl.className = '';

    if (port.status === 'up') {
        statusEl.textContent = 'UP — Connected';
        statusEl.classList.add('status-up');
    } else if (port.status === 'disabled') {
        statusEl.textContent = 'DISABLED — Shutdown';
        statusEl.classList.add('status-disabled');
    } else {
        statusEl.textContent = 'DOWN — No Link';
        statusEl.classList.add('status-down');
    }

    document.getElementById('input-description').value      = port.description || '';
    document.getElementById('input-vlan').value             = port.vlan || '1';
    document.getElementById('input-mode').value             = port.mode || 'access';
    document.getElementById('input-speed').value            = port.speed || 'auto';
    document.getElementById('input-duplex').value           = port.duplex || 'auto';
    document.getElementById('input-port-security').checked  = port.port_security || false;
    document.getElementById('input-max-mac').value          = port.max_mac || 1;

    toggleNativeVlan();
    toggleSecurityFields();

    document.getElementById('info-port-name').textContent      = port.name || '---';
    document.getElementById('info-current-vlan').textContent   = port.vlan || '---';
    document.getElementById('info-current-speed').textContent  = port.speed || '---';
    document.getElementById('info-current-duplex').textContent = port.duplex || '---';
    document.getElementById('info-port-type').textContent      = port.type || '---';

    if (port.mac_addresses && port.mac_addresses.length > 0) {
        document.getElementById('info-mac-addresses').textContent = port.mac_addresses.join(', ');
    } else {
        document.getElementById('info-mac-addresses').textContent = 'No devices connected';
    }
}

async function savePortConfig() {
    if (!currentPortName) return;

    const urlPortName = currentPortName.replace('/', '-');

    const configData = {
        description:   document.getElementById('input-description').value,
        vlan_id:       document.getElementById('input-vlan').value,
        mode:          document.getElementById('input-mode').value,
        speed:         document.getElementById('input-speed').value,
        duplex:        document.getElementById('input-duplex').value,
        port_security: document.getElementById('input-port-security').checked,
        max_mac:       parseInt(document.getElementById('input-max-mac').value) || 1,
        sticky_mac:    document.getElementById('input-sticky-mac').checked,
    };

    if (configData.mode === 'trunk') {
        configData.native_vlan = document.getElementById('input-native-vlan').value;
    }

    document.getElementById('modal-loading').style.display = 'block';

    try {
        const response = await fetch(`/api/port/${urlPortName}/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configData)
        });

        const data = await response.json();
        document.getElementById('modal-loading').style.display = 'none';

        if (data.success) {
            showStatusMessage('Port ' + currentPortName + ' saved successfully ✓', 'success');
            closeModal();
            loadAllPorts();
        } else {
            alert('Failed to save port configuration');
        }
    } catch (error) {
        document.getElementById('modal-loading').style.display = 'none';
        alert('Error: ' + error.message);
    }
}

async function enablePort() {
    await portAction('enable', 'enabled');
}

async function disablePort() {
    await portAction('disable', 'disabled');
}

async function reloadPort() {
    if (!confirm('Reload port ' + currentPortName + '? It will go down briefly.')) return;
    await portAction('reload', 'reloaded');
}

async function resetPort() {
    if (!confirm('Reset port ' + currentPortName + ' to factory defaults? All settings will be lost.')) return;
    await portAction('reset', 'reset to default');
}

async function portAction(action, successLabel) {
    if (!currentPortName) return;

    const urlPortName = currentPortName.replace('/', '-');
    document.getElementById('modal-loading').style.display = 'block';

    try {
        const response = await fetch(`/api/port/${urlPortName}/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        document.getElementById('modal-loading').style.display = 'none';

        if (data.success) {
            showStatusMessage('Port ' + currentPortName + ' ' + successLabel + ' ✓', 'success');
            closeModal();
            loadAllPorts();
        } else {
            alert('Operation failed');
        }
    } catch (error) {
        document.getElementById('modal-loading').style.display = 'none';
        alert('Error: ' + error.message);
    }
}

function closeModalOnOverlay(event) {
    if (event.target === document.getElementById('modal-overlay')) {
        closeModal();
    }
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
    currentPortName = null;
}

function toggleNativeVlan() {
    const mode = document.getElementById('input-mode').value;
    const nativeRow = document.getElementById('native-vlan-row');
    nativeRow.style.display = (mode === 'trunk') ? 'flex' : 'none';
}

function toggleSecurityFields() {
    const enabled = document.getElementById('input-port-security').checked;
    document.getElementById('security-fields').style.display = enabled ? 'block' : 'none';
}

function showStatusMessage(text, type) {
    const el = document.getElementById('status-message');
    el.textContent = text;
    el.className = type;
    el.style.display = 'block';

    if (type === 'success') {
        setTimeout(hideStatusMessage, 4000);
    }
}

function hideStatusMessage() {
    document.getElementById('status-message').style.display = 'none';
}
