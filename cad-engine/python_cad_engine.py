import os
import uuid
import base64
import tempfile
import math
import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCone, BRepPrimAPI_MakeSphere
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Ax1, gp_Pnt, gp_Dir
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound, topods
from OCC.Core.BRepFill import BRepFill_CurveConstraint

app = Flask(__name__)
CORS(app)

scene_objects = {}
scene_meta = {}   # stores rich metadata per object key: {name, material, part_type, density_kg_m3, mass_kg, ...}
last_object_id = None


def json_safe_value(v):
    """Make values JSON-serializable (numpy / OCCT wrappers break Flask jsonify)."""
    if v is None:
        return None
    if isinstance(v, dict):
        return {k: json_safe_value(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [json_safe_value(x) for x in v]
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v
    if isinstance(v, int) and not isinstance(v, bool):
        try:
            return int(v)
        except (TypeError, ValueError, OverflowError):
            pass
    if isinstance(v, float):
        x = float(v)
        return 0.0 if (math.isnan(x) or math.isinf(x)) else x
    try:
        import numpy as np
        if isinstance(v, np.generic):
            return json_safe_value(v.item())
    except ImportError:
        pass
    try:
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            return 0.0
        return x
    except (TypeError, ValueError):
        return str(v)


def json_safe_dict(d):
    return {k: json_safe_value(v) for k, v in d.items()}


def safe_json_response(payload, status=200):
    """Return JSON without relying on Flask's serializer edge cases."""
    body = json.dumps(json_safe_value(payload), ensure_ascii=False)
    return Response(body, status=status, mimetype='application/json')


def safe_float(v, default=0.0):
    """Parse a scalar for math/JSON; never raises."""
    try:
        if v is None:
            return float(default)
        if isinstance(v, bool):
            return float(default)
        x = json_safe_value(v)
        if x is None:
            return float(default)
        if isinstance(x, str) and not x.strip():
            return float(default)
        return float(x)
    except (TypeError, ValueError, OverflowError):
        return float(default)


def bbox_sizes_mm(bb):
    """Bounding-box extents in mm (scene uses cm); safe if bb is malformed."""
    if not bb or len(bb) != 6:
        return 0.0, 0.0, 0.0
    try:
        nums = [safe_float(x, 0.0) for x in bb]
        return (
            round(abs(nums[3] - nums[0]) * 10, 2),
            round(abs(nums[4] - nums[1]) * 10, 2),
            round(abs(nums[5] - nums[2]) * 10, 2),
        )
    except Exception:
        return 0.0, 0.0, 0.0


def entity_list_payload(obj_id, props, meta):
    """Stable, JSON-safe entity row (do not merge arbitrary meta keys)."""
    bb = props.get('bounding_box')
    if not (isinstance(bb, (list, tuple)) and len(bb) == 6):
        bb = [0, 0, 0, 0, 0, 0]
    sx, sy, sz = bbox_sizes_mm(bb)
    vol = safe_float(props.get('volume_m3'), 0.0)
    area = safe_float(props.get('surface_area_m2'), 0.0)
    density = safe_float(meta.get('density_kg_m3', 7850), 7850.0)
    computed_mass = round(vol * density, 4)
    rm_raw = meta.get('mass_kg')
    if rm_raw is None:
        mass_kg = computed_mass
    else:
        rm = json_safe_value(rm_raw)
        if rm is None or rm == 0 or rm == 0.0:
            mass_kg = computed_mass
        else:
            mass_kg = round(safe_float(rm, computed_mass), 4)

    row = {
        'id': str(obj_id),
        'name': str(meta.get('name', obj_id)),
        'part_type': str(meta.get('part_type', 'Shape')),
        'material': str(meta.get('material', 'steel')),
        'density_kg_m3': density,
        'mass_kg': mass_kg,
        'volume_m3': round(vol, 6),
        'surface_area_m2': round(area, 6),
        'bounding_box': [safe_float(x, 0.0) for x in bb],
        'size_x_mm': sx,
        'size_y_mm': sy,
        'size_z_mm': sz,
        'num_teeth': meta.get('num_teeth'),
        'module': meta.get('module'),
        'pitch_diameter_mm': meta.get('pitch_diameter_mm'),
        'thickness_mm': meta.get('thickness_mm'),
        'outer_diameter_mm': meta.get('outer_diameter_mm'),
    }
    return json_safe_dict(row)


def get_real_obj_id(obj_id):
    global last_object_id
    if obj_id == "last" or not obj_id:
        return last_object_id
    return obj_id

def get_shape_metrics_light(shape):
    """Volume, surface area, bbox only — no STEP/GLB (fast for BOM / entity list)."""
    try:
        from OCC.Core.GProp import GProp_GProps

        props = GProp_GProps()
        try:
            from OCC.Core.BRepGProp import brepgprop
            brepgprop.VolumeProperties(shape, props)
        except Exception:
            try:
                from OCC.Core.BRepGProp import brepgprop_VolumeProperties
                brepgprop_VolumeProperties(shape, props)
            except Exception:
                pass
        try:
            volume_raw = float(props.Mass())
        except Exception:
            volume_raw = 0.0
        volume_m3 = volume_raw / 1_000_000.0 if volume_raw > 0 else 0

        props_s = GProp_GProps()
        try:
            from OCC.Core.BRepGProp import brepgprop
            brepgprop.SurfaceProperties(shape, props_s)
        except Exception:
            try:
                from OCC.Core.BRepGProp import brepgprop_SurfaceProperties
                brepgprop_SurfaceProperties(shape, props_s)
            except Exception:
                pass
        try:
            surface_area_raw = float(props_s.Mass())
        except Exception:
            surface_area_raw = 0.0
        surface_area_m2 = surface_area_raw / 10_000.0 if surface_area_raw > 0 else 0

        from OCC.Core.Bnd import Bnd_Box
        bbox = Bnd_Box()
        try:
            from OCC.Core.BRepBndLib import brepbndlib
            brepbndlib.Add(shape, bbox, True)
        except Exception:
            try:
                from OCC.Core.BRepBndLib import brepbndlib_Add
                brepbndlib_Add(shape, bbox, True)
            except Exception:
                pass

        if bbox.IsVoid():
            min_x, min_y, min_z, max_x, max_y, max_z = 0., 0., 0., 0., 0., 0.
        else:
            min_x, min_y, min_z, max_x, max_y, max_z = bbox.Get()
            min_x, min_y, min_z = float(min_x), float(min_y), float(min_z)
            max_x, max_y, max_z = float(max_x), float(max_y), float(max_z)

        return {
            "volume_m3": round(volume_m3, 6),
            "surface_area_m2": round(surface_area_m2, 6),
            "bounding_box": [
                round(min_x, 4), round(min_y, 4), round(min_z, 4),
                round(max_x, 4), round(max_y, 4), round(max_z, 4),
            ],
        }
    except Exception as exc:
        print(f"[get_shape_metrics_light] {exc}")
        return {'volume_m3': 0, 'surface_area_m2': 0, 'bounding_box': [0, 0, 0, 1, 1, 1]}


def get_shape_properties(shape):
    from OCC.Core.GProp import GProp_GProps
    
    props = GProp_GProps()
    try:
        from OCC.Core.BRepGProp import brepgprop_VolumeProperties
        brepgprop_VolumeProperties(shape, props)
    except ImportError:
        from OCC.Core.BRepGProp import brepgprop
        brepgprop.VolumeProperties(shape, props)
    # OpenCASCADE defaults vary, we'll treat them as cm by default (since LLM sends cm)
    # 1 m3 = 1,000,000 cm3
    volume_raw = props.Mass()
    volume_m3 = volume_raw / 1_000_000.0 if volume_raw > 0 else 0
    
    props_s = GProp_GProps()
    try:
        from OCC.Core.BRepGProp import brepgprop_SurfaceProperties
        brepgprop_SurfaceProperties(shape, props_s)
    except ImportError:
        from OCC.Core.BRepGProp import brepgprop
        brepgprop.SurfaceProperties(shape, props_s)
    
    # 1 m2 = 10,000 cm2
    surface_area_raw = props_s.Mass()
    surface_area_m2 = surface_area_raw / 10_000.0 if surface_area_raw > 0 else 0
    
    from OCC.Core.Bnd import Bnd_Box
    bbox = Bnd_Box()
    try:
        from OCC.Core.BRepBndLib import brepbndlib_Add
        brepbndlib_Add(shape, bbox, True)
    except ImportError:
        from OCC.Core.BRepBndLib import brepbndlib
        brepbndlib.Add(shape, bbox, True)
        
    if bbox.IsVoid():
        min_x, min_y, min_z, max_x, max_y, max_z = 0., 0., 0., 0., 0., 0.
    else:
        min_x, min_y, min_z, max_x, max_y, max_z = bbox.Get()
        
    from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCC.Core.IFSelect import IFSelect_RetDone
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    fd, temp_path = tempfile.mkstemp(suffix='.step')
    os.close(fd)
    status = writer.Write(temp_path)
    
    step_base64 = ""
    if status == IFSelect_RetDone:
        with open(temp_path, "rb") as f:
            step_base64 = base64.b64encode(f.read()).decode('utf-8')
    os.remove(temp_path)
    
    # Generate GLB using trimesh
    glb_base64 = ""
    try:
        import trimesh
        import numpy as np
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
        from OCC.Extend.TopologyUtils import TopologyExplorer
        
        # Mesh the shape
        BRepMesh_IncrementalMesh(shape, 0.1, False, 0.5, True)
        
        vertices = []
        faces = []
        vertex_offset = 0
        
        exp = TopologyExplorer(shape)
        for face in exp.faces():
            from OCC.Core.TopLoc import TopLoc_Location
            from OCC.Core.BRep import BRep_Tool
            
            loc = TopLoc_Location()
            triangulation = BRep_Tool.Triangulation(face, loc)
            
            if triangulation is not None:
                trsf = loc.Transformation()
                nb_nodes = triangulation.NbNodes()
                nb_triangles = triangulation.NbTriangles()
                
                for i in range(1, nb_nodes + 1):
                    node = triangulation.Node(i)
                    transformed = node.Transformed(trsf)
                    vertices.append([transformed.X(), transformed.Y(), transformed.Z()])
                
                from OCC.Core.TopAbs import TopAbs_REVERSED
                from OCC.Core.TopoDS import topods_Face
                f = topods_Face(face)
                reversed_face = (f.Orientation() == TopAbs_REVERSED)
                
                for i in range(1, nb_triangles + 1):
                    tri = triangulation.Triangle(i)
                    n1, n2, n3 = tri.Get()
                    if reversed_face:
                        n1, n2 = n2, n1
                    faces.append([vertex_offset + n1 - 1, vertex_offset + n2 - 1, vertex_offset + n3 - 1])
                
                vertex_offset += nb_nodes
        
        if vertices and faces:
            mesh = trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces))
            glb_bytes = mesh.export(file_type='glb')
            glb_base64 = base64.b64encode(glb_bytes).decode('utf-8')
    except Exception as e:
        print(f"[GLB Export] Warning: {e}")
    
    return {
        "volume_m3": round(volume_m3, 6),
        "surface_area_m2": round(surface_area_m2, 6),
        "bounding_box": [
            round(min_x, 4), round(min_y, 4), round(min_z, 4),
            round(max_x, 4), round(max_y, 4), round(max_z, 4)
        ],
        "bounding_box_dict": {
            "min": [round(min_x, 4), round(min_y, 4), round(min_z, 4)],
            "max": [round(max_x, 4), round(max_y, 4), round(max_z, 4)],
            "size": [round(max_x - min_x, 4), round(max_y - min_y, 4), round(max_z - min_z, 4)]
        },
        "step_b64": step_base64,
        "glb_b64": glb_base64
    }

def make_gear(num_teeth=24, module=2.0, thickness=8.0, bore_radius=8.0):
    pitch_radius = (num_teeth * module) / 2.0
    addendum = module
    dedendum = 1.25 * module
    outer_radius = pitch_radius + addendum
    root_radius = max(pitch_radius - dedendum, bore_radius + 2.0)
    tooth_width = (math.pi * module) / 2.2

    gear_body = BRepPrimAPI_MakeCylinder(outer_radius, thickness).Shape()

    root_cylinder = BRepPrimAPI_MakeCylinder(root_radius, thickness).Shape()
    ring = BRepAlgoAPI_Cut(gear_body, root_cylinder).Shape()

    bore = BRepPrimAPI_MakeCylinder(bore_radius, thickness).Shape()
    base_disc = BRepAlgoAPI_Cut(
        BRepPrimAPI_MakeCylinder(root_radius, thickness).Shape(), bore
    ).Shape()

    angle_step = (2.0 * math.pi) / num_teeth
    tooth_slot_width = (2.0 * math.pi * root_radius / num_teeth) * 0.45
    slot_depth = (outer_radius - root_radius) + 0.5

    slot_template = BRepPrimAPI_MakeBox(
        tooth_slot_width,
        slot_depth + outer_radius,
        thickness + 2.0
    ).Shape()

    trsf_init = gp_Trsf()
    trsf_init.SetTranslation(gp_Vec(
        -tooth_slot_width / 2.0,
        0.0,
        -1.0
    ))
    slot_template = BRepBuilderAPI_Transform(
        slot_template, trsf_init
    ).Shape()

    slots_combined = None
    for i in range(num_teeth):
        angle = i * angle_step + angle_step / 2.0
        trsf_rot = gp_Trsf()
        trsf_rot.SetRotation(
            gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
            angle
        )
        rotated_slot = BRepBuilderAPI_Transform(
            slot_template, trsf_rot
        ).Shape()
        if slots_combined is None:
            slots_combined = rotated_slot
        else:
            fuse = BRepAlgoAPI_Fuse(slots_combined, rotated_slot)
            if fuse.IsDone():
                slots_combined = fuse.Shape()

    if slots_combined is not None:
        cut = BRepAlgoAPI_Cut(ring, slots_combined)
        if cut.IsDone():
            teeth_ring = cut.Shape()
        else:
            teeth_ring = ring
    else:
        teeth_ring = ring

    fuse_final = BRepAlgoAPI_Fuse(base_disc, teeth_ring)
    if fuse_final.IsDone():
        final_gear = fuse_final.Shape()
    else:
        final_gear = base_disc

    return final_gear

def generate_shape(filename, dim_mods=None):
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCC.Core.gp import gp_Trsf, gp_Vec

    filename_lower = filename.lower()
    dim = dim_mods or {}
    
    if "bracket" in filename_lower:
        w = dim.get("width", 10.)
        h = dim.get("height", 10.)
        t = dim.get("thickness", 2.)
        box1 = BRepPrimAPI_MakeBox(w, h, t).Shape()
        box2 = BRepPrimAPI_MakeBox(t, h, w).Shape()
        return BRepAlgoAPI_Fuse(box1, box2).Shape()
    elif "shaft" in filename_lower:
        r = dim.get("radius", 2.)
        h = dim.get("height", 20.)
        return BRepPrimAPI_MakeCylinder(r, h).Shape()
    elif "housing" in filename_lower:
        w = dim.get("width", 10.)
        h = dim.get("height", 10.)
        outer = BRepPrimAPI_MakeBox(w, h, w).Shape()
        inner = BRepPrimAPI_MakeBox(w*0.8, h*0.8, w*0.8).Shape()
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(w*0.1, h*0.1, w*0.1))
        inner_trans = BRepBuilderAPI_Transform(inner, trsf).Shape()
        return BRepAlgoAPI_Cut(outer, inner_trans).Shape()
    elif "gear" in filename_lower:
        r = dim.get("radius", 5.)
        h = dim.get("height", 1.)
        return BRepPrimAPI_MakeCylinder(r, h).Shape()
    elif "bearing" in filename_lower:
        r = dim.get("radius", 5.)
        h = dim.get("height", 2.)
        t = dim.get("thickness", 2.)
        outer = BRepPrimAPI_MakeCylinder(r, h).Shape()
        inner = BRepPrimAPI_MakeCylinder(r - t, h).Shape()
        return BRepAlgoAPI_Cut(outer, inner).Shape()
    elif "cone" in filename_lower or "nozzle" in filename_lower:
        r = dim.get("radius", 5.)
        h = dim.get("height", 10.)
        return BRepPrimAPI_MakeCone(r, r*0.4, h).Shape()
    else:
        w = dim.get("width", 10.)
        return BRepPrimAPI_MakeBox(w, w, w).Shape()

@app.route('/health', methods=['GET'])
def health():
    return "pythonOCC 7.9.3 (OpenCASCADE)"

@app.route('/generate_gear', methods=['POST'])
def generate_gear():
    global last_object_id
    try:
        data = request.get_json() or {}
        num_teeth = int(data.get('num_teeth', 24))
        module = float(data.get('module', 2.0))
        thickness = float(data.get('thickness', 8.0))
        bore_radius = float(data.get('bore_radius', 8.0))
        material = data.get('material', 'steel')

        num_teeth = max(8, min(num_teeth, 60))
        module = max(0.5, min(module, 10.0))
        thickness = max(2.0, min(thickness, 50.0))

        shape = make_gear(
            num_teeth=num_teeth,
            module=module,
            thickness=thickness,
            bore_radius=bore_radius
        )

        props = get_shape_properties(shape)
        
        density_map = {
            'steel': 7850, 'aluminum': 2700,
            'plastic': 1200, 'cast_iron': 7200
        }
        density = density_map.get(material, 7850)
        mass_kg = round(props['volume_m3'] * density, 4)

        name = f'spur_gear_{num_teeth}t_m{module}'
        scene_objects[name] = shape
        last_object_id = name
        scene_meta[name] = {
            'name': name,
            'part_type': 'Spur Gear',
            'material': material,
            'density_kg_m3': density,
            'mass_kg': mass_kg,
            'num_teeth': num_teeth,
            'module': module,
            'pitch_diameter_mm': num_teeth * module,
            'outer_diameter_mm': (num_teeth + 2) * module,
            'thickness_mm': thickness,
            'bore_radius_mm': bore_radius,
        }

        return jsonify({
            'status': 'generated',
            'id': name,
            'name': name,
            'part_type': f'Spur Gear',
            'num_teeth': num_teeth,
            'module': module,
            'pitch_diameter_mm': num_teeth * module,
            'outer_diameter_mm': (num_teeth + 2) * module,
            'thickness_mm': thickness,
            'bore_radius_mm': bore_radius,
            'material': material,
            'density_kg_m3': density,
            'mass_kg': mass_kg,
            **props
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/load_model', methods=['POST'])
def load_model():
    global last_object_id
    data = request.get_json() or {}
    filename = data.get("file", "default.step")
    
    shape = generate_shape(filename)
    obj_id = os.path.splitext(filename)[0]
    scene_objects[obj_id] = shape
    last_object_id = obj_id
    
    props = get_shape_properties(shape)
    density = 7850
    scene_meta[obj_id] = {
        "name": obj_id,
        "part_type": "Loaded Model",
        "material": "steel",
        "density_kg_m3": density,
        "mass_kg": round(props.get("volume_m3", 0) * density, 4),
    }
    props["id"] = obj_id
    props["name"] = filename
    return jsonify(props)

@app.route('/load_and_count', methods=['POST'])
def load_and_count():
    data = request.get_json() or {}
    filename = data.get("file", "default.step")
    
    shape = generate_shape(filename)
    obj_id = os.path.splitext(filename)[0]
    scene_objects[obj_id] = shape
    
    props = get_shape_properties(shape)
    props["id"] = obj_id
    props["name"] = filename
    props["entity_count"] = len(scene_objects)
    return jsonify(props)

@app.route('/list_entities', methods=['GET'])
def list_entities():
    try:
        res = []
        # Iterate over a snapshot so concurrent scene updates do not break the loop.
        for obj_id, shape in list(scene_objects.items()):
            try:
                try:
                    props = get_shape_metrics_light(shape) if shape is not None else {
                        'volume_m3': 0,
                        'surface_area_m2': 0,
                        'bounding_box': [0, 0, 0, 0, 0, 0],
                    }
                except BaseException as e:
                    print(f"[list_entities] Error getting properties for {obj_id}: {e}")
                    props = {'volume_m3': 0, 'surface_area_m2': 0, 'bounding_box': [0,0,0,1,1,1]}

                meta = scene_meta.get(obj_id, {})
                if not isinstance(meta, dict):
                    meta = {}
                res.append(entity_list_payload(obj_id, props, meta))
            except BaseException as row_exc:
                print(f"[list_entities] Row error for {obj_id}: {row_exc}")
                res.append(json_safe_dict({
                    'id': str(obj_id),
                    'name': str(obj_id),
                    'part_type': 'Shape',
                    'material': 'steel',
                    'error': str(row_exc),
                    'volume_m3': 0,
                    'surface_area_m2': 0,
                    'bounding_box': [0, 0, 0, 0, 0, 0],
                    'mass_kg': 0,
                    'density_kg_m3': 7850,
                }))
        return safe_json_response(res, 200)
    except BaseException as e:
        import traceback
        print(f"[list_entities] Error: {traceback.format_exc()}")
        return safe_json_response({'error': str(e)}, 500)

@app.route('/bom', methods=['GET'])
def bom():
    """Return Bill of Materials table for all scene objects."""
    try:
        rows = []
        # Iterate over a snapshot so concurrent scene updates do not break the loop.
        for idx, (obj_id, shape) in enumerate(list(scene_objects.items()), start=1):
            try:
                try:
                    props = get_shape_metrics_light(shape) if shape is not None else {
                        'volume_m3': 0,
                        'surface_area_m2': 0,
                        'bounding_box': [0, 0, 0, 0, 0, 0],
                    }
                except BaseException as e:
                    print(f"[BOM] Error getting properties for {obj_id}: {e}")
                    props = {'volume_m3': 0, 'surface_area_m2': 0, 'bounding_box': [0,0,0,1,1,1]}

                meta = scene_meta.get(obj_id, {})
                if not isinstance(meta, dict):
                    meta = {}
                sx, sy, sz = bbox_sizes_mm(props.get('bounding_box', [0, 0, 0, 0, 0, 0]))
                density = safe_float(meta.get('density_kg_m3', 7850), 7850.0)
                volume = safe_float(props.get('volume_m3', 0), 0.0)
                computed_mass = round(volume * density, 4)
                rm_raw = meta.get('mass_kg')
                if rm_raw is None:
                    mass_kg = computed_mass
                else:
                    rm = json_safe_value(rm_raw)
                    if rm is None or rm == 0 or rm == 0.0:
                        mass_kg = computed_mass
                    else:
                        mass_kg = round(safe_float(rm, computed_mass), 4)
                row = {
                    'item': idx,
                    'id': str(obj_id),
                    'name': str(meta.get('name', obj_id)),
                    'part_type': str(meta.get('part_type', 'Shape')),
                    'material': str(meta.get('material', 'steel')),
                    'density_kg_m3': density,
                    'volume_m3': round(volume, 6),
                    'surface_area_m2': round(safe_float(props.get('surface_area_m2', 0), 0.0), 4),
                    'mass_kg': mass_kg,
                    'size_x_mm': sx,
                    'size_y_mm': sy,
                    'size_z_mm': sz,
                    'num_teeth': meta.get('num_teeth'),
                    'module': meta.get('module'),
                    'pitch_diameter_mm': meta.get('pitch_diameter_mm'),
                    'qty': 1,
                }
                rows.append(json_safe_dict(row))
            except BaseException as row_exc:
                print(f"[BOM] Row error for {obj_id}: {row_exc}")
                rows.append(json_safe_dict({
                    'item': idx,
                    'id': str(obj_id),
                    'name': str(obj_id),
                    'part_type': 'Shape',
                    'material': 'steel',
                    'density_kg_m3': 7850,
                    'volume_m3': 0,
                    'surface_area_m2': 0,
                    'mass_kg': 0,
                    'size_x_mm': 0,
                    'size_y_mm': 0,
                    'size_z_mm': 0,
                    'qty': 1,
                    'error': str(row_exc),
                }))
        return safe_json_response({'bom': rows, 'total_items': len(rows)}, 200)
    except BaseException as e:
        import traceback
        print(f"[BOM] Error: {traceback.format_exc()}")
        return safe_json_response({'error': str(e), 'bom': [], 'total_items': 0}, 500)

@app.route('/delete_object', methods=['POST'])
def delete_object():
    """Remove an object from the scene by id or name."""
    data = request.get_json() or {}
    obj_id = data.get('object_id') or data.get('name') or data.get('id')
    if not obj_id:
        return jsonify({'error': 'object_id is required'}), 400
    # Also try last_object_id
    global last_object_id
    if obj_id == '__last__':
        obj_id = last_object_id
    if obj_id not in scene_objects:
        return jsonify({'error': f"Object '{obj_id}' not found"}), 404
    del scene_objects[obj_id]
    scene_meta.pop(obj_id, None)
    if last_object_id == obj_id:
        last_object_id = next(iter(scene_objects), None)
    return jsonify({'status': 'deleted', 'id': obj_id, 'remaining': len(scene_objects)})

@app.route('/import_step', methods=['POST'])
def import_step():
    """Accept a STEP file upload, parse it, add to scene, return properties."""
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone
    global last_object_id
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided. Send multipart/form-data with field "file"'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.step', delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name
    try:
        reader = STEPControl_Reader()
        status = reader.ReadFile(tmp_path)
        os.remove(tmp_path)
        if status != IFSelect_RetDone:
            return jsonify({'error': 'Failed to parse STEP file — invalid format'}), 400
        reader.TransferRoots()
        shape = reader.OneShape()
    except Exception as e:
        return jsonify({'error': f'STEP import error: {str(e)}'}), 500

    raw_name = f.filename.rsplit('.', 1)[0].replace(' ', '_').replace('-', '_')
    obj_id = raw_name or 'imported_shape'
    # Avoid key collisions
    base = obj_id
    counter = 1
    while obj_id in scene_objects:
        obj_id = f'{base}_{counter}'; counter += 1

    scene_objects[obj_id] = shape
    last_object_id = obj_id
    props = get_shape_properties(shape)
    bb = props.get('bounding_box', [0,0,0,0,0,0])
    sx = round(abs(bb[3]-bb[0]), 2) if len(bb)==6 else 0
    sy = round(abs(bb[4]-bb[1]), 2) if len(bb)==6 else 0
    sz = round(abs(bb[5]-bb[2]), 2) if len(bb)==6 else 0
    scene_meta[obj_id] = {
        'name': obj_id,
        'part_type': 'Imported STEP',
        'material': 'unknown',
        'density_kg_m3': 7850,
        'mass_kg': round(props.get('volume_m3', 0) * 7850, 4),
        'size_x_mm': sx, 'size_y_mm': sy, 'size_z_mm': sz,
    }
    return jsonify({
        'status': 'imported', 'id': obj_id, 'name': obj_id,
        'part_type': 'Imported STEP', 'material': 'unknown',
        'size_x_mm': sx, 'size_y_mm': sy, 'size_z_mm': sz,
        **props
    })

@app.route('/update_shape', methods=['POST'])
def update_shape():
    """Re-generate a shape with updated parameters and replace the old one."""
    global last_object_id
    data = request.get_json() or {}
    obj_id = data.get('object_id') or data.get('id')
    if not obj_id:
        return jsonify({'error': 'object_id is required'}), 400
    if obj_id not in scene_objects:
        return jsonify({'error': f"Object '{obj_id}' not found"}), 404
    meta = scene_meta.get(obj_id, {})
    part_type = meta.get('part_type', 'Shape')
    if part_type == 'Spur Gear':
        num_teeth   = int(float(data.get('num_teeth', meta.get('num_teeth', 24))))
        module      = float(data.get('module', meta.get('module', 2.0)))
        thickness   = float(data.get('thickness', meta.get('thickness_mm', 8.0)))
        bore_radius = float(data.get('bore_radius', meta.get('bore_radius_mm', 8.0)))
        material    = data.get('material', meta.get('material', 'steel'))
        num_teeth   = max(8, min(num_teeth, 60))
        module      = max(0.5, min(module, 10.0))
        thickness   = max(2.0, min(thickness, 50.0))
        shape       = make_gear(num_teeth=num_teeth, module=module, thickness=thickness, bore_radius=bore_radius)
        density_map = {'steel': 7850, 'aluminum': 2700, 'plastic': 1200, 'cast_iron': 7200}
        density     = density_map.get(material, 7850)
        props       = get_shape_properties(shape)
        mass_kg     = round(props['volume_m3'] * density, 4)
        new_id      = f'spur_gear_{num_teeth}t_m{module}'
        del scene_objects[obj_id]
        scene_meta.pop(obj_id, None)
        scene_objects[new_id] = shape
        last_object_id = new_id
        scene_meta[new_id] = {
            'name': new_id, 'part_type': 'Spur Gear',
            'material': material, 'density_kg_m3': density,
            'mass_kg': mass_kg, 'num_teeth': num_teeth, 'module': module,
            'pitch_diameter_mm': num_teeth * module,
            'outer_diameter_mm': (num_teeth + 2) * module,
            'thickness_mm': thickness, 'bore_radius_mm': bore_radius,
        }
        return jsonify({'status': 'updated', 'id': new_id, 'name': new_id,
                        **props, **scene_meta[new_id]})
    else:
        return jsonify({'error': f'Update not yet supported for part type: {part_type}'}), 400

@app.route('/get_entity_count', methods=['GET'])
def get_entity_count():
    return jsonify({'count': len(scene_objects), 'ids': list(scene_objects.keys())})

@app.route('/move_object', methods=['POST'])
def move_object():
    from OCC.Core.gp import gp_Trsf, gp_Vec
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
    
    data = request.get_json() or {}
    target_id = get_real_obj_id(data.get("object_id"))
    x = float(data.get("x", 0.0))
    y = float(data.get("y", 0.0))
    z = float(data.get("z", 0.0))
    
    if target_id not in scene_objects:
        return jsonify({"error": f"Object '{target_id}' not found"}), 404
        
    shape = scene_objects[target_id]
    
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    transformed_shape = BRepBuilderAPI_Transform(shape, trsf).Shape()
    
    scene_objects[target_id] = transformed_shape
    
    props = get_shape_properties(transformed_shape)
    props["id"] = target_id
    return jsonify(props)

@app.route('/boolean_union', methods=['POST'])
def boolean_union():
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
    
    data = request.get_json() or {}
    obj_a_id = data.get("object_a")
    obj_b_id = data.get("object_b")
    
    if obj_a_id not in scene_objects or obj_b_id not in scene_objects:
        return jsonify({"error": "Objects not found"}), 404
        
    shape_a = scene_objects[obj_a_id]
    shape_b = scene_objects[obj_b_id]
    
    fused_shape = BRepAlgoAPI_Fuse(shape_a, shape_b).Shape()
    
    new_id = f"{obj_a_id}_union_{obj_b_id}"
    scene_objects[new_id] = fused_shape
    
    props = get_shape_properties(fused_shape)
    props["id"] = new_id
    return jsonify(props)

@app.route('/boolean_cut', methods=['POST'])
def boolean_cut():
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
    
    data = request.get_json() or {}
    obj_a_id = data.get("object_a")
    obj_b_id = data.get("object_b")
    
    if obj_a_id not in scene_objects or obj_b_id not in scene_objects:
        return jsonify({"error": "Objects not found"}), 404
        
    shape_a = scene_objects[obj_a_id]
    shape_b = scene_objects[obj_b_id]
    
    cut_shape = BRepAlgoAPI_Cut(shape_a, shape_b).Shape()
    
    new_id = f"{obj_a_id}_cut_{obj_b_id}"
    scene_objects[new_id] = cut_shape
    
    props = get_shape_properties(cut_shape)
    props["id"] = new_id
    return jsonify(props)

@app.route('/get_mass_properties', methods=['POST'])
def get_mass_properties():
    from OCC.Core.GProp import GProp_GProps
    data = request.get_json() or {}
    obj_id = data.get("object_id")
    density = float(data.get("density_kg_m3", 1000.0))
    
    if obj_id not in scene_objects:
        return jsonify({"error": "Object not found"}), 404
        
    shape = scene_objects[obj_id]
    
    props = GProp_GProps()
    try:
        from OCC.Core.BRepGProp import brepgprop_VolumeProperties
        brepgprop_VolumeProperties(shape, props)
    except ImportError:
        from OCC.Core.BRepGProp import brepgprop
        brepgprop.VolumeProperties(shape, props)
    volume = props.Mass()
    
    mass_kg = volume * density
    
    return jsonify({"object_id": obj_id, "mass_kg": mass_kg, "volume_m3": volume})

@app.route('/fillet_edges', methods=['POST'])
def fillet_edges():
    from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_EDGE
    from OCC.Core.TopoDS import topods
    
    data = request.get_json() or {}
    obj_id = data.get("object_id")
    radius = float(data.get("radius", 0.5))
    
    if obj_id not in scene_objects:
        return jsonify({"error": "Object not found"}), 404
        
    shape = scene_objects[obj_id]
    
    fillet = BRepFilletAPI_MakeFillet(shape)
    explorer = TopExp_Explorer(shape, TopAbs_EDGE)
    while explorer.More():
        edge = topods.Edge(explorer.Current())
        fillet.Add(radius, edge)
        explorer.Next()
        
    try:
        new_shape = fillet.Shape()
        scene_objects[obj_id] = new_shape
        props = get_shape_properties(new_shape)
        props["id"] = obj_id
        return jsonify(props)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/rotate_object', methods=['POST'])
def rotate_object():
    from OCC.Core.gp import gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCC.Core.BRepBndLib import brepbndlib_Add
    from OCC.Core.Bnd import Bnd_Box
    import math

    data = request.get_json() or {}
    target_id = get_real_obj_id(data.get("object_id"))
    axis = str(data.get("axis", "Z")).upper()
    angle_deg = float(data.get("angle", 90.0))

    if target_id not in scene_objects:
        return jsonify({"error": f"Object '{target_id}' not found"}), 404

    shape = scene_objects[target_id]

    # Get object center to rotate around itself
    bbox = Bnd_Box()
    try:
        from OCC.Core.BRepBndLib import brepbndlib
        brepbndlib.Add(shape, bbox, True)
    except:
        brepbndlib_Add(shape, bbox, True)
    
    if bbox.IsVoid():
        cX, cY, cZ = 0., 0., 0.
    else:
        min_x, min_y, min_z, max_x, max_y, max_z = bbox.Get()
        cX, cY, cZ = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0, (min_z + max_z) / 2.0

    if axis == "X":
        ax1 = gp_Ax1(gp_Pnt(cX, cY, cZ), gp_Dir(1, 0, 0))
    elif axis == "Y":
        ax1 = gp_Ax1(gp_Pnt(cX, cY, cZ), gp_Dir(0, 1, 0))
    else:
        ax1 = gp_Ax1(gp_Pnt(cX, cY, cZ), gp_Dir(0, 0, 1))

    trsf = gp_Trsf()
    trsf.SetRotation(ax1, math.radians(angle_deg))
    new_shape = BRepBuilderAPI_Transform(shape, trsf).Shape()

    scene_objects[target_id] = new_shape
    props = get_shape_properties(new_shape)
    props["id"] = target_id
    props["name"] = target_id
    props["rotated"] = {"axis": axis, "angle_deg": angle_deg}
    return jsonify(props)

@app.route('/scale_object', methods=['POST'])
def scale_object():
    from OCC.Core.gp import gp_Trsf, gp_Pnt
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCC.Core.Bnd import Bnd_Box
    
    try:
        data = request.get_json() or {}
        target_id = get_real_obj_id(data.get("object_id"))
        factor = float(data.get("factor", 1.5))
        factor = max(0.01, min(factor, 100.0))
        
        if target_id not in scene_objects:
            return jsonify({"error": f"Object '{target_id}' not found"}), 404
            
        shape = scene_objects[target_id]
        meta = scene_meta.get(target_id, {})
        material = meta.get('material', 'steel')
        
        # Scale center
        bbox = Bnd_Box()
        try:
            from OCC.Core.BRepBndLib import brepbndlib
            brepbndlib.Add(shape, bbox, True)
        except:
            from OCC.Core.BRepBndLib import brepbndlib_Add
            brepbndlib_Add(shape, bbox, True)
        
        min_x, min_y, min_z, max_x, max_y, max_z = bbox.Get()
        cX, cY, cZ = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0, (min_z + max_z) / 2.0

        trsf = gp_Trsf()
        trsf.SetScale(gp_Pnt(cX, cY, cZ), factor)
        new_shape = BRepBuilderAPI_Transform(shape, trsf).Shape()
        
        scene_objects[target_id] = new_shape
        props = get_shape_properties(new_shape)
        
        # Calculate mass
        density_map = {'steel': 7850, 'aluminum': 2700, 'plastic': 1200, 'concrete': 2400, 'wood': 700, 'cast_iron': 7200}
        density = density_map.get(material, 7850)
        mass_kg = round(props['volume_m3'] * density, 4)
        
        # Update metadata
        scene_meta[target_id] = {**meta, 'props': props, 'mass_kg': mass_kg}
        
        return jsonify({
            'status': 'scaled',
            'name': target_id,
            'id': target_id,
            'scale_factor': factor,
            'material': material,
            'mass_kg': mass_kg,
            'density_kg_m3': density,
            **props
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/mirror_object', methods=['POST'])
def mirror_object():
    from OCC.Core.gp import gp_Trsf, gp_Ax2, gp_Pnt, gp_Dir
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
    
    data = request.get_json() or {}
    target_id = get_real_obj_id(data.get("object_id"))
    plane = data.get("plane", "XY").upper()
    
    if target_id not in scene_objects:
        return jsonify({"error": f"Object '{target_id}' not found"}), 404
        
    shape = scene_objects[target_id]
    
    if plane == "XY":
        ax2 = gp_Ax2(gp_Pnt(0,0,0), gp_Dir(0,0,1))
    elif plane == "XZ":
        ax2 = gp_Ax2(gp_Pnt(0,0,0), gp_Dir(0,1,0))
    elif plane == "YZ":
        ax2 = gp_Ax2(gp_Pnt(0,0,0), gp_Dir(1,0,0))
    else:
        ax2 = gp_Ax2(gp_Pnt(0,0,0), gp_Dir(0,0,1))
        
    trsf = gp_Trsf()
    trsf.SetMirror(ax2)
    new_shape = BRepBuilderAPI_Transform(shape, trsf).Shape()
    
    scene_objects[target_id] = new_shape
    props = get_shape_properties(new_shape)
    props["id"] = target_id
    return jsonify(props)

@app.route('/create_assembly', methods=['POST'])
def create_assembly():
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
    
    data = request.get_json() or {}
    parts = data.get("parts", [])
    name = data.get("name", "my_assembly")
    
    if not parts:
        return jsonify({"error": "No parts provided"}), 400
        
    valid_shapes = [scene_objects[pid] for pid in parts if pid in scene_objects]
    if not valid_shapes:
        return jsonify({"error": "No valid parts found in scene"}), 404
        
    result_shape = valid_shapes[0]
    for obj in valid_shapes[1:]:
        result_shape = BRepAlgoAPI_Fuse(result_shape, obj).Shape()
        
    scene_objects[name] = result_shape
    props = get_shape_properties(result_shape)
    props["id"] = name
    props["name"] = name
    return jsonify(props)

@app.route('/get_scene', methods=['POST', 'GET'])
def get_scene():
    from OCC.Core.GProp import GProp_GProps
    try:
        from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
        brepgprop_v = brepgprop_VolumeProperties
        brepgprop_s = brepgprop_SurfaceProperties
    except ImportError:
        from OCC.Core.BRepGProp import brepgprop
        brepgprop_v = brepgprop.VolumeProperties
        brepgprop_s = brepgprop.SurfaceProperties

    res = []
    for obj_id, shape in scene_objects.items():
        v_props = GProp_GProps()
        s_props = GProp_GProps()
        brepgprop_v(shape, v_props)
        brepgprop_s(shape, s_props)
        res.append({
            "name": obj_id,
            "part_type": "shape",
            "volume_m3": v_props.Mass(),
            "surface_area_m2": s_props.Mass()
        })
    return jsonify(res)

@app.route('/modify_dimensions', methods=['POST'])
def modify_dimensions():
    try:
        data = request.get_json() or {}
        obj_id = data.get("object_id")
        parameter = data.get("parameter", "height").lower()
        value = float(data.get("value", 10.0))
        unit = data.get("unit", "mm").lower()
        
        if obj_id not in scene_objects:
            return jsonify({"error": f"Object '{obj_id}' not found"}), 404
        
        # Convert mm to cm (OCCT uses cm)
        if unit == "mm":
            value_cm = value / 10.0
        else:
            value_cm = value
        value_cm = max(0.1, value_cm)
        
        # Get object metadata
        meta = scene_meta.get(obj_id, {})
        part_type = meta.get('part_type', obj_id).lower()
        material = meta.get('material', 'steel')
        
        # Get current bounding box
        old_shape = scene_objects[obj_id]
        old_props = get_shape_properties(old_shape)
        bbox = old_props['bounding_box']
        
        # Determine the current dimensions
        current_x = abs(bbox[3] - bbox[0])
        current_y = abs(bbox[4] - bbox[1])
        current_z = abs(bbox[5] - bbox[2])
        
        # Create new shape based on type
        if 'shaft' in part_type or 'cylinder' in part_type or 'rod' in part_type or 'pipe' in part_type:
            current_r = max(current_x, current_y) / 2.0
            if parameter in ['height', 'length']:
                shape = BRepPrimAPI_MakeCylinder(current_r, value_cm).Shape()
            else:
                shape = BRepPrimAPI_MakeCylinder(value_cm, current_z).Shape()
        elif 'sphere' in part_type or 'ball' in part_type:
            shape = BRepPrimAPI_MakeSphere(value_cm).Shape()
        elif 'cone' in part_type or 'nozzle' in part_type:
            current_r = max(current_x, current_y) / 2.0
            if parameter in ['height', 'length']:
                shape = BRepPrimAPI_MakeCone(current_r, current_r * 0.3, value_cm).Shape()
            else:
                shape = BRepPrimAPI_MakeCone(value_cm, value_cm * 0.3, current_z).Shape()
        else:
            # Default to box
            if parameter == 'height' or parameter == 'length':
                shape = BRepPrimAPI_MakeBox(current_x, current_y, value_cm).Shape()
            elif parameter == 'width':
                shape = BRepPrimAPI_MakeBox(value_cm, current_y, current_z).Shape()
            elif parameter == 'depth':
                shape = BRepPrimAPI_MakeBox(current_x, value_cm, current_z).Shape()
            elif parameter == 'radius':
                shape = BRepPrimAPI_MakeBox(value_cm * 2, value_cm * 2, current_z).Shape()
            else:
                shape = BRepPrimAPI_MakeBox(value_cm, value_cm, value_cm).Shape()
        
        props = get_shape_properties(shape)
        
        # Calculate mass
        density_map = {'steel': 7850, 'aluminum': 2700, 'plastic': 1200, 'concrete': 2400, 'wood': 700, 'cast_iron': 7200}
        density = density_map.get(material, 7850)
        mass_kg = round(props['volume_m3'] * density, 4)
        
        # Update scene
        scene_objects[obj_id] = shape
        scene_meta[obj_id] = {**meta, 'props': props, 'mass_kg': mass_kg}
        
        return jsonify({
            'status': 'modified',
            'name': obj_id,
            'parameter': parameter,
            'new_value': value,
            'unit': unit,
            'material': material,
            'mass_kg': mass_kg,
            'density_kg_m3': density,
            **props
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ---------------------------------------------------------------------------
# Scene Generation Engine — compose multiple primitives into rich 3D scenes
# ---------------------------------------------------------------------------

SCENE_RECIPES = {
    "room": {
        "label": "Room Interior",
        "parts": [
            {"type": "box", "dims": [12, 12, 0.3], "pos": [0, 0, 0]},          # floor
            {"type": "box", "dims": [12, 0.3, 6], "pos": [0, 12, 0]},          # back wall
            {"type": "box", "dims": [0.3, 12, 6], "pos": [0, 0, 0]},           # left wall
            {"type": "box", "dims": [0.3, 12, 6], "pos": [12, 0, 0]},          # right wall
            {"type": "box", "dims": [4, 2.5, 0.6], "pos": [1, 1, 0.3]},        # bed frame
            {"type": "box", "dims": [3.8, 2.3, 0.4], "pos": [1.1, 1.1, 0.9]},  # mattress
            {"type": "box", "dims": [3.8, 0.3, 1.2], "pos": [1.1, 1, 0.9]},    # headboard
            {"type": "cylinder", "dims": [0.35, 0.25], "pos": [1.7, 1.7, 1.3]}, # pillow1
            {"type": "cylinder", "dims": [0.35, 0.25], "pos": [1.7, 2.6, 1.3]}, # pillow2
            {"type": "box", "dims": [2.5, 1.2, 0.08], "pos": [8, 8, 1.8]},     # tabletop
            {"type": "cylinder", "dims": [0.08, 1.8], "pos": [8.2, 8.2, 0.3]},  # leg1
            {"type": "cylinder", "dims": [0.08, 1.8], "pos": [10.2, 8.2, 0.3]}, # leg2
            {"type": "cylinder", "dims": [0.08, 1.8], "pos": [8.2, 9, 0.3]},    # leg3
            {"type": "cylinder", "dims": [0.08, 1.8], "pos": [10.2, 9, 0.3]},   # leg4
            {"type": "box", "dims": [1.2, 1.2, 0.08], "pos": [8.6, 1, 1.1]},   # chair seat
            {"type": "box", "dims": [1.2, 0.08, 1.5], "pos": [8.6, 1, 1.1]},   # chair back
            {"type": "cylinder", "dims": [0.06, 1.1], "pos": [8.7, 1.1, 0.3]},  # chair leg1
            {"type": "cylinder", "dims": [0.06, 1.1], "pos": [9.7, 1.1, 0.3]},  # chair leg2
            {"type": "cylinder", "dims": [0.06, 1.1], "pos": [8.7, 2.0, 0.3]},  # chair leg3
            {"type": "cylinder", "dims": [0.06, 1.1], "pos": [9.7, 2.0, 0.3]},  # chair leg4
        ]
    },
    "car": {
        "label": "Car Body",
        "parts": [
            {"type": "box", "dims": [6, 2.5, 1], "pos": [0, 0, 0.8]},          # body lower
            {"type": "box", "dims": [3, 2.3, 1.2], "pos": [1.2, 0.1, 1.8]},    # cabin
            {"type": "cylinder", "dims": [0.5, 0.4], "pos": [1, -0.2, 0.5]},    # wheel FL
            {"type": "cylinder", "dims": [0.5, 0.4], "pos": [1, 2.5, 0.5]},     # wheel FR
            {"type": "cylinder", "dims": [0.5, 0.4], "pos": [4.5, -0.2, 0.5]},  # wheel RL
            {"type": "cylinder", "dims": [0.5, 0.4], "pos": [4.5, 2.5, 0.5]},   # wheel RR
            {"type": "box", "dims": [0.6, 2.2, 0.15], "pos": [6, 0.15, 1.5]},   # rear spoiler
            {"type": "box", "dims": [0.15, 0.8, 0.3], "pos": [-0.15, 0.2, 1.2]},# headlight L
            {"type": "box", "dims": [0.15, 0.8, 0.3], "pos": [-0.15, 1.5, 1.2]},# headlight R
        ]
    },
    "robot": {
        "label": "Robot Figure",
        "parts": [
            {"type": "sphere", "dims": [1.2], "pos": [0, 0, 7]},                # head
            {"type": "box", "dims": [3, 2, 3.5], "pos": [-1.5, -1, 3]},         # torso
            {"type": "cylinder", "dims": [0.4, 3], "pos": [-2.2, 0, 3.5]},      # left arm
            {"type": "cylinder", "dims": [0.4, 3], "pos": [1.8, 0, 3.5]},       # right arm
            {"type": "cylinder", "dims": [0.5, 3], "pos": [-0.8, 0, 0]},        # left leg
            {"type": "cylinder", "dims": [0.5, 3], "pos": [0.5, 0, 0]},         # right leg
            {"type": "box", "dims": [0.8, 1.2, 0.3], "pos": [-1.1, -0.6, 0]},   # left foot
            {"type": "box", "dims": [0.8, 1.2, 0.3], "pos": [0.3, -0.6, 0]},    # right foot
            {"type": "sphere", "dims": [0.25], "pos": [-0.5, -1.3, 7.3]},       # left eye
            {"type": "sphere", "dims": [0.25], "pos": [0.5, -1.3, 7.3]},        # right eye
            {"type": "cylinder", "dims": [0.15, 0.8], "pos": [0, -1.2, 8.2]},   # antenna
        ]
    },
    "house": {
        "label": "House",
        "parts": [
            {"type": "box", "dims": [10, 8, 6], "pos": [0, 0, 0]},             # main walls
            {"type": "box", "dims": [9.4, 7.4, 5.5], "pos": [0.3, 0.3, 0.3]},  # hollow cutout (note: we fuse, so this becomes solid)
            {"type": "cone", "dims": [7, 10], "pos": [5, 4, 6]},                # roof
            {"type": "box", "dims": [2, 0.3, 3.5], "pos": [4, -0.15, 0]},       # door
            {"type": "box", "dims": [1.5, 0.2, 1.5], "pos": [1, -0.1, 3]},     # window L
            {"type": "box", "dims": [1.5, 0.2, 1.5], "pos": [7.5, -0.1, 3]},   # window R
            {"type": "cylinder", "dims": [0.6, 3], "pos": [8, 5, 6]},           # chimney
        ]
    },
    "bridge": {
        "label": "Bridge Structure",
        "parts": [
            {"type": "box", "dims": [20, 4, 0.5], "pos": [0, 0, 4]},           # deck
            {"type": "cylinder", "dims": [0.8, 4], "pos": [2, 2, 0]},           # pillar 1
            {"type": "cylinder", "dims": [0.8, 4], "pos": [10, 2, 0]},          # pillar 2
            {"type": "cylinder", "dims": [0.8, 4], "pos": [18, 2, 0]},          # pillar 3
            {"type": "box", "dims": [20, 0.2, 1.5], "pos": [0, 0, 4.5]},       # railing L
            {"type": "box", "dims": [20, 0.2, 1.5], "pos": [0, 3.8, 4.5]},     # railing R
        ]
    },
    "table": {
        "label": "Table",
        "parts": [
            {"type": "box", "dims": [4, 2.5, 0.2], "pos": [0, 0, 2.5]},         # tabletop
            {"type": "box", "dims": [0.2, 0.2, 2.5], "pos": [0, 0, 0]},          # leg 1
            {"type": "box", "dims": [0.2, 0.2, 2.5], "pos": [3.8, 0, 0]},        # leg 2
            {"type": "box", "dims": [0.2, 0.2, 2.5], "pos": [0, 2.3, 0]},        # leg 3
            {"type": "box", "dims": [0.2, 0.2, 2.5], "pos": [3.8, 2.3, 0]},      # leg 4
            {"type": "box", "dims": [4, 0.15, 0.15], "pos": [0, 0.1, 0.5]},      # front stretcher
            {"type": "box", "dims": [4, 0.15, 0.15], "pos": [0, 2.2, 0.5]},      # back stretcher
        ]
    },
    "chair": {
        "label": "Chair",
        "parts": [
            {"type": "box", "dims": [2, 2, 0.15], "pos": [0, 0, 1.8]},          # seat
            {"type": "box", "dims": [2, 0.15, 1.6], "pos": [0, 1.85, 1.8]},     # backrest
            {"type": "box", "dims": [0.15, 0.15, 1.8], "pos": [0, 0, 0]},       # leg front-left
            {"type": "box", "dims": [0.15, 0.15, 1.8], "pos": [1.85, 0, 0]},    # leg front-right
            {"type": "box", "dims": [0.15, 0.15, 1.8], "pos": [0, 1.85, 0]},    # leg back-left
            {"type": "box", "dims": [0.15, 0.15, 1.8], "pos": [1.85, 1.85, 0]}, # leg back-right
            {"type": "box", "dims": [2, 0.1, 0.15], "pos": [0, 0.95, 0.4]},     # front crossbar
            {"type": "box", "dims": [0.1, 2, 0.15], "pos": [0.95, 0, 0.4]},     # side crossbar
        ]
    },
    "desk": {
        "label": "Office Desk with Monitor",
        "parts": [
            {"type": "box", "dims": [5, 2.5, 0.12], "pos": [0, 0, 1.8]},       # desktop
            {"type": "box", "dims": [0.5, 2.4, 1.8], "pos": [0, 0.05, 0]},      # left panel
            {"type": "box", "dims": [0.5, 2.4, 1.8], "pos": [4.5, 0.05, 0]},    # right panel
            {"type": "box", "dims": [2, 0.08, 1.4], "pos": [1.5, 0.2, 1.92]},   # monitor screen
            {"type": "box", "dims": [0.6, 0.08, 0.4], "pos": [2.2, 0.2, 3.32]}, # monitor top
            {"type": "cylinder", "dims": [0.12, 0.5], "pos": [2.5, 0.3, 1.92]}, # monitor stand
            {"type": "box", "dims": [0.8, 0.3, 0.05], "pos": [2.1, 0.5, 1.92]}, # keyboard
        ]
    },
    "castle": {
        "label": "Castle",
        "parts": [
            {"type": "box", "dims": [12, 12, 6], "pos": [0, 0, 0]},            # main keep
            {"type": "cylinder", "dims": [1.5, 8], "pos": [0, 0, 0]},           # tower FL
            {"type": "cylinder", "dims": [1.5, 8], "pos": [12, 0, 0]},          # tower FR
            {"type": "cylinder", "dims": [1.5, 8], "pos": [0, 12, 0]},          # tower BL
            {"type": "cylinder", "dims": [1.5, 8], "pos": [12, 12, 0]},         # tower BR
            {"type": "cone", "dims": [2, 3], "pos": [0, 0, 8]},                 # tower hat FL
            {"type": "cone", "dims": [2, 3], "pos": [12, 0, 8]},                # tower hat FR
            {"type": "cone", "dims": [2, 3], "pos": [0, 12, 8]},                # tower hat BL
            {"type": "cone", "dims": [2, 3], "pos": [12, 12, 8]},               # tower hat BR
            {"type": "box", "dims": [3, 1, 4], "pos": [4.5, -0.5, 0]},          # gate
        ]
    },
    "tower": {
        "label": "Tower",
        "parts": [
            {"type": "cylinder", "dims": [3, 15], "pos": [0, 0, 0]},            # main shaft
            {"type": "cone", "dims": [4, 5], "pos": [0, 0, 15]},                # roof
            {"type": "box", "dims": [1.5, 0.3, 3], "pos": [-0.75, -3.3, 0]},    # door
            {"type": "box", "dims": [1, 0.3, 1.5], "pos": [-0.5, -3.3, 8]},     # window
        ]
    },
    "airplane": {
        "label": "Airplane",
        "parts": [
            {"type": "cylinder", "dims": [1.2, 14], "pos": [0, 0, 0]},          # fuselage
            {"type": "box", "dims": [0.3, 12, 1], "pos": [0, -6, -0.5]},        # wings
            {"type": "box", "dims": [0.2, 4, 0.8], "pos": [13, -2, -0.4]},      # tail wings
            {"type": "box", "dims": [0.15, 0.3, 2.5], "pos": [13, -0.15, 0]},   # vertical tail
            {"type": "cone", "dims": [1.2, 2], "pos": [0, 0, 0]},               # nose cone (overlaps fuselage)
        ]
    },
    "shelf": {
        "label": "Bookshelf",
        "parts": [
            {"type": "box", "dims": [3, 0.4, 5], "pos": [0, 0, 0]},             # back panel
            {"type": "box", "dims": [3, 1.2, 0.15], "pos": [0, 0, 0]},          # shelf 1
            {"type": "box", "dims": [3, 1.2, 0.15], "pos": [0, 0, 1.25]},       # shelf 2
            {"type": "box", "dims": [3, 1.2, 0.15], "pos": [0, 0, 2.5]},        # shelf 3
            {"type": "box", "dims": [3, 1.2, 0.15], "pos": [0, 0, 3.75]},       # shelf 4
            {"type": "box", "dims": [3, 1.2, 0.15], "pos": [0, 0, 4.85]},       # shelf 5 (top)
            {"type": "box", "dims": [0.15, 1.2, 5], "pos": [0, 0, 0]},          # left side
            {"type": "box", "dims": [0.15, 1.2, 5], "pos": [2.85, 0, 0]},       # right side
        ]
    },
    "boat": {
        "label": "Boat",
        "parts": [
            {"type": "box", "dims": [8, 3, 1.5], "pos": [0, 0, 0]},             # hull
            {"type": "cone", "dims": [1.5, 2], "pos": [0, 1.5, 0.75]},          # bow
            {"type": "cylinder", "dims": [0.15, 5], "pos": [4, 1.5, 1.5]},      # mast
            {"type": "box", "dims": [0.05, 2, 3.5], "pos": [4, 0.5, 2.5]},      # sail
            {"type": "box", "dims": [2.5, 2, 0.8], "pos": [5, 0.5, 1.5]},       # cabin
        ]
    },
    "tree": {
        "label": "Tree",
        "parts": [
            {"type": "cylinder", "dims": [0.5, 4], "pos": [0, 0, 0]},           # trunk
            {"type": "sphere", "dims": [2.5], "pos": [0, 0, 5.5]},              # canopy
        ]
    },
    "lamp": {
        "label": "Table Lamp",
        "parts": [
            {"type": "cylinder", "dims": [1.5, 0.3], "pos": [0, 0, 0]},         # base
            {"type": "cylinder", "dims": [0.15, 4], "pos": [0, 0, 0.3]},        # shaft
            {"type": "cone", "dims": [2, 1.5], "pos": [0, 0, 4.3]},             # shade
        ]
    },
}

def _build_scene(recipe_parts):
    """Compose multiple primitive shapes into a single fused solid."""
    from OCC.Core.BRepPrimAPI import (
        BRepPrimAPI_MakeBox,
        BRepPrimAPI_MakeCylinder,
        BRepPrimAPI_MakeCone,
        BRepPrimAPI_MakeSphere,
    )
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCC.Core.gp import gp_Trsf, gp_Vec
    from OCC.Core.TopoDS import TopoDS_Compound
    from OCC.Core.BRep import BRep_Builder

    shapes = []
    for part in recipe_parts:
        ptype = part["type"]
        dims = part["dims"]
        px, py, pz = part.get("pos", [0, 0, 0])

        if ptype == "box":
            s = BRepPrimAPI_MakeBox(dims[0], dims[1], dims[2]).Shape()
        elif ptype == "cylinder":
            s = BRepPrimAPI_MakeCylinder(dims[0], dims[1]).Shape()
        elif ptype == "cone":
            s = BRepPrimAPI_MakeCone(dims[0], dims[0] * 0.01, dims[1]).Shape()
        elif ptype == "sphere":
            s = BRepPrimAPI_MakeSphere(dims[0]).Shape()
        else:
            s = BRepPrimAPI_MakeBox(1, 1, 1).Shape()

        if px != 0 or py != 0 or pz != 0:
            trsf = gp_Trsf()
            trsf.SetTranslation(gp_Vec(px, py, pz))
            s = BRepBuilderAPI_Transform(s, trsf).Shape()

        shapes.append(s)

    if not shapes:
        return BRepPrimAPI_MakeBox(1, 1, 1).Shape()

    # Build as compound (faster + no boolean edge-case crashes)
    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    for s in shapes:
        builder.Add(compound, s)
    return compound


def _match_scene(description):
    """Find the best matching scene recipe from a free-text description."""
    desc = description.lower()
    # Direct keyword matching with synonyms
    keyword_map = {
        "room": ["room", "bedroom", "living room", "interior", "apartment", "flat"],
        "car": ["car", "vehicle", "automobile", "sedan", "suv", "truck"],
        "robot": ["robot", "mech", "android", "humanoid", "cyborg", "mecha"],
        "house": ["house", "home", "cottage", "building", "bungalow", "cabin"],
        "bridge": ["bridge", "overpass", "viaduct"],
        "table": ["table", "dining table", "coffee table"],
        "chair": ["chair", "seat", "stool"],
        "desk": ["desk", "workstation", "office desk", "study table", "computer desk"],
        "castle": ["castle", "fortress", "fort", "palace", "keep"],
        "tower": ["tower", "turret", "lighthouse", "watchtower", "spire"],
        "airplane": ["airplane", "aeroplane", "plane", "aircraft", "jet", "aero"],
        "shelf": ["shelf", "bookshelf", "bookcase", "shelving", "rack", "cupboard", "wardrobe"],
        "boat": ["boat", "ship", "yacht", "sailboat", "vessel", "canoe"],
        "tree": ["tree", "oak", "pine", "plant", "forest"],
        "lamp": ["lamp", "light", "lantern", "torch"],
    }
    for recipe_key, keywords in keyword_map.items():
        for kw in keywords:
            if kw in desc:
                return recipe_key
    return None


@app.route('/generate_scene', methods=['POST'])
def generate_scene_route():
    data = request.get_json() or {}
    description = data.get("description", "")
    
    recipe_key = _match_scene(description)
    if not recipe_key or recipe_key not in SCENE_RECIPES:
        # Default to a room if we can't figure it out
        recipe_key = "room"
    
    recipe = SCENE_RECIPES[recipe_key]
    compound = _build_scene(recipe["parts"])
    
    global last_object_id
    obj_id = recipe_key + "_scene"
    scene_objects[obj_id] = compound
    last_object_id = obj_id

    props = get_shape_properties(compound)
    density = 7850
    mass_kg = round(props["volume_m3"] * density, 4)
    scene_meta[obj_id] = {
        "name": obj_id,
        "part_type": recipe["label"],
        "material": "steel",
        "density_kg_m3": density,
        "mass_kg": mass_kg,
    }

    props["id"] = obj_id
    props["name"] = recipe["label"]
    props["scene_type"] = recipe_key
    props["mass_kg"] = mass_kg
    props["material"] = "steel"
    props["density_kg_m3"] = density
    props["part_type"] = recipe["label"]
    return jsonify(props)


# ---------------------------------------------------------------------------
# LLM-driven Shape Generation — accepts geometry JSON with boolean operations
# ---------------------------------------------------------------------------

def safe_build_primitive(geo_type, dims):
    from OCC.Core.BRepPrimAPI import (
        BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder,
        BRepPrimAPI_MakeSphere, BRepPrimAPI_MakeCone, BRepPrimAPI_MakeTorus
    )
    try:
        w = max(float(dims.get("width", 5)), 0.1)
        h = max(float(dims.get("height", 5)), 0.1)
        d = max(float(dims.get("depth", 5)), 0.1)
        r = max(float(dims.get("radius", 2.5)), 0.1)
        ir = float(dims.get("inner_radius", 1.0))
        tr = float(dims.get("top_radius", r * 0.3))
        ir = min(ir, r - 0.1)
        ir = max(ir, 0.05)
        tr = min(tr, r - 0.1)
        tr = max(tr, 0.05)
        if geo_type == "box":
            return BRepPrimAPI_MakeBox(w, d, h).Shape()
        elif geo_type == "cylinder":
            return BRepPrimAPI_MakeCylinder(r, h).Shape()
        elif geo_type == "sphere":
            return BRepPrimAPI_MakeSphere(r).Shape()
        elif geo_type == "cone":
            return BRepPrimAPI_MakeCone(r, tr, h).Shape()
        elif geo_type == "torus":
            return BRepPrimAPI_MakeTorus(r, ir).Shape()
        else:
            return BRepPrimAPI_MakeBox(w, d, h).Shape()
    except Exception as e:
        print(f"Primitive build failed for {geo_type}: {e}")
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
        return BRepPrimAPI_MakeBox(5, 5, 5).Shape()


@app.route('/generate_shape', methods=['POST'])
def generate_shape_llm():
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCC.Core.gp import gp_Trsf, gp_Vec

    try:
        data = request.json or {}
        geometry = data.get('geometry', {})
        name = str(data.get('name', 'generated_shape')).replace(' ', '_')
        material = data.get('material', 'steel')
        description = data.get('shape_description', name)

        geo_type = geometry.get('type', 'box')
        dims = geometry.get('dimensions', {})
        operations = geometry.get('operations', [])

        shape = safe_build_primitive(geo_type, dims)

        for op in operations:
            try:
                op_type = op.get('type', 'fuse')
                op_shape_type = op.get('shape', 'box')
                op_dims = op.get('dimensions', {})
                op_pos = op.get('position', {"x": 0, "y": 0, "z": 0})

                op_primitive = safe_build_primitive(op_shape_type, op_dims)

                px = float(op_pos.get('x', 0))
                py = float(op_pos.get('y', 0))
                pz = float(op_pos.get('z', 0))

                if px != 0 or py != 0 or pz != 0:
                    trsf = gp_Trsf()
                    trsf.SetTranslation(gp_Vec(px, py, pz))
                    op_primitive = BRepBuilderAPI_Transform(op_primitive, trsf).Shape()

                if op_type == 'fuse':
                    result = BRepAlgoAPI_Fuse(shape, op_primitive)
                    if result.IsDone():
                        shape = result.Shape()
                elif op_type == 'cut':
                    result = BRepAlgoAPI_Cut(shape, op_primitive)
                    if result.IsDone():
                        shape = result.Shape()
            except Exception as op_error:
                print(f"Operation {op_type} failed, skipping: {op_error}")
                continue

        props = get_shape_properties(shape)

        density_map = {
            "steel": 7850, "aluminum": 2700,
            "plastic": 1200, "concrete": 2400, "wood": 700
        }
        density = density_map.get(material, 7850)
        mass_kg = round(props["volume_m3"] * density, 4)

        global last_object_id
        scene_objects[name] = shape
        last_object_id = name
        scene_meta[name] = {
            "name": name,
            "part_type": description or geo_type.replace("_", " ").title(),
            "material": material,
            "density_kg_m3": density,
            "mass_kg": mass_kg,
        }

        return jsonify({
            "status": "generated",
            "name": name,
            "shape_description": description,
            "part_type": scene_meta[name]["part_type"],
            "material": material,
            "density_kg_m3": density,
            "mass_kg": mass_kg,
            "step_b64": props["step_b64"],
            "glb_b64": props.get("glb_b64") or "",
            "volume_m3": props["volume_m3"],
            "surface_area_m2": props["surface_area_m2"],
            "bounding_box": props["bounding_box"],
        })
    except Exception as e:
        print(f"generate_shape failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0")


