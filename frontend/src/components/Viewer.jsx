import React, { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

// Cache the OCCT WASM instance
let _occtInstance = null;
let _occtLoading = null;

const loadOCCT = () => {
  if (_occtInstance) return Promise.resolve(_occtInstance);
  if (_occtLoading) return _occtLoading;
  _occtLoading = new Promise((resolve, reject) => {
    if (window.occtimportjs) {
      window.occtimportjs().then(occt => { _occtInstance = occt; resolve(occt); }).catch(reject);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/occt-import-js@0.0.23/dist/occt-import-js.min.js';
    script.onload = async () => {
      try { const occt = await window.occtimportjs(); _occtInstance = occt; resolve(occt); }
      catch (err) { _occtLoading = null; reject(err); }
    };
    script.onerror = (err) => { _occtLoading = null; reject(err); };
    document.head.appendChild(script);
  });
  return _occtLoading;
};

const base64ToUint8Array = (base64) => {
  const bin = window.atob(base64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
};

const PART_COLORS = [
  '#5eaaff', '#ff7b7b', '#61df76', '#ffe04b', '#dc6df8',
  '#30d9a7', '#ffa23b', '#849ffc', '#ff75a5', '#48e9b9',
];

// ── Build XYZ axes with colored lines + labels ──
function createAxesGizmo() {
  const group = new THREE.Group();
  group.name = 'axes_gizmo';

  const defs = [
    { dir: new THREE.Vector3(1, 0, 0), up: new THREE.Vector3(0, 0, 1), color: 0xff4444, label: 'X' },
    { dir: new THREE.Vector3(0, 1, 0), up: new THREE.Vector3(0, 1, 0), color: 0x44ff44, label: 'Y' },
    { dir: new THREE.Vector3(0, 0, 1), up: new THREE.Vector3(1, 0, 0), color: 0x4488ff, label: 'Z' },
  ];

  defs.forEach(({ dir, color, label }) => {
    // Line from origin
    const pts = [new THREE.Vector3(0, 0, 0), dir.clone()];
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    group.add(new THREE.Line(geo, new THREE.LineBasicMaterial({ color, linewidth: 2, depthTest: false })));

    // Arrow cone — default ConeGeometry points along +Y, so rotate to point along `dir`
    const coneGeo = new THREE.ConeGeometry(0.03, 0.1, 12);
    const cone = new THREE.Mesh(coneGeo, new THREE.MeshBasicMaterial({ color, depthTest: false }));
    cone.position.copy(dir.clone());
    // Rotate from default +Y to target direction
    const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
    cone.setRotationFromQuaternion(quat);
    group.add(cone);

    // Label sprite
    const canvas = document.createElement('canvas');
    canvas.width = 64; canvas.height = 64;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#' + color.toString(16).padStart(6, '0');
    ctx.font = 'bold 48px Inter, Arial, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(label, 32, 32);
    const tex = new THREE.CanvasTexture(canvas);
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: false }));
    sprite.position.copy(dir.clone().multiplyScalar(1.18));
    sprite.scale.set(0.12, 0.12, 1);
    group.add(sprite);
  });

  return group;
}

export default function Viewer({ cadData }) {
  const mountRef = useRef(null);
  const [loadingStep, setLoadingStep] = useState(false);
  const [ghostMode, setGhostMode] = useState(false);
  const [wireframe, setWireframe] = useState(false);
  const controlsRef = useRef(null);
  const cameraRef = useRef(null);
  const sceneRef = useRef(null);

  useEffect(() => {
    if (!cadData || !mountRef.current) return;

    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // ── Scene ──
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#0a0a18');
    sceneRef.current = scene;

    // ── Camera ──
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 50000);
    camera.position.set(300, 250, 300);
    cameraRef.current = camera;

    // ── Renderer ──
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.4;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);

    // ── Lighting (5-point for maximum visibility) ──
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));

    const key = new THREE.DirectionalLight(0xffffff, 1.4);
    key.position.set(300, 600, 300);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    scene.add(key);

    const fill = new THREE.DirectionalLight(0xaabbff, 0.6);
    fill.position.set(-300, 300, -200);
    scene.add(fill);

    const back = new THREE.DirectionalLight(0xffffff, 0.3);
    back.position.set(0, 200, -400);
    scene.add(back);

    const hemi = new THREE.HemisphereLight(0x88bbff, 0x334455, 0.4);
    scene.add(hemi);

    // ── Ground grid ──
    const gridHelper = new THREE.GridHelper(2000, 100, 0x1a1a3e, 0x111128);
    gridHelper.position.y = -0.1;
    scene.add(gridHelper);

    // ── XYZ Axes (unit size, scaled in fitCamera) ──
    const axesGizmo = createAxesGizmo();
    axesGizmo.renderOrder = 999; // always on top
    scene.add(axesGizmo);

    // ── Controls ──
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.autoRotate = false;
    controls.minDistance = 1;
    controls.maxDistance = 10000;
    controlsRef.current = controls;

    // ── Animation loop ──
    let animationId;
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // ── Resize ──
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // ── Fit camera ──
    const fitCameraToObject = (object3d) => {
      const box = new THREE.Box3().setFromObject(object3d);
      const center = box.getCenter(new THREE.Vector3());
      const sphere = box.getBoundingSphere(new THREE.Sphere());
      const r = sphere.radius || 100;

      const dir = new THREE.Vector3(1, 0.7, 1).normalize();
      camera.position.copy(center).addScaledVector(dir, r * 2.5);
      camera.lookAt(center);
      controls.target.copy(center);
      gridHelper.position.y = box.min.y - 0.2;

      // Axes at world origin, scaled proportional to model
      const axisLen = Math.max(r * 0.35, 5);
      axesGizmo.scale.setScalar(axisLen);
      axesGizmo.position.set(0, box.min.y, 0);

      controls.update();
    };

    // ── Fallback ──
    const loadPrimitiveFallback = () => {
      console.log('[Viewer] Using primitive fallback for:', cadData.name);
      const [xmin, ymin, zmin, xmax, ymax, zmax] = cadData.bounding_box || [0, 0, 0, 100, 100, 100];
      const sx = xmax - xmin, sy = ymax - ymin, sz = zmax - zmin;
      const n = (cadData.name || '').toLowerCase();
      let geometry;
      if (n.includes('shaft') || n.includes('pipe')) geometry = new THREE.CylinderGeometry(sx / 2, sx / 2, sz, 32);
      else if (n.includes('bearing') || n.includes('torus')) geometry = new THREE.TorusGeometry(sx / 2, sy / 4, 16, 64);
      else if (n.includes('sphere') || n.includes('ball')) geometry = new THREE.SphereGeometry(sx / 2, 32, 32);
      else if (n.includes('cone') || n.includes('nozzle')) geometry = new THREE.ConeGeometry(sx / 2, sz, 32);
      else if (n.includes('cylinder') || n.includes('gear') || n.includes('disc')) geometry = new THREE.CylinderGeometry(sx / 2, sx / 2, sz, 32);
      else geometry = new THREE.BoxGeometry(sx, sy, sz);

      const material = new THREE.MeshPhysicalMaterial({
        color: '#5eaaff', metalness: 0.2, roughness: 0.4, clearcoat: 0.3,
        transparent: ghostMode, opacity: ghostMode ? 0.35 : 1.0,
        wireframe: wireframe, side: THREE.DoubleSide,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.castShadow = true;
      scene.add(mesh);
      fitCameraToObject(mesh);
    };

    // ── Process GLB ──
    const processGLB = async () => {
      console.log('[Viewer] Loading GLB, size:', cadData.glb_b64?.length || 0);
      try {
        const binaryString = atob(cadData.glb_b64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const buffer = bytes.buffer;

        // Check GLB magic number
        const magic = new Uint32Array(buffer, 0, 1)[0];
        console.log('[Viewer] GLB magic number:', magic.toString(16), 'expected: 46546c67');

        if (magic !== 0x46546C67) {
          console.error('[Viewer] Invalid GLB magic number, using fallback');
          loadPrimitiveFallback();
          return;
        }

        const loader = new GLTFLoader();
        loader.parse(
          buffer,
          '',
          (gltf) => {
            console.log('[Viewer] GLB parsed successfully:', gltf);
            const model = gltf.scene;

            model.traverse((child) => {
              if (child.isMesh) {
                console.log('[Viewer] Mesh found:', child.geometry.attributes.position?.count, 'vertices');
                child.material = new THREE.MeshPhysicalMaterial({
                  color: '#5eaaff',
                  metalness: 0.2,
                  roughness: 0.4,
                  clearcoat: 0.3,
                  side: THREE.DoubleSide,
                  transparent: ghostMode,
                  opacity: ghostMode ? 0.4 : 1.0,
                  wireframe: wireframe,
                });
                child.castShadow = true;
                child.receiveShadow = true;
              }
            });

            const box = new THREE.Box3().setFromObject(model);
            const size = box.getSize(new THREE.Vector3());
            const center = box.getCenter(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);

            if (maxDim === 0) {
              console.error('[Viewer] Model has zero size, using fallback');
              loadPrimitiveFallback();
              return;
            }

            scene.add(model);
            fitCameraToObject(model);
            console.log('[Viewer] GLB model added to scene successfully');
          },
          (error) => {
            console.error('[Viewer] GLTFLoader.parse error:', error);
            loadPrimitiveFallback();
          }
        );
      } catch (err) {
        console.error('[Viewer] GLB processing error:', err);
        loadPrimitiveFallback();
      }
    };

    // ── Process STEP ──
    const processSTEP = async () => {
      if (!cadData.step_b64) { loadPrimitiveFallback(); return; }
      setLoadingStep(true);
      try {
        const occt = await loadOCCT();
        const fileBuffer = base64ToUint8Array(cadData.step_b64);
        const result = occt.ReadStepFile(fileBuffer, null);
        if (!result?.meshes?.length) throw new Error('No meshes from STEP');

        const rootGroup = new THREE.Group();
        let count = 0;

        result.meshes.forEach((m, i) => {
          const posArr = m.attributes?.position?.array;
          if (!posArr?.length) return;

          const geometry = new THREE.BufferGeometry();
          geometry.setAttribute('position', new THREE.BufferAttribute(
            posArr instanceof Float32Array ? posArr : new Float32Array(posArr), 3
          ));
          if (m.index?.array) {
            const idx = m.index.array instanceof Uint32Array ? m.index.array :
                        m.index.array instanceof Uint16Array ? m.index.array :
                        new Uint32Array(m.index.array);
            geometry.setIndex(new THREE.BufferAttribute(idx, 1));
          }
          geometry.computeVertexNormals();

          const color = PART_COLORS[i % PART_COLORS.length];
          const mat = new THREE.MeshPhysicalMaterial({
            color, metalness: 0.1, roughness: 0.45, clearcoat: 0.15,
            side: THREE.DoubleSide,
            transparent: ghostMode, opacity: ghostMode ? 0.4 : 1.0,
            depthWrite: !ghostMode, wireframe: wireframe,
          });

          const mesh = new THREE.Mesh(geometry, mat);
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          rootGroup.add(mesh);
          count++;

          // Edges
          const edgeGeo = new THREE.EdgesGeometry(geometry, 15);
          rootGroup.add(new THREE.LineSegments(edgeGeo, new THREE.LineBasicMaterial({
            color: 0xffffff, transparent: true, opacity: ghostMode ? 0.5 : 0.2,
          })));
        });

        if (count === 0) throw new Error('All meshes empty');
        scene.add(rootGroup);
        fitCameraToObject(rootGroup);
      } catch (err) {
        console.error('[Viewer] STEP processing error:', err);
        loadPrimitiveFallback();
      } finally {
        setLoadingStep(false);
      }
    };

    // Decide which loader to use
    const loadGeometry = async () => {
      console.log('[Viewer] Loading geometry for:', cadData.name);
      console.log('[Viewer] Has glb_b64:', !!cadData.glb_b64, 'Has step_b64:', !!cadData.step_b64);
      
      if (cadData.glb_b64) {
        await processGLB();
      } else if (cadData.step_b64) {
        await processSTEP();
      } else {
        console.log('[Viewer] No glb_b64 or step_b64, using fallback');
        loadPrimitiveFallback();
      }
    };

    loadGeometry();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
      if (container && renderer.domElement) container.removeChild(renderer.domElement);
      renderer.dispose(); controls.dispose();
    };
  }, [cadData, ghostMode, wireframe]);

  // ── Empty state ──
  if (!cadData) {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0a0a18', flexDirection: 'column', gap: '16px' }}>
        <div style={{ fontSize: '56px', opacity: 0.15 }}>◇</div>
        <div style={{ color: '#555', fontSize: '14px', fontWeight: 500, letterSpacing: '0.5px' }}>Type a prompt below to generate 3D geometry</div>
        <div style={{ color: '#333', fontSize: '11px' }}>Try: "create a room" or "make a gear"</div>
      </div>
    );
  }

  const modelName = cadData.name || 'model';
  const bb = cadData.bounding_box || [0, 0, 0, 0, 0, 0];
  const dims = [bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]].map(v => v.toFixed(1));

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <div ref={mountRef} style={{ width: '100%', height: '100%' }} />

      {/* ── HUD top-left ── */}
      <div style={{
        position: 'absolute', top: 12, left: 12,
        background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(16px)',
        color: 'white', padding: '12px 16px', borderRadius: '10px',
        fontSize: '11px', zIndex: 11, border: '1px solid rgba(255,255,255,0.06)',
        minWidth: '160px',
      }}>
        <div style={{ fontWeight: 800, color: '#5eaaff', fontSize: '13px', marginBottom: 6, letterSpacing: '0.8px' }}>
          {modelName.replace(/_/g, ' ').toUpperCase()}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '72px 1fr', gap: '3px 8px', lineHeight: '1.7' }}>
          <span style={{ color: '#666' }}>Volume</span><span>{Number(cadData.volume_m3 || 0).toFixed(1)} m³</span>
          <span style={{ color: '#666' }}>Surface</span><span>{Number(cadData.surface_area_m2 || 0).toFixed(1)} m²</span>
          <span style={{ color: '#666' }}>Size</span><span>{dims[0]}×{dims[1]}×{dims[2]}</span>
          <span style={{ color: '#666' }}>Mass</span><span style={{ color: '#61df76', fontWeight: 600 }}>{Number(cadData.mass_kg || 0).toFixed(1)} kg</span>
          <span style={{ color: '#666' }}>Material</span><span style={{ color: '#ffa23b', textTransform: 'capitalize' }}>{cadData.material || 'steel'}</span>
        </div>
      </div>

      {/* ── XYZ legend top-right ── */}
      <div style={{
        position: 'absolute', top: 12, right: 12,
        background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(12px)',
        padding: '8px 14px', borderRadius: '8px', zIndex: 11,
        display: 'flex', gap: '14px', fontSize: '11px', fontWeight: 700,
        border: '1px solid rgba(255,255,255,0.05)',
      }}>
        <span style={{ color: '#ff4444' }}>X</span>
        <span style={{ color: '#44ff44' }}>Y</span>
        <span style={{ color: '#4488ff' }}>Z</span>
      </div>

      {/* ── Bottom toolbar ── */}
      <div style={{
        position: 'absolute', bottom: 16, left: '50%', transform: 'translateX(-50%)',
        display: 'flex', gap: '6px', zIndex: 15,
        background: 'rgba(0,0,0,0.55)', padding: '6px 12px', borderRadius: '32px',
        backdropFilter: 'blur(16px)', border: '1px solid rgba(255,255,255,0.08)',
      }}>
        {/* Ghost toggle */}
        <ToolbarBtn active={ghostMode} onClick={() => setGhostMode(!ghostMode)} icon="👻" label={ghostMode ? 'Solid' : 'X-Ray'} />
        <ToolbarDivider />
        {/* Wireframe toggle */}
        <ToolbarBtn active={wireframe} onClick={() => setWireframe(!wireframe)} icon="◇" label={wireframe ? 'Filled' : 'Wire'} />
        <ToolbarDivider />
        {/* Reset / Jump inside */}
        <ToolbarBtn onClick={() => {
          if (controlsRef.current && cameraRef.current) {
            if (modelName.includes('room')) {
              cameraRef.current.position.set(0, 150, 0);
              controlsRef.current.target.set(100, 150, 100);
            } else {
              // Reset ghost + wireframe to force re-render with fitCamera
              setGhostMode(false); setWireframe(false);
            }
          }
        }} icon="⟳" label={modelName.includes('room') ? 'Inside' : 'Reset'} />
      </div>

      {/* ── Loading overlay ── */}
      {loadingStep && (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(10, 10, 24, 0.88)', color: 'white', zIndex: 100,
          flexDirection: 'column', gap: '16px',
        }}>
          <div style={{ width: 44, height: 44, border: '3px solid #5eaaff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.9s linear infinite' }} />
          <div style={{ fontSize: '13px', letterSpacing: '2px', fontWeight: 400, color: '#aaa' }}>BUILDING GEOMETRY...</div>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}
    </div>
  );
}

// ── Toolbar button component ──
function ToolbarBtn({ active, onClick, icon, label }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: active ? '#5eaaff' : hovered ? 'rgba(255,255,255,0.08)' : 'transparent',
        color: active ? '#000' : '#bbb',
        border: 'none', padding: '6px 14px', borderRadius: '20px',
        fontSize: '11px', fontWeight: 600, cursor: 'pointer',
        transition: 'all 0.15s', display: 'flex', alignItems: 'center', gap: '5px',
        whiteSpace: 'nowrap',
      }}
    >
      <span style={{ fontSize: '13px' }}>{icon}</span> {label}
    </button>
  );
}

function ToolbarDivider() {
  return <div style={{ width: 1, background: 'rgba(255,255,255,0.08)', margin: '4px 0' }} />;
}
