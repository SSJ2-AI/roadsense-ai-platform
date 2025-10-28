import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js';
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut } from 'https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js';
import { getFirestore, collection, onSnapshot, query, orderBy, limit, where } from 'https://www.gstatic.com/firebasejs/10.13.1/firebase-firestore.js';

// Replace at deploy: window.__FIREBASE_CONFIG__ should be injected by deploy script
const firebaseConfig = window.__FIREBASE_CONFIG__ || {
  apiKey: 'REPLACE_ME',
  authDomain: 'REPLACE_ME.firebaseapp.com',
  projectId: 'REPLACE_ME',
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// UI elements
const signInBtn = document.getElementById('sign-in');
const signOutBtn = document.getElementById('sign-out');
const userInfo = document.getElementById('user-info');
const exportBtn = document.getElementById('export-csv');
const applyFiltersBtn = document.getElementById('apply-filters');
const resetFiltersBtn = document.getElementById('reset-filters');
const toggleHeatmapBtn = document.getElementById('toggle-heatmap');
const zoomAllBtn = document.getElementById('zoom-all');

// Filters
const statusFilter = document.getElementById('status-filter');
const severityFilter = document.getElementById('severity-filter');
const areaFilter = document.getElementById('area-filter');
const dateFromFilter = document.getElementById('date-from');
const dateToFilter = document.getElementById('date-to');

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

// Leaflet map
const map = L.map('map').setView([43.7315, -79.7624], 12); // Brampton
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Marker clustering
const markerCluster = L.markerClusterGroup({
  maxClusterRadius: 80,
  spiderfyOnMaxZoom: true,
  showCoverageOnHover: false,
});
map.addLayer(markerCluster);

// Heatmap layer
let heatmapLayer = null;
let heatmapEnabled = false;

const markers = new Map();
let allDetections = [];
let filteredDetections = [];
let areaSet = new Set();

// Severity colors
const severityColors = {
  high: '#dc2626',
  medium: '#f59e0b',
  low: '#10b981',
};

function createMarkerIcon(severity) {
  const color = severityColors[severity] || '#6b7280';
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background-color: ${color}; width: 24px; height: 24px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function formatDate(dateStr) {
  if (!dateStr) return 'n/a';
  const date = new Date(dateStr);
  if (isNaN(date)) return 'n/a';
  const now = new Date();
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return '1 day ago';
  return `${diffDays} days ago`;
}

function upsertMarker(detection) {
  const loc = detection?.metadata?.location;
  if (!loc || typeof loc.lat !== 'number' || typeof loc.lng !== 'number') return;
  
  const latlng = [loc.lat, loc.lng];
  const severity = detection.severity || 'low';
  const priorityScore = detection.priority_score || 0;
  const area = detection.area || 'Unknown';
  const streetName = detection.street_name || 'Unknown street';
  const status = detection.status || 'reported';
  const numDetections = detection.detection?.numDetections || 0;
  
  // Add area to filter dropdown
  if (area && area !== 'Unknown') {
    areaSet.add(area);
  }
  
  const label = `
    <strong>${streetName}</strong><br>
    Area: ${area}<br>
    Severity: <span style="color: ${severityColors[severity]}">${severity.toUpperCase()}</span><br>
    Priority Score: <strong>${priorityScore}</strong><br>
    Potholes: ${numDetections}<br>
    Status: ${status}<br>
    Detected: ${formatDate(detection.createdAt)}
  `;
  
  const icon = createMarkerIcon(severity);
  
  if (markers.has(detection.id)) {
    const marker = markers.get(detection.id);
    marker.setLatLng(latlng).setPopupContent(label).setIcon(icon);
  } else {
    const marker = L.marker(latlng, { icon }).bindPopup(label);
    markers.set(detection.id, marker);
    markerCluster.addLayer(marker);
  }
}

function updateHeatmap() {
  if (heatmapLayer) {
    map.removeLayer(heatmapLayer);
    heatmapLayer = null;
  }
  
  if (heatmapEnabled && filteredDetections.length > 0) {
    const heatData = filteredDetections
      .filter(d => d.metadata?.location?.lat && d.metadata?.location?.lng)
      .map(d => [d.metadata.location.lat, d.metadata.location.lng, 0.5]);
    
    heatmapLayer = L.heatLayer(heatData, {
      radius: 25,
      blur: 15,
      maxZoom: 17,
    }).addTo(map);
  }
}

function applyFilters() {
  const status = statusFilter.value;
  const severity = severityFilter.value;
  const area = areaFilter.value;
  const dateFrom = dateFromFilter.value ? new Date(dateFromFilter.value) : null;
  const dateTo = dateToFilter.value ? new Date(dateToFilter.value) : null;
  
  filteredDetections = allDetections.filter(detection => {
    if (status && detection.status !== status) return false;
    if (severity && detection.severity !== severity) return false;
    if (area && detection.area !== area) return false;
    
    if (dateFrom || dateTo) {
      const createdAt = new Date(detection.createdAt);
      if (dateFrom && createdAt < dateFrom) return false;
      if (dateTo && createdAt > dateTo) return false;
    }
    
    return true;
  });
  
  // Update map markers
  markerCluster.clearLayers();
  filteredDetections.forEach(detection => {
    const marker = markers.get(detection.id);
    if (marker) {
      markerCluster.addLayer(marker);
    }
  });
  
  updateHeatmap();
  renderPriorityQueue();
  renderAreaStats();
}

function resetFilters() {
  statusFilter.value = '';
  severityFilter.value = '';
  areaFilter.value = '';
  dateFromFilter.value = '';
  dateToFilter.value = '';
  applyFilters();
}

function renderPriorityQueue() {
  const tbody = document.getElementById('queue-tbody');
  const queueCount = document.getElementById('queue-count');
  
  if (filteredDetections.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="no-data">No detections match the current filters.</td></tr>';
    queueCount.textContent = '0';
    return;
  }
  
  // Sort by priority score descending
  const sorted = [...filteredDetections].sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0));
  
  queueCount.textContent = sorted.length;
  
  tbody.innerHTML = sorted.map(detection => {
    const severity = detection.severity || 'low';
    const severityBadge = `<span class="badge badge-${severity}">${severity}</span>`;
    const statusBadge = `<span class="badge badge-status">${detection.status || 'reported'}</span>`;
    const urgencyBadge = `<span class="badge">${detection.repair_urgency || 'routine'}</span>`;
    const loc = detection.metadata?.location;
    const mapsUrl = loc ? `https://www.google.com/maps?q=${loc.lat},${loc.lng}` : '#';
    
    return `
      <tr>
        <td><strong>${detection.priority_score || 0}</strong></td>
        <td>${severityBadge}</td>
        <td>${detection.area || 'Unknown'}</td>
        <td>${detection.street_name || 'Unknown'}</td>
        <td>${detection.detection?.numDetections || 0}</td>
        <td>${formatDate(detection.createdAt)}</td>
        <td>${statusBadge}</td>
        <td>${urgencyBadge}</td>
        <td>
          <div class="action-buttons">
            <a href="${mapsUrl}" target="_blank" class="btn-small">Navigate</a>
            <button class="btn-small" onclick="markAsRepaired('${detection.id}')">Mark Repaired</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderAreaStats() {
  const areaStats = {};
  
  filteredDetections.forEach(detection => {
    const area = detection.area || 'Unknown';
    if (!areaStats[area]) {
      areaStats[area] = { count: 0, high: 0, medium: 0, low: 0 };
    }
    areaStats[area].count++;
    const severity = detection.severity || 'low';
    areaStats[area][severity]++;
  });
  
  const sorted = Object.entries(areaStats).sort((a, b) => b[1].count - a[1].count);
  
  // Render table
  const tableDiv = document.getElementById('area-stats-table');
  tableDiv.innerHTML = `
    <table class="stats-table">
      <thead>
        <tr>
          <th>Area</th>
          <th>Total</th>
          <th>High</th>
          <th>Medium</th>
          <th>Low</th>
        </tr>
      </thead>
      <tbody>
        ${sorted.slice(0, 10).map(([area, stats]) => `
          <tr>
            <td>${area}</td>
            <td><strong>${stats.count}</strong></td>
            <td><span class="badge badge-high">${stats.high}</span></td>
            <td><span class="badge badge-medium">${stats.medium}</span></td>
            <td><span class="badge badge-low">${stats.low}</span></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  
  // Render chart
  renderAreaChart(sorted.slice(0, 10));
}

let areaChartInstance = null;

function renderAreaChart(data) {
  const canvas = document.getElementById('area-chart');
  const ctx = canvas.getContext('2d');
  
  if (areaChartInstance) {
    areaChartInstance.destroy();
  }
  
  areaChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(([area]) => area),
      datasets: [{
        label: 'Potholes',
        data: data.map(([, stats]) => stats.count),
        backgroundColor: '#3b82f6',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

function populateAreaFilter() {
  const areas = Array.from(areaSet).sort();
  areaFilter.innerHTML = '<option value="">All Areas</option>' + 
    areas.map(area => `<option value="${area}">${area}</option>`).join('');
}

function toCsv(rows) {
  const headers = ['id', 'priority_score', 'severity', 'area', 'street_name', 'status', 'lat', 'lng', 'numDetections', 'createdAt'];
  const lines = [headers.join(',')];
  rows.forEach(r => {
    const loc = r.metadata?.location || {};
    const line = [
      r.id,
      r.priority_score || 0,
      r.severity || 'low',
      r.area || 'Unknown',
      r.street_name || 'Unknown',
      r.status || 'reported',
      loc.lat || '',
      loc.lng || '',
      r.detection?.numDetections || 0,
      r.createdAt || ''
    ].map(v => `"${v}"`).join(',');
    lines.push(line);
  });
  return lines.join('\n');
}

exportBtn.addEventListener('click', () => {
  const csv = toCsv(filteredDetections);
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `roadsense-priority-queue-${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});

applyFiltersBtn.addEventListener('click', applyFilters);
resetFiltersBtn.addEventListener('click', resetFilters);

toggleHeatmapBtn.addEventListener('click', () => {
  heatmapEnabled = !heatmapEnabled;
  toggleHeatmapBtn.textContent = heatmapEnabled ? 'Hide Heatmap' : 'Show Heatmap';
  updateHeatmap();
});

zoomAllBtn.addEventListener('click', () => {
  if (markerCluster.getLayers().length > 0) {
    map.fitBounds(markerCluster.getBounds(), { padding: [50, 50] });
  }
});

// Backend API configuration
const API_BASE_URL = window.__API_BASE_URL__ || 'https://your-backend.run.app';
const API_KEY = window.__API_KEY__ || '';

// Mark as repaired function (global for inline onclick)
window.markAsRepaired = async function(detectionId) {
  if (!confirm('Mark this pothole as repaired?')) return;
  
  try {
    // Show loading state
    const button = event?.target;
    if (button) {
      button.disabled = true;
      button.textContent = 'Updating...';
    }
    
    // Call backend API to update status
    const response = await fetch(`${API_BASE_URL}/v1/detections/${detectionId}/update-status?status=repaired`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    // Success feedback
    alert(`Successfully marked pothole ${detectionId} as repaired!`);
    
    // Refresh the display (data will update via Firestore listener)
    console.log('Status updated:', result);
    
  } catch (error) {
    console.error('Error marking pothole as repaired:', error);
    alert(`Failed to update status: ${error.message}\n\nPlease ensure:\n1. Backend API is running\n2. API key is configured\n3. You have permission to update detections`);
  } finally {
    // Reset button state
    const button = event?.target;
    if (button) {
      button.disabled = false;
      button.textContent = 'Mark Repaired';
    }
  }
};

// Firestore listener (public collection 'detections')
const detectionsRef = collection(db, 'detections');
const q = query(detectionsRef, orderBy('createdAt', 'desc'), limit(1000));
onSnapshot(q, (snap) => {
  allDetections = [];
  snap.forEach(doc => {
    const detection = { id: doc.id, ...doc.data() };
    allDetections.push(detection);
    upsertMarker(detection);
  });
  
  populateAreaFilter();
  applyFilters(); // Apply current filters to new data
});

// Mobile detection and responsive view
function checkMobileView() {
  const isMobile = window.innerWidth < 768;
  const mobileView = document.getElementById('mobile-view');
  if (isMobile) {
    mobileView.style.display = 'block';
    renderMobileWorkerView();
  } else {
    mobileView.style.display = 'none';
  }
}

function renderMobileWorkerView() {
  const assignedList = document.getElementById('assigned-list');
  const myPotholes = filteredDetections.filter(d => d.status === 'scheduled').slice(0, 10);
  
  if (myPotholes.length === 0) {
    assignedList.innerHTML = '<p class="no-data">No potholes assigned to you.</p>';
    return;
  }
  
  assignedList.innerHTML = myPotholes.map(detection => {
    const loc = detection.metadata?.location;
    const mapsUrl = loc ? `https://www.google.com/maps?q=${loc.lat},${loc.lng}` : '#';
    
    return `
      <div class="mobile-card">
        <div class="mobile-card-header">
          <strong>${detection.street_name || 'Unknown'}</strong>
          <span class="badge badge-${detection.severity}">${detection.severity}</span>
        </div>
        <div class="mobile-card-body">
          <p>Area: ${detection.area || 'Unknown'}</p>
          <p>Priority: ${detection.priority_score || 0}</p>
          <p>Detected: ${formatDate(detection.createdAt)}</p>
        </div>
        <div class="mobile-card-actions">
          <a href="${mapsUrl}" target="_blank" class="btn-primary">Navigate</a>
          <button class="btn-secondary" onclick="markAsRepaired('${detection.id}')">Mark Repaired</button>
        </div>
      </div>
    `;
  }).join('');
}

window.addEventListener('resize', checkMobileView);
checkMobileView();
