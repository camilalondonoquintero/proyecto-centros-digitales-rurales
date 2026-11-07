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
