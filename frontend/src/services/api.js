import axios from 'axios';

const hostname = window.location.hostname;
const protocol = window.location.protocol;

const LLM_BASE = `${protocol}//${hostname}:7000`;
const MCP_BASE = `${protocol}//${hostname}:8000`;
const CAD_BASE = `${protocol}//${hostname}:5000`;

const getErrorMessage = (error, fallback) => {
  if (error.response?.data?.message) return error.response.data.message;
  if (error.response?.data?.detail) return error.response.data.detail;
  if (error.message) return error.message;
  return fallback;
};

export const checkLlmHealth = async () => {
  const response = await axios.get(`${LLM_BASE}/health`);
  return response.data;
};

export const checkMcpHealth = async () => {
  const response = await axios.get(`${MCP_BASE}/health`);
  return response.data;
};

export const checkCadHealth = async () => {
  const response = await axios.get(`${CAD_BASE}/health`);
  return response.data;
};

export const fetchTools = async () => {
  const response = await axios.get(`${MCP_BASE}/api/v1/tools`);
  return response.data;
};

export const generateCommand = async (input) => {
  try {
    const response = await axios.post(`${LLM_BASE}/generate-command`, { input });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to reach LLM service'));
  }
};

export const sendChatPrompt = async (prompt) => {
  try {
    const response = await axios.post(`${MCP_BASE}/api/v1/tools/chat`, { prompt });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to reach MCP chat endpoint'));
  }
};

const toNumber = (value, fallback = 0) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
};

const normalizeBoundingBox = (value) => {
  if (!Array.isArray(value) || value.length !== 6) return [0, 0, 0, 0, 0, 0];
  return value.map((x) => toNumber(x, 0));
};

const sizesFromBoundingBox = (bb) => ({
  size_x_mm: Math.abs(bb[3] - bb[0]) * 10,
  size_y_mm: Math.abs(bb[4] - bb[1]) * 10,
  size_z_mm: Math.abs(bb[5] - bb[2]) * 10,
});

const normalizeEntityRecord = (raw, index = 0) => {
  const bb = normalizeBoundingBox(raw?.bounding_box);
  const sizes = sizesFromBoundingBox(bb);
  const volume = toNumber(raw?.volume_m3, 0);
  const density = toNumber(raw?.density_kg_m3, 7850);
  const computedMass = volume * density;

  return {
    item: toNumber(raw?.item, index + 1),
    id: String(raw?.id ?? raw?.name ?? `entity_${index + 1}`),
    name: String(raw?.name ?? raw?.id ?? `Entity ${index + 1}`),
    part_type: String(raw?.part_type ?? 'Shape'),
    material: String(raw?.material ?? 'steel'),
    density_kg_m3: density,
    volume_m3: volume,
    surface_area_m2: toNumber(raw?.surface_area_m2, 0),
    mass_kg: toNumber(raw?.mass_kg, computedMass),
    size_x_mm: toNumber(raw?.size_x_mm, sizes.size_x_mm),
    size_y_mm: toNumber(raw?.size_y_mm, sizes.size_y_mm),
    size_z_mm: toNumber(raw?.size_z_mm, sizes.size_z_mm),
    num_teeth: raw?.num_teeth ?? null,
    module: raw?.module ?? null,
    pitch_diameter_mm: raw?.pitch_diameter_mm ?? null,
    qty: Math.max(1, toNumber(raw?.qty, 1)),
    bounding_box: bb,
  };
};

const extractFirstArray = (...candidates) => candidates.find(Array.isArray) || [];

const normalizeEntitiesPayload = (data) => {
  const rows = extractFirstArray(
    data,
    data?.entities,
    data?.items,
    data?.data,
    data?.data?.entities,
    data?.data?.items,
    data?.data?.rows,
    data?.result?.data,
    data?.result?.entities,
    data?.result?.items,
  );

  if (data?.error) throw new Error(String(data.error));

  return rows
    .filter((row) => row && typeof row === 'object')
    .map((row, index) => normalizeEntityRecord(row, index));
};

const normalizeBomPayload = (data) => {
  const rows = extractFirstArray(
    data,
    data?.bom,
    data?.BOM,
    data?.items,
    data?.entities,
    data?.data?.bom,
    data?.data?.items,
    data?.data?.entities,
    data?.data?.data?.bom,
    data?.data?.data?.items,
    data?.data?.data?.entities,
    data?.result?.data?.bom,
    data?.result?.data?.items,
    data?.result?.data?.data?.bom,
    data?.result?.data?.data?.items,
  )
    .filter((row) => row && typeof row === 'object')
    .map((row, index) => normalizeEntityRecord(row, index));

  const totalItemsRaw =
    data?.total_items ??
    data?.totalItems ??
    data?.data?.total_items ??
    data?.data?.totalItems;

  const totalItems = Number.isFinite(Number(totalItemsRaw)) ? Number(totalItemsRaw) : rows.length;

  return {
    bom: rows,
    total_items: totalItems,
  };
};

const buildBomFromEntitiesPayload = (data) => {
  const rows = normalizeEntitiesPayload(data).map((row, index) => ({
    ...row,
    item: index + 1,
    qty: Math.max(1, Number(row?.qty || 1)),
  }));

  return {
    bom: rows,
    total_items: rows.length,
  };
};

const requestFromCandidates = async (endpoints) => {
  let lastError;
  for (const endpoint of endpoints) {
    try {
      const response = await axios.get(endpoint);
      return response.data;
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
};

export const fetchBom = async () => {
  const endpoints = [
    `${CAD_BASE}/bom`,
    `${MCP_BASE}/api/v1/tools/bom`,
    `${MCP_BASE}/api/v1/tools/tools/get_bom`,
    `${MCP_BASE}/api/v1/tools/get_bom`,
  ];

  const entityFallbackEndpoints = [
    `${CAD_BASE}/list_entities`,
    `${MCP_BASE}/api/v1/tools/entities`,
    `${MCP_BASE}/api/v1/tools/tools/list_entities`,
    `${MCP_BASE}/api/v1/tools/list_entities`,
  ];

  try {
    const payload = await requestFromCandidates(endpoints);
    const normalized = normalizeBomPayload(payload);

    if (normalized.bom.length > 0) {
      return normalized;
    }

    const entitiesPayload = await requestFromCandidates(entityFallbackEndpoints);
    return buildBomFromEntitiesPayload(entitiesPayload);
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to fetch BOM from CAD engine'));
  }
};

export const deleteObject = async (objectId) => {
  try {
    const response = await axios.post(`${CAD_BASE}/delete_object`, { object_id: objectId });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to delete object'));
  }
};

export const importStepFile = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${CAD_BASE}/import_step`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to import STEP file'));
  }
};

export const updateShape = async (objectId, params) => {
  try {
    const response = await axios.post(`${CAD_BASE}/update_shape`, {
      object_id: objectId, ...params,
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to update shape'));
  }
};

export const fetchEntities = async () => {
  const endpoints = [
    `${CAD_BASE}/list_entities`,
    `${MCP_BASE}/api/v1/tools/entities`,
    `${MCP_BASE}/api/v1/tools/tools/list_entities`,
    `${MCP_BASE}/api/v1/tools/list_entities`,
  ];

  try {
    const payload = await requestFromCandidates(endpoints);
    return normalizeEntitiesPayload(payload);
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to fetch entities'));
  }
};

// Direct CAD engine transformations (don't go through AI)
export const rotateObject = async (objectId, axis, angle) => {
  try {
    const response = await axios.post(`${CAD_BASE}/rotate_object`, {
      object_id: objectId,
      axis: axis,
      angle: angle,
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to rotate object'));
  }
};

export const scaleObject = async (objectId, factor) => {
  try {
    const response = await axios.post(`${CAD_BASE}/scale_object`, {
      object_id: objectId,
      factor: factor,
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to scale object'));
  }
};

export const moveObject = async (objectId, x, y, z) => {
  try {
    const response = await axios.post(`${CAD_BASE}/move_object`, {
      object_id: objectId,
      x: x,
      y: y,
      z: z,
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to move object'));
  }
};
