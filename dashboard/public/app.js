// Google Sheet CSV endpoint (published to web)
const SHEET_URL = 'https://docs.google.com/spreadsheets/d/1O-i2X66NVLQq43l1ORNreTMOEKJoCQQzaTFL9wT7eLE/export?format=csv&gid=0';

let allPotholes = [];

async function loadPotholes() {
  try {
    console.log('Fetching potholes from Google Sheets...');
    const response = await fetch(SHEET_URL);
    const csvText = await response.text();
    console.log('CSV fetched successfully');
    
    // Parse CSV manually
    const lines = csvText.split('\n');
    const headers = lines[0].split(',');
    
    allPotholes = [];
    
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue;
      
      const values = lines[i].split(',');
      if (values.length < 7) continue;
      
      const pothole = {
        id: values[0] || '',
        photo: values[1] || '',
        location: values[2] || '',
        street: values[3] || '',
        intersection: values[4] || '',
        latitude: parseFloat(values[5]) || 0,
        longitude: parseFloat(values[6]) || 0,
        timestamp: values[7] || '',
        severity: values[8] || 'Low',
        status: values[9] || 'Reported',
        confidence: values[10] || '',
        count: values[11] || '',
        notes: values[12] || ''
      };
      
      if (pothole.latitude && pothole.longitude) {
        allPotholes.push(pothole);
      }
    }
    
    console.log(`Loaded ${allPotholes.length} potholes`);
    renderDashboard();
    
  } catch (error) {
    console.error('Error loading potholes:', error);
    document.getElementById('priority-queue').innerHTML = '<p>Error loading data. Please refresh.</p>';
  }
}

function renderDashboard() {
  // Update stats
  document.getElementById('total-potholes').textContent = allPotholes.length;
  
  // Render priority queue
  const queueContainer = document.getElementById('priority-queue');
  queueContainer.innerHTML = '';
  
  allPotholes.forEach(pothole => {
    const row = document.createElement('div');
    row.className = 'pothole-row';
    row.innerHTML = `
      <strong>${pothole.id}</strong> - ${pothole.street} (${pothole.intersection})<br>
      Severity: ${pothole.severity} | Status: ${pothole.status}<br>
      Location: ${pothole.latitude}, ${pothole.longitude}
    `;
    queueContainer.appendChild(row);
    
    // Add to map if map exists
    if (typeof L !== 'undefined' && window.map) {
      L.marker([pothole.latitude, pothole.longitude])
        .addTo(window.map)
        .bindPopup(`<b>${pothole.id}</b><br>${pothole.street}<br>Severity: ${pothole.severity}`);
    }
  });
}

// Load on page ready
document.addEventListener('DOMContentLoaded', loadPotholes);
