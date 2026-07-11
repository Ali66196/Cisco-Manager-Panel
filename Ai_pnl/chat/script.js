const PANEL_URL = "http://localhost:5000";
const N8N_WEBHOOK_URL = "https://n8n.net11.ir/webhook/cisco-chat";

let conversationHistory = [];
let isProcessing = false;
let logMode = false;

document.addEventListener('DOMContentLoaded', () => {
  checkPanelConnection();

  const userInput = document.getElementById('user-input');
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  document.getElementById('send-btn').addEventListener('click', handleSend);

  document.getElementById('log-btn').addEventListener('click', () => {
    logMode = !logMode;
    const btn = document.getElementById('log-btn');
    btn.classList.toggle('active', logMode);
    btn.textContent = logMode ? 'Log ON' : 'Log';
    document.querySelectorAll('.system-message').forEach(el => {
      el.style.display = logMode ? '' : 'none';
    });
  });
});

async function checkPanelConnection() {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');

  try {
    const response = await fetch(`${PANEL_URL}/api/status`);
    const data = await response.json();

    if (data.connected) {
      dot.className = 'connected';
      text.textContent = 'Switch connected';
    } else {
      dot.className = 'disconnected';
      text.textContent = 'Switch not connected';
    }
  } catch (err) {
    dot.className = 'disconnected';
    text.textContent = 'Panel offline';
  }
}

async function handleSend() {
  if (isProcessing) return;

  const input = document.getElementById('user-input');
  const message = input.value.trim();

  if (!message) return;

  input.value = '';
  setProcessing(true);

  appendMessage(message, 'user');

  try {
    const switchState = await getSwitchState();
    const aiResponse = await sendToN8N(message, switchState);
    const parsed = parseAIResponse(aiResponse);

    appendMessage(parsed.reply, 'assistant');

    if (parsed.commands.length > 0) {
      await executeCommands(parsed.commands);
    }

    conversationHistory.push(
      { role: 'user', content: message },
      { role: 'assistant', content: parsed.reply }
    );

    checkPanelConnection();

  } catch (err) {
    appendMessage('Error: ' + err.message, 'error');
  } finally {
    setProcessing(false);
  }
}

async function getSwitchState() {
  try {
    const [portsRes, statusRes] = await Promise.all([
      fetch(`${PANEL_URL}/api/ports`),
      fetch(`${PANEL_URL}/api/status`)
    ]);

    const portsData = await portsRes.json();
    const statusData = await statusRes.json();

    return {
      connected: statusData.connected,
      ports: portsData.success ? portsData.ports : []
    };
  } catch (err) {
    return { connected: false, ports: [] };
  }
}

async function sendToN8N(message, switchState) {
  const MAX_WAIT_MS = 15 * 60 * 1000;
  const RETRY_DELAY_MS = 3000;
  const startTime = Date.now();

  while (true) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), MAX_WAIT_MS);

    try {
      const response = await fetch(N8N_WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Connection': 'keep-alive'
        },
        signal: controller.signal,
        keepalive: true,
        body: JSON.stringify({
          message: message,
          switch_state: switchState,
          history: conversationHistory
        })
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        return response.text();
      }

      if (response.status >= 500 && Date.now() - startTime < MAX_WAIT_MS - RETRY_DELAY_MS) {
        console.warn(`n8n returned ${response.status}, retrying in ${RETRY_DELAY_MS/1000}s...`);
        await new Promise(r => setTimeout(r, RETRY_DELAY_MS));
        continue;
      }

      throw new Error('n8n returned ' + response.status);

    } catch (err) {
      clearTimeout(timeoutId);

      if (err.name === 'AbortError') {
        throw new Error('Request timed out after 15 minutes');
      }

      if (err.message === 'Failed to fetch' && Date.now() - startTime < MAX_WAIT_MS - RETRY_DELAY_MS) {
        console.warn(`Connection dropped, retrying in ${RETRY_DELAY_MS/1000}s...`);
        await new Promise(r => setTimeout(r, RETRY_DELAY_MS));
        continue;
      }

      throw err;
    }
  }
}

function parseAIResponse(text) {
  const trimmed = text.trim();

  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      const raw = JSON.parse(trimmed);
      const obj = Array.isArray(raw) ? raw[0] : raw;

      const reply = obj.reply || obj.text || obj.message || JSON.stringify(obj);

      let commands = [];
      if (Array.isArray(obj.commands)) {
        commands = obj.commands
          .map(cmd => {
            if (typeof cmd === 'string') return cmd.trim();
            if (cmd.method && cmd.endpoint) {
              const body = cmd.body && Object.keys(cmd.body).length > 0
                ? ' ' + JSON.stringify(cmd.body)
                : '';
              return `${cmd.method.toUpperCase()} ${cmd.endpoint}${body}`;
            }
            return null;
          })
          .filter(Boolean);
      } else if (obj.commands && !Array.isArray(obj.commands)) {
        const cmd = obj.commands;
        if (cmd.method && cmd.endpoint) {
          const body = cmd.body && Object.keys(cmd.body).length > 0
            ? ' ' + JSON.stringify(cmd.body)
            : '';
          commands = [`${cmd.method.toUpperCase()} ${cmd.endpoint}${body}`];
        }
      }

      return { reply, commands };
    } catch (e) {
    }
  }

  const replyMatch = trimmed.match(/REPLY:\n([\s\S]*?)(?:\n\nCOMMANDS:|$)/);
  const commandsMatch = trimmed.match(/COMMANDS:\n([\s\S]*)/);

  if (!replyMatch) {
    return { reply: trimmed, commands: [] };
  }

  const reply = replyMatch[1].trim();
  const commands = commandsMatch
    ? commandsMatch[1]
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
    : [];

  return { reply, commands };
}

async function executeCommands(commands) {
  for (const line of commands) {
    try {
      const result = await executeOneCommand(line);

      if (result.method === 'GET') {
        const formatted = formatGetResult(result.endpoint, result.data);
        if (formatted) {
          appendMessage(formatted, 'system');
        }
      }
    } catch (err) {
      console.error('Error executing command:', line, err);
    }
  }
}

async function executeOneCommand(line) {
  const firstSpace = line.indexOf(' ');
  const secondSpace = line.indexOf(' ', firstSpace + 1);

  const method = line.substring(0, firstSpace).toUpperCase();
  const endpoint = secondSpace !== -1
    ? line.substring(firstSpace + 1, secondSpace)
    : line.substring(firstSpace + 1);
  const bodyStr = secondSpace !== -1
    ? line.substring(secondSpace + 1).trim()
    : null;

  const fetchOptions = {
    method: method,
    headers: { 'Content-Type': 'application/json' }
  };

  if (bodyStr && bodyStr !== '{}') {
    try {
      const parsed = JSON.parse(bodyStr);
      if (Object.keys(parsed).length > 0) {
        fetchOptions.body = bodyStr;
      }
    } catch (e) {
      fetchOptions.body = bodyStr;
    }
  }

  const response = await fetch(PANEL_URL + endpoint, fetchOptions);
  const data = await response.json();

  return { method, endpoint, data };
}

function formatGetResult(endpoint, data) {
  if (endpoint === '/api/ports' && data.success) {
    const lines = ['📊 Switch Port Status:\n'];

    for (const port of data.ports) {
      let statusEmoji;
      if (port.status === 'up') {
        statusEmoji = '🟢';
      } else if (port.status === 'disabled') {
        statusEmoji = '🟠';
      } else {
        statusEmoji = '🔴';
      }

      const modeTag = port.mode === 'trunk' ? '[T]' : '[A]';
      const line = `${statusEmoji} ${port.name} ${modeTag}  VLAN: ${port.vlan || '-'}  Speed: ${port.speed || '-'}  ${port.description || ''}`;
      lines.push(line);
    }

    return lines.join('\n');
  }

  if (/\/api\/port\/Fa0-\d+/.test(endpoint) && data.port) {
    const p = data.port;
    let result = `📋 Port ${p.name}:\n`;
    result += ` Status: ${p.status} | VLAN: ${p.vlan || '-'} | Mode: ${p.mode || '-'}\n`;
    result += ` Speed: ${p.speed || '-'} | Duplex: ${p.duplex || '-'}\n`;

    if (p.description) {
      result += ` Description: ${p.description}\n`;
    }

    if (p.mac_addresses && p.mac_addresses.length > 0) {
      result += ` MAC Addresses:\n`;
      for (const mac of p.mac_addresses) {
        result += `   • ${mac}\n`;
      }
    }

    return result.trim();
  }

  return null;
}

function markdownToHtml(text) {
  const lines = text.split('\n');
  const output = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim().startsWith('|')) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        tableLines.push(lines[i]);
        i++;
      }

      let tableHtml = '<table>';
      let isHeader = true;

      for (const tline of tableLines) {
        if (/^\s*\|[\s\-|:]+\|\s*$/.test(tline)) {
          isHeader = false;
          continue;
        }

        const cells = tline
          .split('|')
          .slice(1, -1)
          .map(cell => cell.trim());

        const tag = isHeader ? 'th' : 'td';
        const row = cells
          .map(cell => `<${tag}>${renderInline(cell)}</${tag}>`)
          .join('');

        tableHtml += isHeader
          ? `<thead><tr>${row}</tr></thead><tbody>`
          : `<tr>${row}</tr>`;
      }

      tableHtml += '</tbody></table>';
      output.push(tableHtml);
      continue;
    }

    output.push(`<span>${renderInline(line)}</span><br>`);
    i++;
  }

  return output.join('');
}

function renderInline(text) {
  text = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/`(.+?)`/g, '<code>$1</code>');
  return text;
}

function appendMessage(text, type) {
  const chatArea = document.getElementById('chat-area');

  const div = document.createElement('div');
  div.classList.add('message', `${type}-message`);

  if (type === 'assistant') {
    const label = document.createElement('strong');
    label.textContent = 'Cisco AI Assistant';
    div.appendChild(label);

    const content = document.createElement('div');
    content.classList.add('assistant-content');
    content.innerHTML = markdownToHtml(text);
    div.appendChild(content);
  } else {
    div.style.whiteSpace = 'pre-wrap';
    div.textContent = text;
  }

  chatArea.appendChild(div);

  if (type === 'system' && !logMode) {
    div.style.display = 'none';
  }

  chatArea.scrollTop = chatArea.scrollHeight;
}

function setProcessing(state) {
  isProcessing = state;

  const sendBtn = document.getElementById('send-btn');
  const userInput = document.getElementById('user-input');
  const thinkingIndicator = document.getElementById('thinking-indicator');

  sendBtn.disabled = state;
  userInput.disabled = state;
  thinkingIndicator.style.display = state ? 'flex' : 'none';

  if (!state) {
    userInput.focus();
  }
}
