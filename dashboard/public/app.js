const SHEET_URL = 'https://docs.google.com/spreadsheets/d/1O-i2X66NVLQq43l1ORNreTMOEKJoCQQzaTFL9wT7eLE/export?format=csv';

// Load potholes from Google Sheets
async function loadPotholes() {
  try {
    const response = await fetch(SHEET_URL);
    const text = await response.text();
    
    // Parse CSV data
    const lines = text.split('\n');
    const headers = lines[0].split(',');
    
    // Clear existing potholes
    potholes = [];
    
    // Parse each row
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue;
      
      const values = lines[i].split(',');
      if (values.length < 11) continue;
      
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
        potholes.push(pothole);
        addMarker(pothole);
      }
    }
    
    updateStats();
    console.log('Potholes loaded successfully from Google Sheets');
  } catch (error) {
    console.error('Error loading potholes:', error);
  }
}

// Call on page load
document.addEventListener('DOMContentLoaded', loadPotholes);
