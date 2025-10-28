import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js';
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut } from 'https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js';
import { getFirestore, collection, onSnapshot, query, orderBy, limit } from 'https://www.gstatic.com/firebasejs/10.13.1/firebase-firestore.js';

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

const markers = new Map();
let latestData = [];

function upsertMarker(doc) {
  const data = doc.data();
  const id = doc.id;
  const loc = data?.metadata?.location;
  if (!loc || typeof loc.lat !== 'number' || typeof loc.lng !== 'number') { return; }
  const latlng = [loc.lat, loc.lng];
  const label = `Detections: ${data?.detection?.numDetections ?? 0}<br>Confidence: ${(data?.detection?.boundingBoxes?.[0]?.confidence ?? 0).toFixed(2)}<br>Captured: ${data?.metadata?.capturedAt ?? 'n/a'}`;
  if (markers.has(id)) {
    markers.get(id).setLatLng(latlng).setPopupContent(label);
  } else {
    const m = L.marker(latlng).addTo(map).bindPopup(label);
    markers.set(id, m);
  }
}

function toCsv(rows) {
  const headers = ['id','createdAt','lat','lng','numDetections','modelVersion'];
  const lines = [headers.join(',')];
  rows.forEach(r => {
    const loc = r.metadata?.location || {};
    const line = [
      r.id,
      r.createdAt,
      loc.lat ?? '',
      loc.lng ?? '',
      r.detection?.numDetections ?? 0,
      r.detection?.modelVersion ?? ''
    ].join(',');
    lines.push(line);
  });
  return lines.join('\n');
}

exportBtn.addEventListener('click', () => {
  const csv = toCsv(latestData);
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'roadsense-detections.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});

// Firestore listener (public collection 'detections')
const detectionsRef = collection(db, 'detections');
const q = query(detectionsRef, orderBy('createdAt', 'desc'), limit(500));
onSnapshot(q, (snap) => {
  latestData = [];
  snap.forEach(doc => {
    upsertMarker(doc);
    latestData.push({ id: doc.id, ...doc.data() });
  });
  document.getElementById('stats').textContent = `Loaded ${snap.size} detections.`;
});
