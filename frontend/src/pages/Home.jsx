import React, { useEffect, useState, useRef, useCallback } from 'react';
import Viewer from '../components/Viewer';
import BomPanel from '../components/BomPanel';
import {
  checkCadHealth, checkLlmHealth, checkMcpHealth, sendChatPrompt,
  deleteObject, importStepFile, updateShape, fetchEntities,
  rotateObject, scaleObject, moveObject,
} from '../services/api';

const C = {
  bg: '#1c1c1e', sidebar: '#252528', toolbar: '#2a2a2d', panel: '#2a2a2d',
  border: '#3a3a3d', accent: '#00c5b8', text: '#d4d4d8', muted: '#71717a',
  hover: '#303033', active: '#3a3a3f', treeHover: '#323236', treeActive: '#3d3d44',
  danger: '#ef4444',
};

// ─── SMALL REUSABLE COMPONENTS ────────────────────────────────────────────────
function ToolBtn({ icon, label, onClick, active, danger, disabled, tooltip }) {
  const [h, setH] = useState(false);
  const isClickable = !disabled && onClick;
  return (
    <div 
      title={tooltip || label} 
      onClick={isClickable ? onClick : undefined}
      onMouseEnter={() => setH(true)} 
      onMouseLeave={() => setH(false)}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        padding: '6px 10px', gap: 2, cursor: isClickable ? 'pointer' : 'not-allowed', borderRadius: 4, minWidth: 48,
        background: active ? C.active : (h && isClickable) ? C.hover : 'transparent',
        border: danger && h && isClickable ? `1px solid ${C.danger}` : '1px solid transparent',
        transition: 'all 0.15s',
        opacity: disabled ? 0.4 : 1,
      }}>
      <span style={{ fontSize: 18 }}>{icon}</span>
      <span style={{ fontSize: 9, color: danger && h ? C.danger : C.muted, fontWeight: 600, letterSpacing: 0.3 }}>{label}</span>
    </div>
  );
}

function TreeNode({ label, icon = '📄', depth = 0, children, defaultOpen = false, active, onSelect }) {
  const [open, setOpen] = useState(defaultOpen);
  const [h, setH] = useState(false);
  const hasChildren = React.Children.count(children) > 0;
  return (
    <div>
      <div onMouseEnter={() => setH(true)} onMouseLeave={() => setH(false)}
        onClick={() => { hasChildren && setOpen(!open); onSelect && onSelect(); }}
        style={{
          display: 'flex', alignItems: 'center', gap: 4,
          padding: `3px 8px 3px ${12 + depth * 14}px`,
          fontSize: 11.5, color: active ? '#fff' : C.text,
          background: active ? C.treeActive : h ? C.treeHover : 'transparent',
          cursor: 'pointer', transition: 'background 0.1s',
          borderLeft: active ? `2px solid ${C.accent}` : '2px solid transparent',
        }}>
        {hasChildren ? <span style={{ fontSize: 9, color: C.muted, minWidth: 10 }}>{open ? '▾' : '▸'}</span> : <span style={{ minWidth: 10 }} />}
        <span style={{ fontSize: 13 }}>{icon}</span>
        <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{label}</span>
      </div>
      {open && children && <div>{children}</div>}
    </div>
  );
}

function PropRow({ label, value, valueColor, unit, editable, onEdit }) {
  const [hover, setHover] = useState(false);
  return (
    <div 
      style={{ 
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
        padding: '5px 0', borderBottom: `1px solid ${C.border}`,
        cursor: editable ? 'pointer' : 'default',
        background: hover && editable ? 'rgba(0,197,184,0.05)' : 'transparent',
        transition: 'background 0.1s',
      }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onClick={editable ? onEdit : undefined}
    >
      <span style={{ fontSize: 11, color: C.muted, display: 'flex', alignItems: 'center', gap: 4 }}>
        {label}
        {editable && <span style={{ fontSize: 9, color: C.accent, opacity: hover ? 1 : 0.5 }}>✎</span>}
      </span>
      <span style={{ fontSize: 11, color: valueColor || C.text, fontWeight: 600 }}>
        {value}{unit && <span style={{ color: C.muted, fontWeight: 400, marginLeft: 2 }}>{unit}</span>}
      </span>
    </div>
  );
}

function SectionHdr({ label, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ marginBottom: 6 }}>
      <div onClick={() => setOpen(!open)}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '5px 12px', background: C.active, cursor: 'pointer',
          fontSize: 10, fontWeight: 700, color: C.muted,
          textTransform: 'uppercase', letterSpacing: 1, borderRadius: 3,
        }}>
        <span>{label}</span><span style={{ fontSize: 8 }}>{open ? '▾' : '▸'}</span>
      </div>
      {open && <div style={{ padding: '6px 12px' }}>{children}</div>}
    </div>
  );
}

function PipelineStatus({ activeNode }) {
  const nodes = ['Prompt Layer', 'Parsing', 'CAD', 'Render'];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, fontSize: 10.5, color: C.muted }}>
      {nodes.map((n, i) => (
        <React.Fragment key={n}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{
              width: 14, height: 14, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: activeNode >= i ? '#22c55e' : C.border, fontSize: 8, color: '#fff', fontWeight: 800,
              boxShadow: activeNode >= i ? '0 0 6px rgba(34,197,94,0.6)' : 'none', transition: 'all 0.3s',
            }}>{activeNode >= i ? '✓' : ''}</span>
            <span style={{ color: activeNode >= i ? '#d4d4d8' : C.muted, fontWeight: activeNode >= i ? 600 : 400 }}>[{n}]</span>
          </div>
          {i < nodes.length - 1 && <div style={{ width: 32, height: 1.5, margin: '0 2px', background: activeNode > i ? '#22c55e' : C.border, transition: 'background 0.4s' }} />}
        </React.Fragment>
      ))}
    </div>
  );
}

// ─── MODAL SHELL ──────────────────────────────────────────────────────────────
function Modal({ title, onClose, children }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200,
      background: 'rgba(0,0,0,0.65)', display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        background: '#1e1e21', border: `1px solid ${C.border}`, borderRadius: 8,
        width: 420, maxHeight: '80vh', overflow: 'auto',
        boxShadow: '0 24px 80px rgba(0,0,0,0.7)',
      }}>
        <div style={{ padding: '14px 16px', borderBottom: `1px solid ${C.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: '#fff' }}>{title}</span>
          <span onClick={onClose} style={{ cursor: 'pointer', color: C.muted, fontSize: 16 }}>✕</span>
        </div>
        <div style={{ padding: 16 }}>{children}</div>
      </div>
    </div>
  );
}

function FormField({ label, type = 'text', value, onChange, options, min, max, step }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <label style={{ fontSize: 10, color: C.muted, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8, display: 'block', marginBottom: 4 }}>{label}</label>
      {type === 'select' ? (
        <select value={value} onChange={e => onChange(e.target.value)}
          style={{ width: '100%', background: '#111114', border: `1px solid ${C.border}`, borderRadius: 4, padding: '7px 10px', color: C.text, fontSize: 12, outline: 'none' }}>
          {options.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : (
        <input type={type} value={value} onChange={e => onChange(e.target.value)} min={min} max={max} step={step}
          style={{ width: '100%', boxSizing: 'border-box', background: '#111114', border: `1px solid ${C.border}`, borderRadius: 4, padding: '7px 10px', color: C.text, fontSize: 12, outline: 'none' }} />
      )}
    </div>
  );
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────
export default function Home() {
  const [cadData, setCadData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [servicesOnline, setServicesOnline] = useState(false);
  const [activeNode, setActiveNode] = useState(-1);
  const [showChat, setShowChat] = useState(false);
  const [activeTab, setActiveTab] = useState('Feature');
  const [showBom, setShowBom] = useState(false);

  // Modal states
  const [showEditModal, setShowEditModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showEntitiesModal, setShowEntitiesModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showToolModal, setShowToolModal] = useState(null); // 'rotate'|'scale'|'fillet'|'move'|'boolean'

  // Edit params
  const [editParams, setEditParams] = useState({});
  const [editLoading, setEditLoading] = useState(false);
  const [editMsg, setEditMsg] = useState('');

  // Import state
  const [importFile, setImportFile] = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importMsg, setImportMsg] = useState('');
  const importRef = useRef(null);

  // Entities state
  const [entities, setEntities] = useState([]);
  const [entitiesLoading, setEntitiesLoading] = useState(false);
  const [entitiesError, setEntitiesError] = useState('');
  const [selectedEntity, setSelectedEntity] = useState(null);

  const normalizeEntity = useCallback((row, index) => {
    const bb = Array.isArray(row?.bounding_box) && row.bounding_box.length === 6
      ? row.bounding_box.map((x) => Number(x) || 0)
      : [0, 0, 0, 0, 0, 0];

    const sx = row?.size_x_mm != null ? Number(row.size_x_mm) : Math.abs(bb[3] - bb[0]) * 10;
    const sy = row?.size_y_mm != null ? Number(row.size_y_mm) : Math.abs(bb[4] - bb[1]) * 10;
    const sz = row?.size_z_mm != null ? Number(row.size_z_mm) : Math.abs(bb[5] - bb[2]) * 10;

    return {
      id: String(row?.id ?? row?.name ?? `entity_${index + 1}`),
      name: String(row?.name ?? row?.id ?? `Entity ${index + 1}`),
      material: String(row?.material ?? 'steel'),
      part_type: String(row?.part_type ?? 'Shape'),
      volume_m3: Number(row?.volume_m3 || 0),
      mass_kg: Number(row?.mass_kg || 0),
      size_x_mm: Number.isFinite(sx) ? sx : 0,
      size_y_mm: Number.isFinite(sy) ? sy : 0,
      size_z_mm: Number.isFinite(sz) ? sz : 0,
      bounding_box: bb,
    };
  }, []);

  // Tool modal params
  const [toolParams, setToolParams] = useState({ axis: 'Z', angle: 90, factor: 1.5, radius: 0.5, moveX: 0, moveY: 0, moveZ: 0 });
  const [toolLoading, setToolLoading] = useState(false);
  const [toolMsg, setToolMsg] = useState('');

  const chatEndRef = useRef(null);
  const fileName = cadData ? cadData.name : 'Untitled_Assembly';

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  useEffect(() => {
    const checkAll = async () => {
      try { await Promise.all([checkLlmHealth(), checkMcpHealth(), checkCadHealth()]); setServicesOnline(true); }
      catch { setServicesOnline(false); }
    };
    checkAll();
    const iv = setInterval(checkAll, 10000);
    return () => clearInterval(iv);
  }, []);

  const triggerPipeline = () => {
    [0, 1, 2, 3].forEach(i => setTimeout(() => setActiveNode(i), i * 350));
    setTimeout(() => setActiveNode(-1), 5000);
  };

  // Comprehensive cadData extraction that handles all response formats
  const extractCadData = (response) => {
    if (!response) return null;
    
    // Direct fields on response root
    if (response.step_b64 || response.glb_b64) {
      return {
        name: response.name || response.shape_description || 'shape',
        volume_m3: response.volume_m3 || 0,
        surface_area_m2: response.surface_area_m2 || 0,
        mass_kg: response.mass_kg || 0,
        material: response.material || 'steel',
        density_kg_m3: response.density_kg_m3 || 7850,
        bounding_box: response.bounding_box || [0,0,0,5,5,5],
        step_b64: response.step_b64 || null,
        glb_b64: response.glb_b64 || null,
        part_type: response.part_type || response.shape_description || '',
        num_teeth: response.num_teeth || null,
        module: response.module || null,
        thickness_mm: response.thickness_mm || null,
        pitch_diameter_mm: response.pitch_diameter_mm || null,
        outer_diameter_mm: response.outer_diameter_mm || null,
      };
    }
    
    // Nested under result.data
    if (response.result?.data) {
      const d = response.result.data;
      if (d.step_b64 || d.glb_b64 || d.bounding_box) {
        return {
          name: d.name || d.shape_description || 'shape',
          volume_m3: d.volume_m3 || 0,
          surface_area_m2: d.surface_area_m2 || 0,
          mass_kg: d.mass_kg || 0,
          material: d.material || 'steel',
          density_kg_m3: d.density_kg_m3 || 7850,
          bounding_box: d.bounding_box || [0,0,0,5,5,5],
          step_b64: d.step_b64 || null,
          glb_b64: d.glb_b64 || null,
          part_type: d.part_type || d.shape_description || '',
          num_teeth: d.num_teeth || null,
          module: d.module || null,
          thickness_mm: d.thickness_mm || null,
          pitch_diameter_mm: d.pitch_diameter_mm || null,
          outer_diameter_mm: d.outer_diameter_mm || null,
        };
      }
    }
    
    // Nested under data
    if (response.data?.step_b64 || response.data?.glb_b64 || response.data?.bounding_box) {
      const d = response.data;
      return {
        name: d.name || 'shape',
        volume_m3: d.volume_m3 || 0,
        surface_area_m2: d.surface_area_m2 || 0,
        mass_kg: d.mass_kg || 0,
        material: d.material || 'steel',
        density_kg_m3: d.density_kg_m3 || 7850,
        bounding_box: d.bounding_box || [0,0,0,5,5,5],
        step_b64: d.step_b64 || null,
        glb_b64: d.glb_b64 || null,
        part_type: d.part_type || '',
        num_teeth: d.num_teeth || null,
        module: d.module || null,
        thickness_mm: d.thickness_mm || null,
        pitch_diameter_mm: d.pitch_diameter_mm || null,
        outer_diameter_mm: d.outer_diameter_mm || null,
      };
    }
    
    // Nested under result directly
    if (response.result?.step_b64 || response.result?.glb_b64 || response.result?.bounding_box) {
      const d = response.result;
      return {
        name: d.name || 'shape',
        volume_m3: d.volume_m3 || 0,
        surface_area_m2: d.surface_area_m2 || 0,
        mass_kg: d.mass_kg || 0,
        material: d.material || 'steel',
        density_kg_m3: d.density_kg_m3 || 7850,
        bounding_box: d.bounding_box || [0,0,0,5,5,5],
        step_b64: d.step_b64 || null,
        glb_b64: d.glb_b64 || null,
        part_type: d.part_type || '',
        num_teeth: d.num_teeth || null,
        module: d.module || null,
        thickness_mm: d.thickness_mm || null,
        pitch_diameter_mm: d.pitch_diameter_mm || null,
        outer_diameter_mm: d.outer_diameter_mm || null,
      };
    }
    
    return null;
  };

  // ── SEND PROMPT ──
  const handleSend = async (prompt) => {
    if (!prompt.trim()) return;
    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setMessages(prev => [...prev, { role: 'user', content: prompt, timestamp: ts }]);
    setInputText(''); setLoading(true); triggerPipeline();
    try {
      const response = await sendChatPrompt(prompt);
      const rTs = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const extracted = extractCadData(response);
      let replyText = '';
      const action = response?.parsed_command?.action;
      const resultData = response?.result?.data;
      if (extracted?.name) {
        replyText = `✅ Generated: ${extracted.name.replace(/_/g, ' ')}\nVolume: ${Number(extracted.volume_m3 || 0).toFixed(4)} m³ | Material: ${extracted.material || 'steel'}`;
        if (extracted.mass_kg) replyText += `\nMass: ${Number(extracted.mass_kg).toFixed(2)} kg`;
        if (extracted.pitch_diameter_mm) replyText += `\nPitch Ø: ${extracted.pitch_diameter_mm} mm`;
      } else if (action === 'get_entity_count') {
        replyText = `📊 Entity Count: ${resultData?.count ?? '?'}`;
      } else if (action === 'list_entities') {
        const ents = Array.isArray(resultData) ? resultData : [];
        replyText = ents.length === 0 ? '📋 No entities.' : `📋 ${ents.length} entities:\n` + ents.map((e, i) => `  ${i+1}. ${e.name || e.id}`).join('\n');
      } else if (action === 'rotate_object') { replyText = `🔄 Rotated ${resultData?.id || 'object'}`; }
      else if (action === 'move_object') { replyText = `📍 Moved ${resultData?.id || 'object'}`; }
      else if (action === 'scale_object') { replyText = `📐 Scaled ${resultData?.id || 'object'}`; }
      else if (response?.name) { replyText = `Rendered ${response.name}`; }
      else { replyText = response?.result?.ok ? '✅ Done.' : `ℹ️ ${JSON.stringify(resultData || response, null, 2)}`; }
      setMessages(prev => [...prev, { role: 'ai', content: replyText, timestamp: rTs }]);
      if (extracted?.bounding_box) setCadData(extracted);
      else if (response?.bounding_box) setCadData(response);
    } catch (error) {
      const eTs = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setMessages(prev => [...prev, { role: 'ai', content: `❌ ${error.message}`, timestamp: eTs }]);
    } finally { setLoading(false); }
  };

  // ── DELETE ──
  const handleDelete = async () => {
    if (!cadData?.name) return;
    try {
      await deleteObject(cadData.name);
      setCadData(null);
      setShowDeleteConfirm(false);
      const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setMessages(prev => [...prev, { role: 'ai', content: `🗑 Deleted: ${cadData.name}`, timestamp: ts }]);
    } catch (e) {
      alert(`Delete failed: ${e.message}`);
    }
  };

  // ── EDIT / UPDATE ──
  const openEditModal = () => {
    if (!cadData) return;
    const partType = (cadData.part_type || '').toLowerCase();
    const bb = cadData.bounding_box || [0, 0, 0, 100, 100, 100];
    const inferredX = Math.abs(bb[3] - bb[0]);
    const inferredY = Math.abs(bb[4] - bb[1]);
    const inferredZ = Math.abs(bb[5] - bb[2]);
    
    // Initialize edit params based on object type
    if (partType.includes('gear')) {
      setEditParams({
        partType: 'gear',
        num_teeth: cadData.num_teeth || 24,
        module: cadData.module || 2.0,
        thickness: cadData.thickness_mm || 8.0,
        bore_radius: cadData.bore_radius_mm || 8.0,
        material: cadData.material || 'steel',
      });
    } else if (partType.includes('cylinder') || partType.includes('pipe') || partType.includes('shaft')) {
      setEditParams({
        partType: 'cylinder',
        radius: cadData.radius_mm || Math.max(inferredX, inferredY) / 2,
        height: cadData.height_mm || inferredZ,
        material: cadData.material || 'steel',
      });
    } else if (partType.includes('sphere') || partType.includes('ball')) {
      setEditParams({
        partType: 'sphere',
        radius: cadData.radius_mm || Math.max(inferredX, inferredY, inferredZ) / 2,
        material: cadData.material || 'steel',
      });
    } else if (partType.includes('cone')) {
      setEditParams({
        partType: 'cone',
        radius: cadData.radius_mm || Math.max(inferredX, inferredY) / 2,
        height: cadData.height_mm || inferredZ,
        material: cadData.material || 'steel',
      });
    } else {
      // Default to box (most common primitive)
      setEditParams({
        partType: 'box',
        length: cadData.length_mm || inferredX,
        width: cadData.width_mm || inferredY,
        height: cadData.height_mm || inferredZ,
        material: cadData.material || 'steel',
      });
    }
    setEditMsg('');
    setShowEditModal(true);
  };

  const handleUpdate = async () => {
    if (!cadData?.name) return;
    setEditLoading(true); setEditMsg('');
    try {
      // For gears, use the backend update endpoint
      if (editParams.partType === 'gear') {
        const result = await updateShape(cadData.name, editParams);
        setCadData(result);
        setShowEditModal(false);
        const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        setMessages(prev => [...prev, { role: 'ai', content: `✅ Updated: ${result.name}`, timestamp: ts }]);
      } else {
        // For other primitives, regenerate via AI prompt
        let prompt = '';
        switch (editParams.partType) {
          case 'box':
            prompt = `create a box ${editParams.length} by ${editParams.width} by ${editParams.height} ${editParams.material}`;
            break;
          case 'cylinder':
            prompt = `create a cylinder radius ${editParams.radius} height ${editParams.height} ${editParams.material}`;
            break;
          case 'sphere':
            prompt = `create a sphere radius ${editParams.radius} ${editParams.material}`;
            break;
          case 'cone':
            prompt = `create a cone radius ${editParams.radius} height ${editParams.height} ${editParams.material}`;
            break;
          default:
            setEditMsg('❌ Unknown part type');
            setEditLoading(false);
            return;
        }
        // Delete old and create new
        await deleteObject(cadData.name);
        await handleSend(prompt);
        setShowEditModal(false);
      }
    } catch (e) {
      setEditMsg(`❌ ${e.message}`);
    } finally { setEditLoading(false); }
  };

  // ── IMPORT STEP ──
  const handleImport = async () => {
    if (!importFile) return;
    setImportLoading(true); setImportMsg('');
    try {
      const result = await importStepFile(importFile);
      const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setMessages(prev => [...prev, { role: 'ai', content: `📥 Imported: ${result.name}\nSize: ${result.size_x_mm}×${result.size_y_mm}×${result.size_z_mm} mm\nVol: ${Number(result.volume_m3).toFixed(5)} m³`, timestamp: ts }]);
      if (result.bounding_box) setCadData(result);
      setShowImportModal(false);
      setImportFile(null);
    } catch (e) {
      setImportMsg(`❌ ${e.message}`);
    } finally { setImportLoading(false); }
  };

  // ── ENTITIES ──
  const loadEntities = useCallback(async () => {
    setEntitiesLoading(true);
    setEntitiesError('');
    try {
      const data = await fetchEntities();
      const rows = Array.isArray(data) ? data.map((row, index) => normalizeEntity(row, index)) : [];
      setEntities(rows);
      setSelectedEntity((prev) => (prev && rows.some((e) => e.id === prev) ? prev : null));
    } catch (e) {
      setEntities([]);
      setEntitiesError(e.message || 'Could not load entities');
    } finally {
      setEntitiesLoading(false);
    }
  }, [normalizeEntity]);

  const openEntities = useCallback(async () => {
    setShowEntitiesModal(true);
    await loadEntities();
  }, [loadEntities]);

  // ── EXPORT STEP ──
  const handleExport = () => {
    if (!cadData?.step_b64) return;
    const bin = atob(cadData.step_b64);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    const blob = new Blob([arr], { type: 'application/step' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `${cadData.name || 'model'}.step`; a.click();
    URL.revokeObjectURL(url);
  };

  // ── SEND FROM TOOLBAR ──
  const toolbarAction = (prompt) => { setInputText(prompt); handleSend(prompt); };

  // Derived sizes
  let sizeX = 0, sizeY = 0, sizeZ = 0, massKg = 0;
  if (cadData?.bounding_box) {
    const [x0, y0, z0, x1, y1, z1] = cadData.bounding_box;
    sizeX = Math.abs(x1 - x0); sizeY = Math.abs(y1 - y0); sizeZ = Math.abs(z1 - z0);
    massKg = cadData.mass_kg || (cadData.volume_m3 * (cadData.density_kg_m3 || 7850));
  }

  const llmLines = cadData ? [
    cadData.part_type && `> ${cadData.part_type.toUpperCase().replace(/ /g, '_')}`,
    cadData.num_teeth && `> TEETH ${cadData.num_teeth}`,
    cadData.module && `> MODULE ${cadData.module}`,
    cadData.pitch_diameter_mm && `> PITCH_DIA ${cadData.pitch_diameter_mm} mm`,
    cadData.material && `> MATERIAL ${cadData.material.toUpperCase()}`,
    cadData.mass_kg && `> MASS ${Number(cadData.mass_kg).toFixed(2)} kg`,
    cadData.bounding_box && `> BBOX ${sizeX.toFixed(0)}×${sizeY.toFixed(0)}×${sizeZ.toFixed(0)}`,
  ].filter(Boolean) : ['> AWAITING INPUT'];

  const aiHistory = messages.filter(m => m.role === 'user').slice(-4);
  const TABS = ['Sketch', 'Feature', 'Assemble', 'Evaluate', 'Render', 'AI Command', 'BOM'];

  const TOOLBAR_ITEMS = [
    { icon: '⬜', label: 'Box', action: () => toolbarAction('create a box 50 by 50 by 100 steel'), tooltip: 'Create a new box primitive' },
    { icon: '⚪', label: 'Cylinder', action: () => toolbarAction('create a cylinder radius 30 height 80 steel'), tooltip: 'Create a new cylinder primitive' },
    { icon: '⚙️', label: 'Gear', action: () => toolbarAction('create a spur gear 24 teeth module 2 steel'), tooltip: 'Create a new spur gear' },
    { divider: true },
    { icon: '↻', label: 'Rotate', action: () => cadData && setShowToolModal('rotate'), disabled: !cadData, tooltip: 'Rotate selected object around axis' },
    { icon: '⤢', label: 'Scale', action: () => cadData && setShowToolModal('scale'), disabled: !cadData, tooltip: 'Scale selected object uniformly' },
    { icon: '↔', label: 'Move', action: () => cadData && setShowToolModal('move'), disabled: !cadData, tooltip: 'Move selected object' },
    { divider: true },
    { icon: '✏️', label: 'Edit', action: () => openEditModal(), disabled: !cadData, tooltip: 'Edit parameters of selected object' },
    { icon: '🗑️', label: 'Delete', action: () => cadData && setShowDeleteConfirm(true), danger: true, disabled: !cadData, tooltip: 'Delete selected object' },
    { divider: true },
    { icon: '📥', label: 'Import', action: () => setShowImportModal(true), tooltip: 'Import STEP file' },
    { icon: '💾', label: 'Export', action: () => handleExport(), disabled: !cadData, tooltip: 'Export current model as STEP' },
    { icon: '📋', label: 'Entities', action: () => openEntities(), tooltip: 'View all scene entities' },
    { icon: '🔭', label: 'AR', action: () => window.open('/ar-view.html', '_blank'), tooltip: 'View in Augmented Reality' },
    { divider: true },
    { icon: '◐', label: 'Fillet', action: null, disabled: true, tooltip: 'Fillet edges (coming soon)' },
    { icon: '▢', label: 'Chamfer', action: null, disabled: true, tooltip: 'Chamfer edges (coming soon)' },
  ];

  // ─── JSX ──────────────────────────────────────────────────────────────────
  return (
    <div style={{ height: '100vh', background: C.bg, color: C.text, fontFamily: '"Segoe UI","Inter",system-ui,sans-serif', display: 'flex', flexDirection: 'column', overflow: 'hidden', fontSize: 12 }}>

      {/* ═══ MODALS ═══ */}

      {/* Delete confirm */}
      {showDeleteConfirm && (
        <Modal title="Delete Object" onClose={() => setShowDeleteConfirm(false)}>
          <p style={{ color: C.text, marginBottom: 16, fontSize: 13 }}>
            Are you sure you want to delete <strong style={{ color: C.accent }}>{cadData?.name}</strong> from the scene?
          </p>
          <p style={{ color: C.muted, fontSize: 11, marginBottom: 20 }}>This action cannot be undone.</p>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => setShowDeleteConfirm(false)} style={{ flex: 1, padding: '9px 0', background: 'transparent', border: `1px solid ${C.border}`, color: C.text, borderRadius: 4, cursor: 'pointer', fontSize: 12 }}>Cancel</button>
            <button onClick={handleDelete} style={{ flex: 1, padding: '9px 0', background: C.danger, border: 'none', color: '#fff', borderRadius: 4, cursor: 'pointer', fontSize: 12, fontWeight: 700 }}>🗑 Delete</button>
          </div>
        </Modal>
      )}

      {/* Edit / Update modal */}
      {showEditModal && cadData && (
        <Modal title={`Edit: ${cadData.name}`} onClose={() => setShowEditModal(false)}>
          {/* Object type indicator */}
          <div style={{ 
            padding: '8px 12px', marginBottom: 14, borderRadius: 4,
            background: 'rgba(0,197,184,0.08)', border: `1px solid rgba(0,197,184,0.2)`,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between'
          }}>
            <span style={{ fontSize: 11, color: C.accent }}>
              <strong>Type:</strong> {cadData.part_type || 'Shape'}
            </span>
            <span style={{ fontSize: 10, color: C.muted }}>
              {editParams.partType === 'gear' ? '(Direct update)' : '(Regenerate)'}
            </span>
          </div>

          {/* Gear-specific parameters */}
          {editParams.partType === 'gear' && (
            <>
              <FormField label="Number of Teeth" type="number" min={8} max={60} value={editParams.num_teeth} onChange={v => setEditParams(p => ({ ...p, num_teeth: parseInt(v) || 24 }))} />
              <FormField label="Module (mm)" type="number" min={0.5} max={10} step={0.5} value={editParams.module} onChange={v => setEditParams(p => ({ ...p, module: parseFloat(v) || 2 }))} />
              <FormField label="Thickness (mm)" type="number" min={2} max={50} value={editParams.thickness} onChange={v => setEditParams(p => ({ ...p, thickness: parseFloat(v) || 8 }))} />
              <FormField label="Bore Radius (mm)" type="number" min={1} max={30} value={editParams.bore_radius} onChange={v => setEditParams(p => ({ ...p, bore_radius: parseFloat(v) || 8 }))} />
              <FormField label="Material" type="select" value={editParams.material} options={['steel', 'aluminum', 'plastic', 'cast_iron']} onChange={v => setEditParams(p => ({ ...p, material: v }))} />
            </>
          )}

          {/* Box parameters */}
          {editParams.partType === 'box' && (
            <>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 10 }}>
                Define the dimensions of the box (in mm). Changes will regenerate the geometry.
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                <FormField label="Length (X)" type="number" min={1} step={5} value={editParams.length} onChange={v => setEditParams(p => ({ ...p, length: parseFloat(v) || 50 }))} />
                <FormField label="Width (Y)" type="number" min={1} step={5} value={editParams.width} onChange={v => setEditParams(p => ({ ...p, width: parseFloat(v) || 50 }))} />
                <FormField label="Height (Z)" type="number" min={1} step={5} value={editParams.height} onChange={v => setEditParams(p => ({ ...p, height: parseFloat(v) || 100 }))} />
              </div>
              <FormField label="Material" type="select" value={editParams.material} options={['steel', 'aluminum', 'plastic', 'cast_iron']} onChange={v => setEditParams(p => ({ ...p, material: v }))} />
            </>
          )}

          {/* Cylinder parameters */}
          {editParams.partType === 'cylinder' && (
            <>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 10 }}>
                Define the cylinder dimensions (in mm). Changes will regenerate the geometry.
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <FormField label="Radius (mm)" type="number" min={1} step={5} value={editParams.radius} onChange={v => setEditParams(p => ({ ...p, radius: parseFloat(v) || 30 }))} />
                <FormField label="Height (mm)" type="number" min={1} step={5} value={editParams.height} onChange={v => setEditParams(p => ({ ...p, height: parseFloat(v) || 80 }))} />
              </div>
              <FormField label="Material" type="select" value={editParams.material} options={['steel', 'aluminum', 'plastic', 'cast_iron']} onChange={v => setEditParams(p => ({ ...p, material: v }))} />
            </>
          )}

          {/* Sphere parameters */}
          {editParams.partType === 'sphere' && (
            <>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 10 }}>
                Define the sphere radius (in mm). Changes will regenerate the geometry.
              </div>
              <FormField label="Radius (mm)" type="number" min={1} step={5} value={editParams.radius} onChange={v => setEditParams(p => ({ ...p, radius: parseFloat(v) || 25 }))} />
              <FormField label="Material" type="select" value={editParams.material} options={['steel', 'aluminum', 'plastic', 'cast_iron']} onChange={v => setEditParams(p => ({ ...p, material: v }))} />
            </>
          )}

          {/* Cone parameters */}
          {editParams.partType === 'cone' && (
            <>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 10 }}>
                Define the cone dimensions (in mm). Changes will regenerate the geometry.
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <FormField label="Base Radius (mm)" type="number" min={1} step={5} value={editParams.radius} onChange={v => setEditParams(p => ({ ...p, radius: parseFloat(v) || 30 }))} />
                <FormField label="Height (mm)" type="number" min={1} step={5} value={editParams.height} onChange={v => setEditParams(p => ({ ...p, height: parseFloat(v) || 60 }))} />
              </div>
              <FormField label="Material" type="select" value={editParams.material} options={['steel', 'aluminum', 'plastic', 'cast_iron']} onChange={v => setEditParams(p => ({ ...p, material: v }))} />
            </>
          )}

          {editMsg && (
            <div style={{ 
              padding: '8px 12px', marginBottom: 10, borderRadius: 4,
              background: editMsg.startsWith('✅') ? 'rgba(74,222,128,0.1)' : 'rgba(252,165,165,0.1)', 
              border: `1px solid ${editMsg.startsWith('✅') ? 'rgba(74,222,128,0.3)' : 'rgba(252,165,165,0.3)'}`,
              color: editMsg.startsWith('✅') ? '#4ade80' : '#fca5a5', 
              fontSize: 11 
            }}>
              {editMsg}
            </div>
          )}
          
          <button onClick={handleUpdate} disabled={editLoading}
            style={{ 
              width: '100%', padding: '10px 0', 
              background: editLoading ? '#333' : C.accent, 
              border: 'none', color: editLoading ? '#666' : '#000', 
              fontWeight: 700, borderRadius: 4, 
              cursor: editLoading ? 'not-allowed' : 'pointer', 
              fontSize: 12, transition: 'all 0.15s'
            }}>
            {editLoading ? '⟳ Updating…' : '✓ Apply Changes'}
          </button>
        </Modal>
      )}

      {/* Import STEP modal */}
      {showImportModal && (
        <Modal title="Import STEP File" onClose={() => { setShowImportModal(false); setImportFile(null); setImportMsg(''); }}>
          <div style={{ color: C.muted, fontSize: 11, marginBottom: 12 }}>
            Import a .step or .stp file to add it to the scene. Its dimensions and entity count will be computed automatically.
          </div>
          <div
            onClick={() => importRef.current?.click()}
            onDrop={e => { e.preventDefault(); setImportFile(e.dataTransfer.files[0]); }}
            onDragOver={e => e.preventDefault()}
            style={{
              border: `2px dashed ${importFile ? C.accent : C.border}`, borderRadius: 6,
              padding: '24px 16px', textAlign: 'center', cursor: 'pointer',
              background: importFile ? 'rgba(0,197,184,0.05)' : 'transparent',
              marginBottom: 12, transition: 'all 0.2s',
            }}>
            <div style={{ fontSize: 28, marginBottom: 6 }}>{importFile ? '📄' : '📂'}</div>
            <div style={{ fontSize: 12, color: importFile ? C.accent : C.muted }}>
              {importFile ? importFile.name : 'Click or drag & drop a .step / .stp file'}
            </div>
          </div>
          <input ref={importRef} type="file" accept=".step,.stp,.STEP,.STP" style={{ display: 'none' }}
            onChange={e => setImportFile(e.target.files[0])} />
          {importMsg && <div style={{ color: '#fca5a5', fontSize: 11, marginBottom: 8 }}>{importMsg}</div>}
          <button onClick={handleImport} disabled={!importFile || importLoading}
            style={{ width: '100%', padding: '9px 0', background: !importFile || importLoading ? '#333' : C.accent, border: 'none', color: !importFile ? '#555' : '#000', fontWeight: 700, borderRadius: 4, cursor: 'pointer', fontSize: 12 }}>
            {importLoading ? '⟳ Importing…' : '📥 Import STEP'}
          </button>
        </Modal>
      )}

      {/* Entities modal */}
      {showEntitiesModal && (
        <Modal title="Scene Entities" onClose={() => { setShowEntitiesModal(false); setEntitiesError(''); }}>
          {entitiesLoading ? (
            <div style={{ textAlign: 'center', padding: 24, color: C.muted }}>⟳ Loading entities…</div>
          ) : entitiesError ? (
            <div style={{ textAlign: 'center', padding: 24, color: '#fca5a5', fontSize: 12 }}>
              ⚠ {entitiesError}
              <div style={{ marginTop: 12, color: C.muted, fontSize: 11 }}>Check that the CAD engine is running on port 5000.</div>
            </div>
          ) : entities.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 24, color: C.muted }}>No entities in scene. Generate a shape first.</div>
          ) : (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <div style={{ fontSize: 10, color: C.muted }}>{entities.length} object(s) in scene</div>
                <button
                  onClick={loadEntities}
                  disabled={entitiesLoading}
                  style={{
                    padding: '4px 9px',
                    border: `1px solid ${C.border}`,
                    background: 'transparent',
                    color: C.text,
                    borderRadius: 4,
                    fontSize: 10,
                    cursor: entitiesLoading ? 'not-allowed' : 'pointer',
                  }}
                >
                  Refresh
                </button>
              </div>
              {entities.map((e, i) => {
                const selected = selectedEntity === e.id;
                return (
                  <div key={e.id || i} onClick={() => setSelectedEntity(selected ? null : e.id)}
                    style={{
                      padding: '10px 12px', marginBottom: 6, borderRadius: 5, cursor: 'pointer',
                      border: `1px solid ${selected ? C.accent : C.border}`,
                      background: selected ? 'rgba(0,197,184,0.07)' : '#1a1a1d',
                      transition: 'all 0.15s',
                    }}>
                    <div style={{ fontWeight: 700, color: '#fff', fontSize: 12, marginBottom: 4 }}>
                      {i + 1}. {e.name}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px 12px', fontSize: 10, color: C.muted }}>
                      <span>Vol: <strong style={{ color: C.text }}>{Number(e.volume_m3 || 0).toFixed(5)} m³</strong></span>
                      <span>Mass: <strong style={{ color: '#4ade80' }}>{Number(e.mass_kg || 0).toFixed(2)} kg</strong></span>
                      <span>X: <strong style={{ color: '#ff6666' }}>{Number(e.size_x_mm || 0).toFixed(1)} mm</strong></span>
                      <span>Y: <strong style={{ color: '#66ff88' }}>{Number(e.size_y_mm || 0).toFixed(1)} mm</strong></span>
                      <span>Z: <strong style={{ color: '#6699ff' }}>{Number(e.size_z_mm || 0).toFixed(1)} mm</strong></span>
                      <span>Mat: <strong style={{ color: '#ffa23b' }}>{e.material || '—'}</strong></span>
                      <span>Type: <strong style={{ color: C.text }}>{e.part_type || 'Shape'}</strong></span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Modal>
      )}

      {/* Tool modals: Rotate / Scale / Move */}
      {showToolModal && (
        <Modal 
          title={
            showToolModal === 'rotate' ? 'Rotate Object' : 
            showToolModal === 'scale' ? 'Scale Object' : 
            showToolModal === 'move' ? 'Move Object' :
            'Apply Fillet'
          }
          onClose={() => { setShowToolModal(null); setToolMsg(''); }}
        >
          {/* Object info banner */}
          <div style={{ 
            padding: '8px 12px', marginBottom: 12, borderRadius: 4,
            background: 'rgba(0,197,184,0.08)', border: `1px solid rgba(0,197,184,0.2)`,
            fontSize: 11, color: C.accent, display: 'flex', alignItems: 'center', gap: 8
          }}>
            <span style={{ fontSize: 16 }}>📦</span>
            <span>Target: <strong>{cadData?.name || 'No object selected'}</strong></span>
          </div>

          {showToolModal === 'rotate' && (
            <>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 10 }}>
                Rotate the selected object around its center point.
              </div>
              <FormField label="Rotation Axis" type="select" value={toolParams.axis} options={['X', 'Y', 'Z']} onChange={v => setToolParams(p => ({ ...p, axis: v }))} />
              <FormField label="Angle (degrees)" type="number" min={-360} max={360} step={15} value={toolParams.angle} onChange={v => setToolParams(p => ({ ...p, angle: parseFloat(v) || 0 }))} />
              {/* Quick angle buttons */}
              <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
                {[45, 90, 180, -90].map(a => (
                  <button key={a} onClick={() => setToolParams(p => ({ ...p, angle: a }))}
                    style={{ flex: 1, padding: '6px 0', background: toolParams.angle === a ? C.accent : '#1a1a1d', 
                      border: `1px solid ${toolParams.angle === a ? C.accent : C.border}`, 
                      color: toolParams.angle === a ? '#000' : C.text, borderRadius: 4, cursor: 'pointer', fontSize: 10, fontWeight: 600 }}>
                    {a}°
                  </button>
                ))}
              </div>
            </>
          )}
          
          {showToolModal === 'scale' && (
            <>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 10 }}>
                Scale the object uniformly from its center.
              </div>
              <FormField label="Scale Factor" type="number" min={0.1} max={10} step={0.1} value={toolParams.factor} onChange={v => setToolParams(p => ({ ...p, factor: parseFloat(v) || 1 }))} />
              {/* Quick scale buttons */}
              <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
                {[0.5, 0.75, 1.5, 2.0].map(f => (
                  <button key={f} onClick={() => setToolParams(p => ({ ...p, factor: f }))}
                    style={{ flex: 1, padding: '6px 0', background: toolParams.factor === f ? C.accent : '#1a1a1d', 
                      border: `1px solid ${toolParams.factor === f ? C.accent : C.border}`, 
                      color: toolParams.factor === f ? '#000' : C.text, borderRadius: 4, cursor: 'pointer', fontSize: 10, fontWeight: 600 }}>
                    {f}×
                  </button>
                ))}
              </div>
            </>
          )}
          
          {showToolModal === 'move' && (
            <>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 10 }}>
                Translate the object in 3D space (values in mm).
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                <FormField label="X (mm)" type="number" step={10} value={toolParams.moveX} onChange={v => setToolParams(p => ({ ...p, moveX: parseFloat(v) || 0 }))} />
                <FormField label="Y (mm)" type="number" step={10} value={toolParams.moveY} onChange={v => setToolParams(p => ({ ...p, moveY: parseFloat(v) || 0 }))} />
                <FormField label="Z (mm)" type="number" step={10} value={toolParams.moveZ} onChange={v => setToolParams(p => ({ ...p, moveZ: parseFloat(v) || 0 }))} />
              </div>
            </>
          )}
          
          {showToolModal === 'fillet' && (
            <>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 10 }}>
                Apply a fillet (rounded edge) to all edges of the object.
              </div>
              <FormField label="Fillet Radius (mm)" type="number" min={0.1} max={20} step={0.5} value={toolParams.radius} onChange={v => setToolParams(p => ({ ...p, radius: parseFloat(v) || 0.5 }))} />
            </>
          )}
          
          {toolMsg && (
            <div style={{ 
              padding: '8px 12px', marginBottom: 10, borderRadius: 4,
              background: toolMsg.startsWith('✅') ? 'rgba(74,222,128,0.1)' : 'rgba(252,165,165,0.1)', 
              border: `1px solid ${toolMsg.startsWith('✅') ? 'rgba(74,222,128,0.3)' : 'rgba(252,165,165,0.3)'}`,
              color: toolMsg.startsWith('✅') ? '#4ade80' : '#fca5a5', 
              fontSize: 11 
            }}>
              {toolMsg}
            </div>
          )}
          
          <button disabled={toolLoading || !cadData?.name} onClick={async () => {
            if (!cadData?.name) { setToolMsg('❌ No active object'); return; }
            setToolLoading(true); setToolMsg('');
            const ts = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            
            try {
              let result;
              if (showToolModal === 'rotate') {
                // Direct CAD API call for rotation
                result = await rotateObject(cadData.name, toolParams.axis, toolParams.angle);
                setMessages(prev => [...prev, { role: 'ai', content: `↻ Rotated ${cadData.name} by ${toolParams.angle}° around ${toolParams.axis}-axis`, timestamp: ts() }]);
              } else if (showToolModal === 'scale') {
                // Direct CAD API call for scaling
                result = await scaleObject(cadData.name, toolParams.factor);
                setMessages(prev => [...prev, { role: 'ai', content: `⤢ Scaled ${cadData.name} by factor ${toolParams.factor}×`, timestamp: ts() }]);
              } else if (showToolModal === 'move') {
                // Direct CAD API call for moving
                result = await moveObject(cadData.name, toolParams.moveX, toolParams.moveY, toolParams.moveZ);
                setMessages(prev => [...prev, { role: 'ai', content: `↔ Moved ${cadData.name} by (${toolParams.moveX}, ${toolParams.moveY}, ${toolParams.moveZ}) mm`, timestamp: ts() }]);
              } else {
                // Fillet uses AI prompt (not directly supported yet)
                await handleSend(`fillet edges of ${cadData.name} with radius ${toolParams.radius}`);
                setToolMsg('✅ Command sent to AI');
                setTimeout(() => { setShowToolModal(null); setToolMsg(''); }, 1000);
                setToolLoading(false);
                return;
              }
              
              // Update the cadData with the transformed result
              if (result && result.bounding_box) {
                setCadData(prev => ({ ...prev, ...result }));
              }
              
              setToolMsg('✅ Transformation applied successfully');
              setTimeout(() => { setShowToolModal(null); setToolMsg(''); }, 800);
            } catch (e) {
              setToolMsg(`❌ ${e.message}`);
            } finally { setToolLoading(false); }
          }}
            style={{ 
              width: '100%', padding: '10px 0', 
              background: (toolLoading || !cadData?.name) ? '#333' : C.accent, 
              border: 'none', color: (toolLoading || !cadData?.name) ? '#666' : '#000', 
              fontWeight: 700, borderRadius: 4, cursor: (toolLoading || !cadData?.name) ? 'not-allowed' : 'pointer', 
              fontSize: 12, transition: 'all 0.15s',
            }}>
            {toolLoading ? '⟳ Applying…' : '✓ Apply Transformation'}
          </button>
        </Modal>
      )}

      {/* ═══ TITLE BAR ═══ */}
      <div style={{ height: 32, background: '#111113', borderBottom: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 12px', flexShrink: 0, userSelect: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 800, color: C.accent, letterSpacing: 1.5 }}>TESSERACT</span>
          <span style={{ color: C.border }}>│</span>
          <span style={{ fontSize: 11, color: C.muted }}>{fileName}</span>
          {cadData && <span style={{ fontSize: 10, color: C.accent }}>● Modified</span>}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: servicesOnline ? '#22c55e' : '#ef4444', boxShadow: servicesOnline ? '0 0 6px #22c55e' : 'none' }} />
            <span style={{ fontSize: 10, color: C.muted }}>{servicesOnline ? 'Online' : 'Offline'}</span>
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            {['─', '□', '✕'].map((s, i) => <div key={i} style={{ width: 24, height: 18, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, color: C.muted, cursor: 'pointer' }}>{s}</div>)}
          </div>
        </div>
      </div>

      {/* ═══ MENU BAR ═══ */}
      <div style={{ height: 30, background: C.sidebar, borderBottom: `1px solid ${C.border}`, display: 'flex', alignItems: 'stretch', padding: '0 8px', flexShrink: 0, gap: 2 }}>
        {TABS.map(tab => (
          <div key={tab} onClick={() => { setActiveTab(tab); setShowBom(tab === 'BOM'); }}
            style={{ padding: '0 14px', display: 'flex', alignItems: 'center', fontSize: 11.5, fontWeight: tab === activeTab ? 700 : 400, color: tab === activeTab ? '#fff' : C.muted, borderBottom: tab === activeTab ? `2px solid ${C.accent}` : '2px solid transparent', cursor: 'pointer', transition: 'all 0.15s' }}>
            {tab === 'AI Command' ? <span style={{ color: C.accent }}>[AI Command]</span> : tab === 'BOM' ? <span style={{ color: showBom ? C.accent : C.muted }}>📋 BOM</span> : `[${tab}]`}
          </div>
        ))}
      </div>

      {/* ═══ TOOLBAR ═══ */}
      <div style={{ height: 68, background: C.toolbar, borderBottom: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', padding: '0 8px', flexShrink: 0, gap: 2, overflowX: 'auto' }}>
        {TOOLBAR_ITEMS.map((t, i) => 
          t.divider ? (
            <div key={i} style={{ width: 1, height: 40, background: C.border, margin: '0 6px', flexShrink: 0 }} />
          ) : (
            <ToolBtn key={i} icon={t.icon} label={t.label} onClick={t.action} active={t.active} danger={t.danger} disabled={t.disabled} tooltip={t.tooltip} />
          )
        )}
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: 10, color: C.muted, paddingRight: 8, flexShrink: 0 }}>pythonOCC 7.9.3</span>
      </div>

      {/* ═══ MAIN CONTENT ═══ */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* ── LEFT: Feature Manager ── */}
        <div style={{ width: 260, background: C.sidebar, borderRight: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', flexShrink: 0, overflow: 'hidden' }}>
          <div style={{ padding: '6px 10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: `1px solid ${C.border}`, background: C.panel }}>
            <span style={{ fontSize: 11.5, fontWeight: 700, color: C.text }}>FeatureManager</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <span title="Import STEP" onClick={() => setShowImportModal(true)} style={{ fontSize: 12, color: C.muted, cursor: 'pointer' }}>📥</span>
              <span title="View Entities" onClick={openEntities} style={{ fontSize: 12, color: C.muted, cursor: 'pointer' }}>📋</span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', padding: '4px 8px', gap: 4, borderBottom: `1px solid ${C.border}`, background: C.panel }}>
            {[
              { ic: '🏠', title: 'Home', action: () => {} },
              { ic: '📐', title: 'Edit Dimensions', action: openEditModal },
              { ic: '🗑', title: 'Delete', action: () => cadData && setShowDeleteConfirm(true) },
              { ic: '📋', title: 'Entities', action: openEntities },
              { ic: '🔭', title: 'View in AR', action: () => window.open('/ar-view.html', '_blank') },
            ].map((b, i) => (
              <span key={i} title={b.title} onClick={b.action} style={{ fontSize: 14, cursor: 'pointer', padding: '3px 5px', borderRadius: 3, color: C.muted, transition: 'color 0.15s' }}
                onMouseEnter={e => e.target.style.color = C.accent} onMouseLeave={e => e.target.style.color = C.muted}>{b.ic}</span>
            ))}
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0' }}>
            <TreeNode icon="📝" label="Annotations" depth={0} />
            <TreeNode icon="📡" label="Sensors" depth={0} />
            <TreeNode icon="🧱" label={`Material: ${cadData?.material || '<not specified>'}`} depth={0} />
            <TreeNode icon="━" label="Front Plane" depth={0} />
            <TreeNode icon="━" label="Top Plane" depth={0} />
            <TreeNode icon="━" label="Right Plane" depth={0} />
            {cadData ? (
              <TreeNode icon="📦" label={cadData.name?.slice(0, 28) || 'Generated Shape'} depth={0} defaultOpen active>
                <TreeNode icon="●" label="Origin" depth={1} />
                <TreeNode icon="📐" label={`Size: ${sizeX.toFixed(0)}×${sizeY.toFixed(0)}×${sizeZ.toFixed(0)} mm`} depth={1} />
                {cadData.part_type && <TreeNode icon="⚙" label={cadData.part_type} depth={1} />}
                {cadData.num_teeth && <TreeNode icon="🦷" label={`Teeth: ${cadData.num_teeth} | Module: ${cadData.module}`} depth={2} />}
                {cadData.pitch_diameter_mm && <TreeNode icon="⭕" label={`Pitch Ø: ${cadData.pitch_diameter_mm} mm`} depth={2} />}
                {cadData.material && <TreeNode icon="🧪" label={`Material: ${cadData.material}`} depth={2} />}
                <TreeNode icon="⚖" label={`Mass: ${Number(massKg).toFixed(2)} kg`} depth={2} />
                <TreeNode icon="📦" label={`Vol: ${Number(cadData.volume_m3 || 0).toFixed(5)} m³`} depth={2} />
              </TreeNode>
            ) : (
              <TreeNode icon="📁" label="Assembly_Root" depth={0} defaultOpen>
                <TreeNode icon="●" label="Origin" depth={1} />
                <TreeNode icon="🔲" label="Default Plane (XY)" depth={1} />
              </TreeNode>
            )}
          </div>
        </div>

        {/* ── CENTER: Viewport ── */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden' }}>
          <div style={{ flex: 1, overflow: 'hidden', background: '#101014', position: 'relative' }}>
            <Viewer cadData={cadData} />

            {showBom && (
              <div style={{ position: 'absolute', inset: 0, zIndex: 50, background: C.bg, display: 'flex', flexDirection: 'column' }}>
                <BomPanel refreshToken={`${cadData?.name || ''}:${cadData?.mass_kg || ''}:${messages.length}`} />
              </div>
            )}

            {/* Color palette */}
            <div style={{ position: 'absolute', bottom: 52, left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: 8, padding: '8px 16px', borderRadius: 32, background: 'rgba(26,26,30,0.82)', backdropFilter: 'blur(12px)', border: `1px solid ${C.border}`, zIndex: 20 }}>
              {['#ef4444', '#f97316', '#22c55e', '#3b82f6', '#d4d4d8'].map((c, i) => (
                <div key={i} style={{ width: 20, height: 20, borderRadius: '50%', background: c, cursor: 'pointer', boxShadow: '0 2px 6px rgba(0,0,0,0.5)', transition: 'transform 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.2)'}
                  onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'} />
              ))}
            </div>

            {/* Context chips */}
            {cadData && (
              <div style={{ position: 'absolute', bottom: 52, left: 16, display: 'flex', gap: 6, zIndex: 20 }}>
                {cadData.material && <ContextChip>Mat: {cadData.material}</ContextChip>}
                {cadData.pitch_diameter_mm && <ContextChip>Pitch Ø {cadData.pitch_diameter_mm}mm</ContextChip>}
                {sizeX > 0 && <ContextChip>{sizeX.toFixed(0)}×{sizeY.toFixed(0)}×{sizeZ.toFixed(0)} mm</ContextChip>}
              </div>
            )}
          </div>

          {showChat && (
            <div style={{ height: 240, background: C.sidebar, borderTop: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column' }}>
              <div style={{ flex: 1, overflowY: 'auto', padding: '8px 12px' }}>
                {messages.length === 0 && <div style={{ color: C.muted, fontSize: 11, textAlign: 'center', marginTop: 16 }}>Send a prompt to start generating geometry</div>}
                {messages.map((m, i) => (
                  <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, flexDirection: m.role === 'user' ? 'row-reverse' : 'row', alignItems: 'flex-start' }}>
                    <div style={{ fontSize: 9, color: C.muted, paddingTop: 2, minWidth: 36, textAlign: m.role === 'user' ? 'right' : 'left' }}>{m.role === 'user' ? '👤' : '🤖'} {m.timestamp}</div>
                    <div style={{ maxWidth: '80%', padding: '6px 10px', borderRadius: 8, background: m.role === 'user' ? 'rgba(0,197,184,0.12)' : 'rgba(255,255,255,0.04)', border: `1px solid ${m.role === 'user' ? 'rgba(0,197,184,0.25)' : C.border}`, fontSize: 12, color: C.text, whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>{m.content}</div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT: Property Manager ── */}
        <div style={{ width: 220, background: C.panel, borderLeft: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', flexShrink: 0, overflowY: 'auto' }}>
          <div style={{ padding: '7px 12px', borderBottom: `1px solid ${C.border}`, background: '#222225' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: C.text }}>PropertyManager</div>
            {cadData && <div style={{ fontSize: 9, color: C.accent, marginTop: 2 }}>{cadData.part_type || 'Shape'}</div>}
          </div>
          {cadData ? (
            <>
              <SectionHdr label="Dimensions">
                <PropRow label="Size X" value={sizeX.toFixed(1)} unit="mm" valueColor="#ff6666" />
                <PropRow label="Size Y" value={sizeY.toFixed(1)} unit="mm" valueColor="#66ff88" />
                <PropRow label="Size Z" value={sizeZ.toFixed(1)} unit="mm" valueColor="#6699ff" />
              </SectionHdr>
              <SectionHdr label="Physical Properties">
                <PropRow label="Volume" value={Number(cadData.volume_m3).toFixed(4)} unit="m³" />
                <PropRow label="Surface Area" value={Number(cadData.surface_area_m2).toFixed(3)} unit="m²" />
                <PropRow label="Mass" value={Number(massKg).toFixed(2)} unit="kg" valueColor="#22c55e" />
              </SectionHdr>
              {cadData.num_teeth && (
                <SectionHdr label="Gear Parameters">
                  <PropRow label="Teeth" value={cadData.num_teeth} editable onEdit={openEditModal} />
                  <PropRow label="Module" value={cadData.module} unit="mm" editable onEdit={openEditModal} />
                  <PropRow label="Pitch Ø" value={cadData.pitch_diameter_mm} unit="mm" valueColor={C.accent} />
                  <PropRow label="Outer Ø" value={cadData.outer_diameter_mm || '—'} unit="mm" />
                  {cadData.thickness_mm && <PropRow label="Thickness" value={cadData.thickness_mm} unit="mm" editable onEdit={openEditModal} />}
                </SectionHdr>
              )}
              <SectionHdr label="Material">
                <PropRow label="Type" value={(cadData.material || 'steel').charAt(0).toUpperCase() + (cadData.material || 'steel').slice(1)} valueColor="#ffa23b" editable onEdit={openEditModal} />
                <PropRow label="Density" value={cadData.density_kg_m3 || 7850} unit="kg/m³" />
              </SectionHdr>
              
              {/* Quick Transform buttons */}
              <SectionHdr label="Transform">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 4 }}>
                  <button onClick={() => setShowToolModal('rotate')} style={{ padding: '6px 0', background: 'transparent', border: `1px solid ${C.border}`, color: C.text, fontSize: 9, borderRadius: 3, cursor: 'pointer' }}
                    onMouseEnter={e => e.target.style.borderColor = C.accent} onMouseLeave={e => e.target.style.borderColor = C.border}>↻ Rotate</button>
                  <button onClick={() => setShowToolModal('scale')} style={{ padding: '6px 0', background: 'transparent', border: `1px solid ${C.border}`, color: C.text, fontSize: 9, borderRadius: 3, cursor: 'pointer' }}
                    onMouseEnter={e => e.target.style.borderColor = C.accent} onMouseLeave={e => e.target.style.borderColor = C.border}>⤢ Scale</button>
                  <button onClick={() => setShowToolModal('move')} style={{ padding: '6px 0', background: 'transparent', border: `1px solid ${C.border}`, color: C.text, fontSize: 9, borderRadius: 3, cursor: 'pointer' }}
                    onMouseEnter={e => e.target.style.borderColor = C.accent} onMouseLeave={e => e.target.style.borderColor = C.border}>↔ Move</button>
                </div>
              </SectionHdr>
              
              <SectionHdr label="AI History" defaultOpen={false}>
                {aiHistory.length === 0 ? (
                  <div style={{ fontSize: 10, color: C.muted }}>No history yet</div>
                ) : aiHistory.map((m, i) => (
                  <div key={i} style={{ fontSize: 10, color: C.muted, padding: '3px 0', borderBottom: `1px solid ${C.border}` }}>
                    {m.content.slice(0, 40)}…
                  </div>
                ))}
              </SectionHdr>
              <SectionHdr label="LLM Interpretation" defaultOpen={false}>
                <div style={{ fontFamily: '"Cascadia Code","Courier New",monospace', fontSize: 10, color: '#a0f0e8', background: '#0d1f1e', borderRadius: 4, padding: '8px', lineHeight: 1.8, border: '1px solid rgba(0,197,184,0.2)' }}>
                  {llmLines.map((l, i) => <div key={i}>{l}</div>)}
                </div>
              </SectionHdr>

              {/* Action buttons */}
              <div style={{ padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 6, marginTop: 'auto' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  <button onClick={openEditModal} style={{ padding: '7px 0', background: 'transparent', border: `1px solid ${C.accent}`, color: C.accent, fontSize: 10, fontWeight: 600, borderRadius: 4, cursor: 'pointer' }}>✏️ Edit</button>
                  <button onClick={() => setShowDeleteConfirm(true)} style={{ padding: '7px 0', background: 'transparent', border: `1px solid ${C.danger}`, color: C.danger, fontSize: 10, fontWeight: 600, borderRadius: 4, cursor: 'pointer' }}>🗑️ Delete</button>
                </div>
                <button onClick={handleExport} style={{ width: '100%', padding: '8px 0', background: 'transparent', border: `1px solid ${C.border}`, color: C.text, fontSize: 11, fontWeight: 600, borderRadius: 4, cursor: 'pointer' }}
                  onMouseEnter={e => e.target.style.borderColor = C.accent} onMouseLeave={e => e.target.style.borderColor = C.border}>💾 Export STEP</button>
                <button onClick={() => window.open('/ar-view.html', '_blank')} style={{ width: '100%', padding: '8px 0', background: C.accent, border: 'none', color: '#000', fontSize: 11, fontWeight: 700, borderRadius: 4, cursor: 'pointer', boxShadow: `0 0 12px rgba(0,197,184,0.4)` }}>
                  🔭 View in AR
                </button>
              </div>
            </>
          ) : (
            <div style={{ padding: 16, fontSize: 11, color: C.muted, textAlign: 'center', marginTop: 20 }}>
              No model loaded.<br /><br />
              <button onClick={() => setShowImportModal(true)} style={{ padding: '7px 14px', background: 'transparent', border: `1px solid ${C.accent}`, color: C.accent, fontSize: 11, fontWeight: 600, borderRadius: 4, cursor: 'pointer', marginBottom: 8 }}>📥 Import STEP</button>
              <br />
              or type a prompt below to generate geometry.
            </div>
          )}
        </div>
      </div>

      {/* ═══ BOTTOM BAR ═══ */}
      <div style={{ background: C.sidebar, borderTop: `1px solid ${C.border}`, flexShrink: 0 }}>
        {/* Prompt Preview (when typing) */}
        {inputText.trim() && !loading && (
          <div style={{ 
            padding: '6px 16px', 
            borderBottom: `1px solid ${C.border}`,
            background: 'rgba(0,197,184,0.03)',
            display: 'flex', alignItems: 'center', gap: 12
          }}>
            <span style={{ fontSize: 9, color: C.muted, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Preview:
            </span>
            <PromptPreview text={inputText} />
          </div>
        )}
        
        <div style={{ height: 58, display: 'flex', alignItems: 'center', padding: '0 16px', gap: 12 }}>
          <div style={{ flexShrink: 0 }}>
            <div style={{ fontSize: 9.5, color: C.accent, fontWeight: 700, letterSpacing: 0.8 }}>Smart Prompt Input</div>
            <div style={{ fontSize: 9, color: C.muted }}>Describe your geometry…</div>
          </div>
          <input value={inputText} onChange={e => setInputText(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) handleSend(inputText); }}
            placeholder={loading ? 'Processing...' : 'e.g., "create a gear 24 teeth module 2 steel" or "make a box 50x50x100"'}
            disabled={loading}
            style={{ flex: 1, background: '#111114', border: `1px solid ${C.border}`, borderRadius: 6, padding: '9px 14px', color: C.text, fontSize: 12, outline: 'none' }}
            onFocus={e => e.target.style.borderColor = C.accent} onBlur={e => e.target.style.borderColor = C.border} />
          <div style={{ display: 'flex', gap: 4 }}>
            {[
              { icon: '💬', title: 'Toggle Chat History', active: showChat, action: () => setShowChat(!showChat) },
            ].map((b, i) => (
              <button key={i} title={b.title} onClick={b.action || (() => {})}
                style={{ width: 34, height: 34, borderRadius: '50%', background: b.active ? C.accent : '#111114', border: `1px solid ${b.active ? C.accent : C.border}`, color: b.active ? '#000' : C.muted, cursor: 'pointer', fontSize: 14, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {b.icon}
              </button>
            ))}
          </div>
          <button onClick={() => handleSend(inputText)} disabled={loading || !inputText.trim()}
            style={{ padding: '8px 20px', background: loading ? '#333' : C.accent, border: 'none', color: loading ? '#555' : '#000', fontWeight: 700, fontSize: 12, borderRadius: 5, cursor: 'pointer', opacity: (loading || !inputText.trim()) ? 0.5 : 1, boxShadow: !loading ? `0 0 10px rgba(0,197,184,0.4)` : 'none', transition: 'all 0.15s', flexShrink: 0 }}>
            {loading ? '⏳ Processing' : '▶ Generate'}
          </button>
          <div style={{ flexShrink: 0 }}>
            <PipelineStatus activeNode={activeNode} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Prompt Preview Component ──
function PromptPreview({ text }) {
  // Simple keyword detection for preview (doesn't change actual parsing)
  const keywords = {
    shapes: ['box', 'cube', 'cylinder', 'sphere', 'cone', 'gear', 'torus', 'pipe', 'room'],
    actions: ['create', 'make', 'generate', 'build', 'rotate', 'scale', 'move', 'delete'],
    materials: ['steel', 'aluminum', 'plastic', 'cast_iron', 'iron', 'copper', 'brass'],
    dimensions: text.match(/\d+(\.\d+)?/g) || [],
  };
  
  const lower = text.toLowerCase();
  const detectedShape = keywords.shapes.find(s => lower.includes(s));
  const detectedAction = keywords.actions.find(a => lower.includes(a));
  const detectedMaterial = keywords.materials.find(m => lower.includes(m));
  const dimensions = keywords.dimensions.slice(0, 3);
  
  if (!detectedAction && !detectedShape) {
    return <span style={{ fontSize: 10, color: C.muted, fontStyle: 'italic' }}>Type a shape command...</span>;
  }
  
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 10 }}>
      {detectedAction && (
        <span style={{ padding: '2px 8px', borderRadius: 10, background: 'rgba(0,197,184,0.15)', color: C.accent, fontWeight: 600 }}>
          {detectedAction.toUpperCase()}
        </span>
      )}
      {detectedShape && (
        <span style={{ padding: '2px 8px', borderRadius: 10, background: 'rgba(94,170,255,0.15)', color: '#5eaaff', fontWeight: 600 }}>
          {detectedShape.toUpperCase()}
        </span>
      )}
      {dimensions.length > 0 && (
        <span style={{ color: '#ffa23b' }}>
          📐 {dimensions.join(' × ')} mm
        </span>
      )}
      {detectedMaterial && (
        <span style={{ padding: '2px 8px', borderRadius: 10, background: 'rgba(255,162,59,0.15)', color: '#ffa23b', fontWeight: 600 }}>
          {detectedMaterial.toUpperCase()}
        </span>
      )}
    </div>
  );
}

function ContextChip({ children }) {
  return (
    <div style={{ padding: '4px 12px', borderRadius: 16, background: 'rgba(26,26,30,0.82)', backdropFilter: 'blur(8px)', border: '1px solid rgba(0,197,184,0.3)', fontSize: 10.5, color: '#a0f0e8', fontWeight: 600 }}>
      {children}
    </div>
  );
}
