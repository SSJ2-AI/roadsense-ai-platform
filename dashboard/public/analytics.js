import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js';
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut } from 'https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js';
import { getFirestore, collection, onSnapshot, query, orderBy, limit } from 'https://www.gstatic.com/firebasejs/10.13.1/firebase-firestore.js';

// Firebase config
const firebaseConfig = window.__FIREBASE_CONFIG__ || {
  apiKey: 'REPLACE_ME',
  authDomain: 'REPLACE_ME.firebaseapp.com',
  projectId: 'REPLACE_ME',
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// UI elements
const signInBtn = document.getElementById('sign-in');
const signOutBtn = document.getElementById('sign-out');
const userInfo = document.getElementById('user-info');

// Auth
const provider = new GoogleAuthProvider();
signInBtn.addEventListener('click', async () => {
  try { await signInWithPopup(auth, provider); } catch (e) { alert('Sign-in failed: ' + e); }
});
signOutBtn.addEventListener('click', async () => { await signOut(auth); });

onAuthStateChanged(auth, (user) => {
  if (user) {
    userInfo.textContent = user.email || user.uid;
    signInBtn.classList.add('hidden');
    signOutBtn.classList.remove('hidden');
  } else {
    userInfo.textContent = '';
    signInBtn.classList.remove('hidden');
    signOutBtn.classList.add('hidden');
  }
});

let allDetections = [];
let charts = {};

// Load data from Firestore
const detectionsRef = collection(db, 'detections');
const q = query(detectionsRef, orderBy('createdAt', 'desc'), limit(1000));

onSnapshot(q, (snap) => {
  allDetections = [];
  snap.forEach(doc => {
    allDetections.push({ id: doc.id, ...doc.data() });
  });
  
  calculateStatistics();
  renderCharts();
});

function calculateStatistics() {
  const now = new Date();
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  
  const recentDetections = allDetections.filter(d => {
    const createdAt = new Date(d.createdAt);
    return createdAt >= thirtyDaysAgo;
  });
  
  const totalCount = recentDetections.length;
  const repairedCount = recentDetections.filter(d => d.status === 'repaired').length;
  const pendingCount = totalCount - repairedCount;
  const repairRate = totalCount > 0 ? ((repairedCount / totalCount) * 100).toFixed(1) : 0;
  
  // Update KPI cards
  document.getElementById('kpi-total').textContent = totalCount.toLocaleString();
  document.getElementById('kpi-repaired').textContent = repairedCount.toLocaleString();
  document.getElementById('kpi-pending').textContent = pendingCount.toLocaleString();
  document.getElementById('kpi-rate').textContent = `${repairRate}%`;
  
  // Calculate cost savings
  const costSavingsPerPothole = 500; // Proactive vs reactive
  const costSavings = repairedCount * costSavingsPerPothole;
  document.getElementById('cost-savings').textContent = `$${costSavings.toLocaleString()}`;
  
  // Average repair time (placeholder - need repairedAt field)
  document.getElementById('avg-repair-time').textContent = 'N/A';
  
  // Top hotspot areas
  renderHotspotsTable(recentDetections);
}

function renderHotspotsTable(detections) {
  const areaCounts = {};
  const areaPriorities = {};
  
  detections.forEach(d => {
    const area = d.area || 'Unknown';
    areaCounts[area] = (areaCounts[area] || 0) + 1;
    if (!areaPriorities[area]) {
      areaPriorities[area] = { sum: 0, count: 0 };
    }
    areaPriorities[area].sum += d.priority_score || 0;
    areaPriorities[area].count++;
  });
  
  const sortedAreas = Object.entries(areaCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);
  
  const tbody = document.getElementById('hotspots-tbody');
  tbody.innerHTML = sortedAreas.map(([area, count], index) => {
    const avgPriority = areaPriorities[area] 
      ? (areaPriorities[area].sum / areaPriorities[area].count).toFixed(1)
      : 0;
    
    return `
      <tr>
        <td>${index + 1}</td>
        <td><strong>${area}</strong></td>
        <td>${count}</td>
        <td><span class="badge">${avgPriority}</span></td>
      </tr>
    `;
  }).join('');
}

function renderCharts() {
  renderStatusPieChart();
  renderTimelineChart();
  renderSeverityChart();
}

function renderStatusPieChart() {
  const canvas = document.getElementById('status-pie-chart');
  const ctx = canvas.getContext('2d');
  
  if (charts.statusPie) {
    charts.statusPie.destroy();
  }
  
  const repairedCount = allDetections.filter(d => d.status === 'repaired').length;
  const pendingCount = allDetections.length - repairedCount;
  
  charts.statusPie = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Pending', 'Repaired'],
      datasets: [{
        data: [pendingCount, repairedCount],
        backgroundColor: ['#f59e0b', '#10b981'],
        borderWidth: 2,
        borderColor: '#fff',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom',
        }
      }
    }
  });
}

function renderTimelineChart() {
  const canvas = document.getElementById('timeline-chart');
  const ctx = canvas.getContext('2d');
  
  if (charts.timeline) {
    charts.timeline.destroy();
  }
  
  // Group by date
  const dateMap = {};
  const now = new Date();
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  
  // Initialize all dates with 0
  for (let i = 0; i < 30; i++) {
    const date = new Date(thirtyDaysAgo.getTime() + i * 24 * 60 * 60 * 1000);
    const dateKey = date.toISOString().split('T')[0];
    dateMap[dateKey] = 0;
  }
  
  allDetections.forEach(d => {
    const createdAt = new Date(d.createdAt);
    if (createdAt >= thirtyDaysAgo) {
      const dateKey = createdAt.toISOString().split('T')[0];
      if (dateMap[dateKey] !== undefined) {
        dateMap[dateKey]++;
      }
    }
  });
  
  const labels = Object.keys(dateMap).sort();
  const data = labels.map(date => dateMap[date]);
  
  charts.timeline = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
      datasets: [{
        label: 'Detections',
        data: data,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.3,
        fill: true,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

function renderSeverityChart() {
  const canvas = document.getElementById('severity-chart');
  const ctx = canvas.getContext('2d');
  
  if (charts.severity) {
    charts.severity.destroy();
  }
  
  const severityCounts = {
    high: allDetections.filter(d => d.severity === 'high').length,
    medium: allDetections.filter(d => d.severity === 'medium').length,
    low: allDetections.filter(d => d.severity === 'low').length,
  };
  
  charts.severity = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['High', 'Medium', 'Low'],
      datasets: [{
        data: [severityCounts.high, severityCounts.medium, severityCounts.low],
        backgroundColor: ['#dc2626', '#f59e0b', '#10b981'],
        borderWidth: 2,
        borderColor: '#fff',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom',
        }
      }
    }
  });
}

// ROI Calculator
document.getElementById('calculate-roi').addEventListener('click', () => {
  const investment = parseFloat(document.getElementById('roi-investment').value) || 0;
  const reactiveCost = parseFloat(document.getElementById('roi-reactive-cost').value) || 800;
  const proactiveCost = parseFloat(document.getElementById('roi-proactive-cost').value) || 300;
  
  const repairedCount = allDetections.filter(d => d.status === 'repaired').length;
  
  // Calculate savings
  const savingsPerPothole = reactiveCost - proactiveCost;
  const totalSavings = repairedCount * savingsPerPothole;
  const netSavings = totalSavings - investment;
  const roiPercentage = investment > 0 ? ((netSavings / investment) * 100).toFixed(1) : 0;
  
  // Payback period (months)
  const savingsPerMonth = totalSavings / 12; // Assuming 1 year period
  const paybackMonths = investment > 0 && savingsPerMonth > 0 
    ? (investment / savingsPerMonth).toFixed(1) 
    : 'N/A';
  
  // Display results
  document.getElementById('roi-total-savings').textContent = `$${totalSavings.toLocaleString()}`;
  document.getElementById('roi-percentage').textContent = `${roiPercentage}%`;
  document.getElementById('roi-payback').textContent = paybackMonths === 'N/A' ? 'N/A' : `${paybackMonths} months`;
  document.getElementById('roi-results').classList.remove('hidden');
});

// Export functions
document.getElementById('export-full-report').addEventListener('click', () => {
  const headers = ['id', 'area', 'street_name', 'severity', 'priority_score', 'status', 'createdAt', 'lat', 'lng'];
  const lines = [headers.join(',')];
  
  allDetections.forEach(d => {
    const loc = d.metadata?.location || {};
    const line = [
      d.id,
      d.area || 'Unknown',
      d.street_name || 'Unknown',
      d.severity || 'low',
      d.priority_score || 0,
      d.status || 'reported',
      d.createdAt || '',
      loc.lat || '',
      loc.lng || ''
    ].map(v => `"${v}"`).join(',');
    lines.push(line);
  });
  
  const csv = lines.join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `roadsense-full-report-${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});

document.getElementById('export-summary').addEventListener('click', () => {
  alert('PDF export coming soon! For now, please use Print to PDF from your browser.');
  window.print();
});
