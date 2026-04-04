/**
 * cadApi.js
 * Handles backend API calls for CAD operations.
 */

const BASE_URL = "http://localhost:5000";

// Geometry

export async function createHexagon() {
  const res = await fetch(`${BASE_URL}/createHexagon`, { method: "POST" });
  return await res.json();
}

export async function createCircle() {
  const res = await fetch(`${BASE_URL}/createCircle`, { method: "POST" });
  return await res.json();
}

export async function createRectangle() {
  const res = await fetch(`${BASE_URL}/createRectangle`, { method: "POST" });
  return await res.json();
}

// Operations

export async function extrude() {
  const res = await fetch(`${BASE_URL}/extrude`, { method: "POST" });
  return await res.json();
}

export async function extrudeAdd() {
  const res = await fetch(`${BASE_URL}/extrudeAdd`, { method: "POST" });
  return await res.json();
}

export async function extrudeRemove() {
  const res = await fetch(`${BASE_URL}/extrudeRemove`, { method: "POST" });
  return await res.json();
}

// Export

export async function exportSTEP() {
  const res = await fetch(`${BASE_URL}/exportSTEP`, { method: "POST" });
  return await res.json();
}

export async function getScene() {
  const res = await fetch(`${BASE_URL}/scene`);
  return await res.json();
}

// AI

export async function sendMessage(prompt) {
  const res = await fetch(`${BASE_URL}/api/ai`, { 
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: prompt })
  });
  return await res.json();
}
