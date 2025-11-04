// Load potholes from Google Sheets
async function loadPotholes() {
  try {
    const response = await fetch(SHEET_URL);
    const text = await response.text();
    const json = JSON.parse(text.substr(47).slice(0, -2));
    const rows = json.table.rows;
    
    rows.forEach(row => {
      const cells = row.c;
      if (!cells || cells.length < 11) return;
      
      const pothole = {
        id: cells[0]?.v || '',
        photo: cells[1]?.v || '',
        location: cells[2]?.v || '',
        street: cells[3]?.v || '',
        intersection: cells[4]?.v || '',
        latitude: parseFloat(cells[5]?.v || 0),
        longitude: parseFloat(cells[6]?.v || 0),
        timestamp: cells[7]?.v || '',
        severity: cells[8]?.v || 'Low',
        status: cells[9]?.v || 'Reported',
        confidence: cells[10]?.v || '',
        count: cells[11]?.v || '',
        notes: cells[12]?.v || ''
      };
      
      if (pothole.latitude && pothole.longitude) {
        addPotholeToMap(pothole);
        addToPriorityQueue(pothole);
      }
    });
    
    updateStats();
    console.log('Potholes loaded successfully from Google Sheets');
  } catch (error) {
    console.error('Error loading potholes:', error);
  }
}

// Call on page load
document.addEventListener('DOMContentLoaded', loadPotholes);
