const palette = ['#6750A4', '#FF8A65', '#F4B942', '#4E9FCE', '#8E7CC3', '#E76F51', '#6FA8A1', '#D98C8C', '#7F9C55', '#A78BBA'];
const data = window.dashboardData || { states: [], departments: [] };
const common = { responsive: true, maintainAspectRatio: false };

new Chart(document.getElementById('departmentChart'), {
  type: 'bar',
  data: {
    labels: data.departments.map(item => item.label),
    datasets: [{ data: data.departments.map(item => item.value), backgroundColor: '#6750A4', borderRadius: 5, borderSkipped: false, barThickness: 18 }]
  },
  options: { ...common, plugins: { legend: { display: false }, tooltip: { backgroundColor: '#172734', padding: 11, displayColors: false } }, scales: { x: { grid: { display: false }, ticks: { color: '#75808a', font: { size: 9 }, maxRotation: 35, minRotation: 35 } }, y: { beginAtZero: true, grid: { color: '#edf0ed' }, ticks: { color: '#75808a', font: { size: 9 } } } } }
});

new Chart(document.getElementById('statusChart'), {
  type: 'doughnut',
  data: { labels: data.states.map(item => item.label), datasets: [{ data: data.states.map(item => item.value), backgroundColor: palette, borderWidth: 3, borderColor: '#fff', hoverOffset: 5 }] },
  options: { ...common, cutout: '75%', plugins: { legend: { display: false }, tooltip: { backgroundColor: '#172734', padding: 10 } } }
});

const chatModal = document.getElementById('chat-modal');
const chatOpen = document.getElementById('chat-open');
const chatClose = document.getElementById('chat-close');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');

function setChatOpen(open) {
  chatModal.classList.toggle('is-open', open);
  chatModal.setAttribute('aria-hidden', String(!open));
  document.body.classList.toggle('chat-is-open', open);
  if (open) chatInput.focus();
  else chatOpen.focus();
}

chatOpen.addEventListener('click', () => setChatOpen(true));
chatClose.addEventListener('click', () => setChatOpen(false));
chatModal.addEventListener('click', event => {
  if (event.target === chatModal) setChatOpen(false);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && chatModal.classList.contains('is-open')) setChatOpen(false);
});

function addChatMessage(text, author, extraClass = '') {
  const message = document.createElement('div');
  message.className = `chat-message ${author} ${extraClass}`.trim();
  message.textContent = text;
  chatMessages.appendChild(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return message;
}

chatForm.addEventListener('submit', async event => {
  event.preventDefault();
  const pregunta = chatInput.value.trim();
  if (!pregunta) return;
  addChatMessage(pregunta, 'user');
  chatInput.value = '';
  chatInput.disabled = true;
  const esperando = addChatMessage('Estoy consultando los datos…', 'assistant', 'is-pending');
  const enviar = chatForm.querySelector('button');
  enviar.disabled = true;
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pregunta })
    });
    const result = await response.json();
    esperando.remove();
    addChatMessage(result.respuesta || 'No recibí una respuesta. Intenta de nuevo.', result.success ? 'assistant' : 'assistant is-error');
  } catch (error) {
    esperando.remove();
    addChatMessage('No pude conectar con el asistente. Revisa tu conexión e inténtalo otra vez.', 'assistant is-error');
  } finally {
    chatInput.disabled = false;
    enviar.disabled = false;
    chatInput.focus();
  }
});

chatInput.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});
