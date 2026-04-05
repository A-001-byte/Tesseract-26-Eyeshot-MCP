import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchBom } from '../services/api';

const C = {
  bg: '#1c1c1e',
  row: '#252528',
  rowAlt: '#222225',
  panel: '#2a2a2d',
  border: '#3a3a3d',
  accent: '#00c5b8',
  text: '#d4d4d8',
  muted: '#71717a',
  hover: '#303033',
  error: '#fca5a5',
  success: '#4ade80',
};

const COLS = [
  { key: 'item', label: '#', w: 36, align: 'center' },
  { key: 'name', label: 'Part Name', w: 180, align: 'left' },
  { key: 'part_type', label: 'Type', w: 100, align: 'left' },
  { key: 'material', label: 'Material', w: 92, align: 'left' },
  { key: 'volume_m3', label: 'Vol (m3)', w: 86, align: 'right', fmt: (v) => Number(v || 0).toFixed(5) },
  { key: 'surface_area_m2', label: 'Area (m2)', w: 86, align: 'right', fmt: (v) => Number(v || 0).toFixed(3) },
  { key: 'mass_kg', label: 'Mass (kg)', w: 86, align: 'right', fmt: (v) => Number(v || 0).toFixed(3) },
  { key: 'size_x_mm', label: 'X (mm)', w: 72, align: 'right', fmt: (v) => Number(v || 0).toFixed(1) },
  { key: 'size_y_mm', label: 'Y (mm)', w: 72, align: 'right', fmt: (v) => Number(v || 0).toFixed(1) },
  { key: 'size_z_mm', label: 'Z (mm)', w: 72, align: 'right', fmt: (v) => Number(v || 0).toFixed(1) },
  { key: 'num_teeth', label: 'Teeth', w: 58, align: 'center', fmt: (v) => (v == null ? '-' : v) },
  { key: 'pitch_diameter_mm', label: 'Pitch D', w: 72, align: 'right', fmt: (v) => (v == null ? '-' : Number(v).toFixed(1)) },
  { key: 'qty', label: 'Qty', w: 42, align: 'center', fmt: (v) => Math.max(1, Number(v || 1)) },
];

const toCsvCell = (val) => {
  const text = String(val ?? '');
  return `"${text.replaceAll('"', '""')}"`;
};

const buildCsv = (rows, totals) => {
  const headers = COLS.map((c) => c.label).join(',');
  const body = rows.map((row) => COLS.map((c) => toCsvCell(c.fmt ? c.fmt(row[c.key]) : (row[c.key] ?? ''))).join(','));
  const footer = COLS.map((c) => {
    if (c.key === 'name') return toCsvCell('TOTAL');
    if (c.key === 'mass_kg') return toCsvCell(totals.mass.toFixed(3));
    if (c.key === 'volume_m3') return toCsvCell(totals.volume.toFixed(5));
    if (c.key === 'qty') return toCsvCell(totals.qty);
    return toCsvCell('');
  }).join(',');
  return [headers, ...body, footer].join('\n');
};

const exportCsv = (rows, totals) => {
  const blob = new Blob([buildCsv(rows, totals)], { type: 'text/csv' });
  const href = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = href;
  a.download = `bom_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(href);
};

export default function BomPanel({ refreshToken }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadedOnce, setLoadedOnce] = useState(false);
  const [sortKey, setSortKey] = useState('item');
  const [sortDir, setSortDir] = useState(1);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const payload = await fetchBom();
      setRows(Array.isArray(payload.bom) ? payload.bom : []);
      setLoadedOnce(true);
    } catch (e) {
      setRows([]);
      setError(e?.message || 'Failed to load BOM');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, refreshToken]);

  const sortedRows = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a?.[sortKey] ?? '';
      const bv = b?.[sortKey] ?? '';
      if (typeof av === 'number' || typeof bv === 'number') {
        return (Number(av || 0) - Number(bv || 0)) * sortDir;
      }
      return String(av).localeCompare(String(bv)) * sortDir;
    });
    return copy;
  }, [rows, sortDir, sortKey]);

  const totals = useMemo(() => rows.reduce((acc, row) => ({
    mass: acc.mass + Number(row?.mass_kg || 0),
    volume: acc.volume + Number(row?.volume_m3 || 0),
    qty: acc.qty + Math.max(1, Number(row?.qty || 1)),
  }), { mass: 0, volume: 0, qty: 0 }), [rows]);

  const onSort = (key) => {
    if (key === sortKey) {
      setSortDir((d) => d * -1);
      return;
    }
    setSortKey(key);
    setSortDir(1);
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: C.bg, color: C.text }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', borderBottom: `1px solid ${C.border}`, background: C.panel }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 13 }}>Bill of Materials</div>
          <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>
            {loadedOnce
              ? `${rows.length} part${rows.length === 1 ? '' : 's'} · ${totals.mass.toFixed(2)} kg total`
              : 'Loading scene BOM'}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => exportCsv(sortedRows, totals)}
            disabled={rows.length === 0}
            style={{
              padding: '6px 10px',
              borderRadius: 4,
              border: `1px solid ${C.border}`,
              background: 'transparent',
              color: rows.length === 0 ? C.muted : C.text,
              cursor: rows.length === 0 ? 'not-allowed' : 'pointer',
              fontSize: 11,
            }}
          >
            Export CSV
          </button>
          <button
            onClick={refresh}
            disabled={loading}
            style={{
              padding: '6px 12px',
              borderRadius: 4,
              border: 'none',
              background: loading ? '#333' : C.accent,
              color: loading ? '#666' : '#000',
              fontWeight: 700,
              fontSize: 11,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Loading...' : 'Refresh BOM'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ margin: 12, padding: '8px 10px', border: '1px solid rgba(252,165,165,0.35)', borderRadius: 4, color: C.error, fontSize: 11 }}>
          {error}
        </div>
      )}

      {!loading && rows.length === 0 && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: C.muted, fontSize: 12 }}>
          No parts in the scene.
        </div>
      )}

      {rows.length > 0 && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed', minWidth: COLS.reduce((s, c) => s + c.w, 0) }}>
            <colgroup>
              {COLS.map((col) => <col key={col.key} style={{ width: col.w }} />)}
            </colgroup>
            <thead>
              <tr style={{ position: 'sticky', top: 0, background: C.panel, zIndex: 1 }}>
                {COLS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => onSort(col.key)}
                    style={{
                      padding: '8px 6px',
                      borderBottom: `1px solid ${C.border}`,
                      textAlign: col.align,
                      fontSize: 10,
                      letterSpacing: 0.5,
                      textTransform: 'uppercase',
                      color: sortKey === col.key ? C.accent : C.muted,
                      cursor: 'pointer',
                      userSelect: 'none',
                    }}
                  >
                    {col.label}{sortKey === col.key ? (sortDir === 1 ? ' ▲' : ' ▼') : ''}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row, idx) => (
                <tr
                  key={row.id || `${row.name}-${idx}`}
                  style={{ background: idx % 2 === 0 ? C.row : C.rowAlt }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = C.hover; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = idx % 2 === 0 ? C.row : C.rowAlt; }}
                >
                  {COLS.map((col) => {
                    const raw = row[col.key];
                    const val = col.fmt ? col.fmt(raw) : (raw ?? '-');
                    const isMass = col.key === 'mass_kg';
                    return (
                      <td key={col.key} style={{ padding: '7px 6px', textAlign: col.align, fontSize: 11, color: isMass ? C.success : C.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={String(val)}>
                        {val}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr style={{ background: C.panel, borderTop: `1px solid ${C.border}` }}>
                {COLS.map((col) => {
                  if (col.key === 'name') return <td key={col.key} style={{ padding: '8px 6px', color: C.muted, fontWeight: 700, fontSize: 10 }}>TOTAL</td>;
                  if (col.key === 'mass_kg') return <td key={col.key} style={{ padding: '8px 6px', textAlign: 'right', color: C.success, fontWeight: 700 }}>{totals.mass.toFixed(3)}</td>;
                  if (col.key === 'volume_m3') return <td key={col.key} style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 700 }}>{totals.volume.toFixed(5)}</td>;
                  if (col.key === 'qty') return <td key={col.key} style={{ padding: '8px 6px', textAlign: 'center', fontWeight: 700 }}>{totals.qty}</td>;
                  return <td key={col.key} />;
                })}
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}
