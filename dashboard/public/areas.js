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
const areaSelect = document.getElementById('area-select');
const compareAllBtn = document.getElementById('compare-all');

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

// Map
const map = L.map('area-map').setView([43.7315, -79.7624], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

let allDetections = [];
let areaStats = {};
let cityAverages = {};
let charts = {};
let selectedArea = null;

// Load data
const detectionsRef = collection(db, 'detections');
const q = query(detectionsRef, orderBy('createdAt', 'desc'), limit(1000));

onSnapshot(q, (snap) => {
  allDetections = [];
  snap.forEach(doc => {
    allDetections.push({ id: doc.id, ...doc.data() });
  });
  
  calculateAreaStats();
  populateAreaSelect();
});

function calculateAreaStats() {
  areaStats = {};
  
  allDetections.forEach(d => {
    const area = d.area || 'Unknown';
    
    if (!areaStats[area]) {
      areaStats[area] = {
        total: 0,
        high: 0,
        medium: 0,
        low: 0,
        repaired: 0,
        pending: 0,
        prioritySum: 0,
        streets: new Set(),
        detections: [],
      };
    }
    
    const stats = areaStats[area];
    stats.total++;
    stats.detections.push(d);
    
    const severity = d.severity || 'low';
    stats[severity]++;
    
    if (d.status === 'repaired') {
      stats.repaired++;
    } else {
      stats.pending++;
    }
    
    stats.prioritySum += d.priority_score || 0;
    
    if (d.street_name && d.street_name !== 'Unknown') {
      stats.streets.add(d.street_name);
    }
  });
  
  // Calculate city averages
  const totalPotholes = allDetections.length;
  const totalAreas = Object.keys(areaStats).length;
  const totalRepaired = allDetections.filter(d => d.status === 'repaired').length;
  
  cityAverages = {
    avgPotholesPerArea: totalAreas > 0 ? totalPotholes / totalAreas : 0,
    cityRepairRate: totalPotholes > 0 ? (totalRepaired / totalPotholes) * 100 : 0,
    avgPriority: allDetections.reduce((sum, d) => sum + (d.priority_score || 0), 0) / (totalPotholes || 1),
  };
}

function populateAreaSelect() {
  const areas = Object.keys(areaStats).sort();
  areaSelect.innerHTML = '<option value="">-- Select Area --</option>' +
    areas.map(area => `<option value="${area}">${area} (${areaStats[area].total})</option>`).join('');
}

areaSelect.addEventListener('change', (e) => {
  selectedArea = e.target.value;
  if (selectedArea) {
    renderAreaDetails(selectedArea);
    document.getElementById('city-comparison-section').classList.add('hidden');
  }
});

compareAllBtn.addEventListener('click', () => {
  renderCityComparison();
  document.getElementById('city-comparison-section').classList.remove('hidden');
});

function renderAreaDetails(area) {
  const stats = areaStats[area];
  if (!stats) return;
  
  // Area info
  document.getElementById('area-info').innerHTML = `
    <p><strong>Area Name:</strong> ${area}</p>
    <p><strong>Total Streets:</strong> ${stats.streets.size}</p>
    <p><strong>Detection Density:</strong> ${stats.total} potholes</p>
  `;
  
  // Key metrics
  document.getElementById('area-total').textContent = stats.total;
  document.getElementById('area-high').textContent = stats.high;
  const avgPriority = stats.total > 0 ? (stats.prioritySum / stats.total).toFixed(1) : 0;
  document.getElementById('area-priority').textContent = avgPriority;
  const repairRate = stats.total > 0 ? ((stats.repaired / stats.total) * 100).toFixed(1) : 0;
  document.getElementById('area-repair-rate').textContent = `${repairRate}%`;
  
  // Repair completion
  document.getElementById('area-repaired').textContent = stats.repaired;
  document.getElementById('area-pending').textContent = stats.pending;
  document.getElementById('completion-percentage').textContent = `${repairRate}%`;
  document.getElementById('progress-fill').style.width = `${repairRate}%`;
  
  // Streets list
  const streetsArray = Array.from(stats.streets).sort();
  document.getElementById('streets-list').innerHTML = streetsArray.length > 0
    ? `<ul>${streetsArray.map(s => `<li>${s}</li>`).join('')}</ul>`
    : '<p class="no-data">No street data available</p>';
  
  // Update map
  updateAreaMap(stats.detections);
  
  // Render charts
  renderComparisonChart(area, stats);
  renderSeverityBreakdownChart(stats);
  renderStatusBreakdownChart(stats);
}

function updateAreaMap(detections) {
  // Clear existing markers
  map.eachLayer(layer => {
    if (layer instanceof L.Marker) {
      map.removeLayer(layer);
    }
  });
  
  const markers = [];
  
  detections.forEach(d => {
    const loc = d.metadata?.location;
    if (loc && loc.lat && loc.lng) {
      const severity = d.severity || 'low';
      const color = severity === 'high' ? '#dc2626' : severity === 'medium' ? '#f59e0b' : '#10b981';
      
      const marker = L.marker([loc.lat, loc.lng], {
        icon: L.divIcon({
          className: 'custom-marker',
          html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>`,
          iconSize: [20, 20],
        })
      }).bindPopup(`
        <strong>${d.street_name || 'Unknown'}</strong><br>
        Severity: ${severity}<br>
        Priority: ${d.priority_score || 0}
      `).addTo(map);
      
      markers.push(marker);
    }
  });
  
  // Fit bounds to markers
  if (markers.length > 0) {
    const group = L.featureGroup(markers);
    map.fitBounds(group.getBounds(), { padding: [50, 50] });
  }
}

function renderComparisonChart(area, stats) {
  const canvas = document.getElementById('comparison-chart');
  const ctx = canvas.getContext('2d');
  
  if (charts.comparison) {
    charts.comparison.destroy();
  }
  
  const areaAvgPriority = stats.total > 0 ? stats.prioritySum / stats.total : 0;
  const areaRepairRate = stats.total > 0 ? (stats.repaired / stats.total) * 100 : 0;
  
  charts.comparison = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Potholes per Area', 'Repair Rate (%)', 'Avg Priority'],
      datasets: [
        {
          label: area,
          data: [stats.total, areaRepairRate, areaAvgPriority],
          backgroundColor: '#3b82f6',
        },
        {
          label: 'City Average',
          data: [cityAverages.avgPotholesPerArea, cityAverages.cityRepairRate, cityAverages.avgPriority],
          backgroundColor: '#94a3b8',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: 'bottom' }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

function renderSeverityBreakdownChart(stats) {
  const canvas = document.getElementById('severity-breakdown-chart');
  const ctx = canvas.getContext('2d');
  
  if (charts.severity) {
    charts.severity.destroy();
  }
  
  charts.severity = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['High', 'Medium', 'Low'],
      datasets: [{
        data: [stats.high, stats.medium, stats.low],
        backgroundColor: ['#dc2626', '#f59e0b', '#10b981'],
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}

function renderStatusBreakdownChart(stats) {
  const canvas = document.getElementById('status-breakdown-chart');
  const ctx = canvas.getContext('2d');
  
  if (charts.status) {
    charts.status.destroy();
  }
  
  charts.status = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Pending', 'Repaired'],
      datasets: [{
        data: [stats.pending, stats.repaired],
        backgroundColor: ['#f59e0b', '#10b981'],
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}

function renderCityComparison() {
  const tbody = document.getElementById('city-comparison-tbody');
  
  const sortedAreas = Object.entries(areaStats)
    .sort((a, b) => b[1].total - a[1].total);
  
  tbody.innerHTML = sortedAreas.map(([area, stats]) => {
    const avgPriority = stats.total > 0 ? (stats.prioritySum / stats.total).toFixed(1) : 0;
    const repairRate = stats.total > 0 ? ((stats.repaired / stats.total) * 100).toFixed(1) : 0;
    
    return `
      <tr>
        <td><strong>${area}</strong></td>
        <td>${stats.total}</td>
        <td><span class="badge badge-high">${stats.high}</span></td>
        <td><span class="badge badge-medium">${stats.medium}</span></td>
        <td><span class="badge badge-low">${stats.low}</span></td>
        <td>${avgPriority}</td>
        <td>${repairRate}%</td>
      </tr>
    `;
  }).join('');
}
