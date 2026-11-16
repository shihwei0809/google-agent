import json
import math
import os
import bpy
import bmesh
from mathutils import Vector, Quaternion

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
MP4_PATH = os.path.join(OUT_DIR, "fpv_white_model.mp4")
FIRST_FRAME_PATH = os.path.join(OUT_DIR, "fpv_first_frame.png")
LAST_FRAME_PATH = os.path.join(OUT_DIR, "fpv_last_frame.png")
BLEND_PATH = os.path.join(OUT_DIR, "fpv_white_model.blend")
GLB_PATH = os.path.join(OUT_DIR, "fpv_white_model.glb")
CAM_PATH_JSON = os.path.join(OUT_DIR, "fpv_camera_path.json")


def make_clay_material(name, color, roughness=0.72, metallic=0.02):
    """Create a clean matte clay white-model material for GLB export & Three.js."""
    mat = bpy.data.materials.new(name=name)
    if hasattr(mat, "use_nodes"):
        mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF") or nodes.new(type="ShaderNodeBsdfPrincipled")
    if "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = (*color[:3], 1.0)
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = roughness
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_box(bm, center, size, rot_euler=(0.0, 0.0, 0.0)):
    """Add a box into bmesh with optional Euler rotation around its center."""
    sx, sy, sz = size
    cx, cy, cz = center
    ret = bmesh.ops.create_cube(bm, size=1.0)
    verts = ret["verts"]
    for v in verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    if any(abs(a) > 1e-6 for a in rot_euler):
        from mathutils import Euler
        rot_mat = Euler(rot_euler, "XYZ").to_matrix()
        bmesh.ops.rotate(bm, verts=verts, cent=(0.0, 0.0, 0.0), matrix=rot_mat)
    for v in verts:
        v.co.x += cx
        v.co.y += cy
        v.co.z += cz


def add_cylinder(bm, center, radius, depth, segments=16):
    """Add a vertical cylinder into bmesh."""
    ret = bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=depth,
    )
    cx, cy, cz = center
    for v in ret["verts"]:
        v.co.x += cx
        v.co.y += cy
        v.co.z += cz


def finalize_mesh(name, bm, mat, obj_color, collection, bevel_width=0.0):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    obj.color = (*obj_color[:3], 1.0)
    collection.objects.link(obj)
    if bevel_width > 0:
        mod = obj.modifiers.new(name="Bevel", type="BEVEL")
        mod.width = bevel_width
        mod.segments = 2
        mod.limit_method = "ANGLE"
    return obj


def catmull_rom(p0, p1, p2, p3, t):
    """Evaluate Centripetal-like uniform Catmull-Rom spline segment for t in [0, 1]."""
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        (2.0 * p1)
        + (-p0 + p2) * t
        + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
        + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
    )


def eval_polyline_spline(points, u):
    """Sample a multi-point Catmull-Rom spline at normalized parameter u in [0, 1]."""
    n = len(points)
    if u <= 0.0:
        return points[0].copy()
    if u >= 1.0:
        return points[-1].copy()
    scaled = u * (n - 1)
    idx = min(int(scaled), n - 2)
    t = scaled - idx
    p0 = points[max(0, idx - 1)]
    p1 = points[idx]
    p2 = points[idx + 1]
    p3 = points[min(n - 1, idx + 2)]
    return catmull_rom(p0, p1, p2, p3, t)


def smoothstep(edge0, edge1, x):
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def build_fpv_white_model():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # Configure BLENDER_WORKBENCH for fast, crisp white-model (Previs) output on integrated GPU
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    try:
        shading.light = "STUDIO"
    except Exception:
        pass
    try:
        shading.color_type = "OBJECT"
    except Exception:
        pass
    try:
        shading.show_cavity = True
        shading.cavity_type = "BOTH"
        shading.cavity_ridge_factor = 1.15
        shading.cavity_valley_factor = 1.15
    except Exception:
        pass
    try:
        shading.show_object_outline = True
        shading.object_outline_color = (0.12, 0.14, 0.18)
    except Exception:
        pass
    try:
        shading.show_shadows = True
        shading.shadow_intensity = 0.55
    except Exception:
        pass

    if scene.world is None:
        scene.world = bpy.data.worlds.new("ClayStudioWorld")
    scene.world.color = (0.16, 0.18, 0.22)

    col_env = bpy.data.collections.new("01_Street_Ground")
    col_bldgs = bpy.data.collections.new("02_Buildings")
    col_props = bpy.data.collections.new("03_Bridges_Props")
    col_hero = bpy.data.collections.new("04_Protagonist")
    for c in (col_env, col_bldgs, col_props, col_hero):
        scene.collection.children.link(c)

    # Clay colors & materials
    col_road = (0.48, 0.50, 0.54)
    col_sidewalk = (0.74, 0.76, 0.80)
    col_markings = (0.92, 0.93, 0.96)
    col_bldg = (0.86, 0.87, 0.90)
    col_bridge = (0.78, 0.81, 0.86)
    col_prop = (0.70, 0.73, 0.78)
    col_hero_tone = (0.98, 0.98, 1.00)

    mat_road = make_clay_material("Clay_Road", col_road, roughness=0.85)
    mat_sidewalk = make_clay_material("Clay_Sidewalk", col_sidewalk, roughness=0.75)
    mat_markings = make_clay_material("Clay_Markings", col_markings, roughness=0.6)
    mat_bldg = make_clay_material("Clay_Building", col_bldg, roughness=0.68)
    mat_bridge = make_clay_material("Clay_Bridge", col_bridge, roughness=0.65)
    mat_prop = make_clay_material("Clay_Prop", col_prop, roughness=0.6)
    mat_hero = make_clay_material("Clay_Hero", col_hero_tone, roughness=0.45)

    # 1. Street Road & Sidewalks
    bm_road = bmesh.new()
    add_box(bm_road, (0.0, -16.0, -0.15), (9.0, 68.0, 0.30))
    finalize_mesh("Street_Road", bm_road, mat_road, col_road, col_env)

    bm_sw = bmesh.new()
    add_box(bm_sw, (-6.2, -16.0, 0.08), (3.6, 68.0, 0.16))
    add_box(bm_sw, (6.2, -16.0, 0.08), (3.6, 68.0, 0.16))
    # End plaza behind hero
    add_box(bm_sw, (0.0, 4.5, 0.04), (16.0, 12.0, 0.08))
    finalize_mesh("Street_Sidewalks", bm_sw, mat_sidewalk, col_sidewalk, col_env)

    bm_marks = bmesh.new()
    for y in range(-44, -4, 4):
        add_box(bm_marks, (0.0, float(y), 0.015), (0.18, 1.8, 0.03))
    for cx in (-3.2, -2.0, -0.8, 0.8, 2.0, 3.2):
        add_box(bm_marks, (cx, -3.5, 0.015), (0.55, 2.2, 0.03))
    finalize_mesh("Street_Markings", bm_marks, mat_markings, col_markings, col_env)

    # 2. Street Canyon Buildings (left & right blocks with tiered architecture)
    bldg_heights_L = [18.0, 13.0, 22.0, 15.0, 19.0, 11.5, 16.5, 14.0, 21.0, 12.5]
    bldg_heights_R = [15.5, 21.0, 14.0, 18.5, 12.0, 20.0, 13.5, 17.5, 15.0, 19.5]

    for idx, y in enumerate(range(-42, 12, 5)):
        for side, x_base, heights in (("L", -9.2, bldg_heights_L), ("R", 9.2, bldg_heights_R)):
            h = heights[idx % len(heights)]
            bm_b = bmesh.new()
            # Main tower mass
            add_box(bm_b, (x_base, float(y), h / 2.0), (4.4, 4.3, h))
            # Ground podium ledge
            podium_x = x_base + (0.6 if side == "L" else -0.6)
            add_box(bm_b, (podium_x, float(y), 1.8), (4.2, 4.5, 3.6))
            # Mid cornice & upper setback
            add_box(bm_b, (x_base, float(y), h * 0.65), (4.65, 4.55, 0.45))
            add_box(bm_b, (x_base, float(y), h + 1.4), (3.0, 3.0, 2.8))
            # Vertical facade pilasters for crisp speed parallax
            pil_x = x_base + (2.25 if side == "L" else -2.25)
            for dy in (-1.4, 0.0, 1.4):
                add_box(bm_b, (pil_x, float(y) + dy, h * 0.5), (0.28, 0.35, h))
            finalize_mesh(f"Bldg_{side}_{idx:02d}", bm_b, mat_bldg, col_bldg, col_bldgs, bevel_width=0.04)

    # 3. Overhead Skybridges (dramatic FPV dive landmarks) & Street Props
    skybridges = [
        ("Skybridge_High", -30.0, 12.0, 1.3),
        ("Skybridge_Mid", -18.0, 5.5, 1.1),
        ("Skybridge_Arch", -8.0, 4.3, 0.9),
    ]
    for name, by, bz, thick in skybridges:
        bm_br = bmesh.new()
        add_box(bm_br, (0.0, by, bz + thick / 2.0), (15.0, 2.2, thick))
        add_box(bm_br, (0.0, by, bz + thick + 0.5), (14.6, 1.6, 0.8))
        # Side support arches
        add_box(bm_br, (-6.2, by, (bz + thick) / 2.0), (0.7, 1.2, bz + thick))
        add_box(bm_br, (6.2, by, (bz + thick) / 2.0), (0.7, 1.2, bz + thick))
        finalize_mesh(name, bm_br, mat_bridge, col_bridge, col_props, bevel_width=0.03)

    # Streetlights & parked vehicle blockouts for foreground parallax
    bm_props = bmesh.new()
    for y in range(-38, 0, 7):
        for sx, dir_sign in ((-4.3, 1.0), (4.3, -1.0)):
            add_box(bm_props, (sx, float(y), 2.3), (0.14, 0.14, 4.6))
            add_box(bm_props, (sx + dir_sign * 0.55, float(y), 4.55), (1.15, 0.16, 0.14))
    for vy, vx in ((-32.0, -3.1), (-24.0, 3.1), (-14.0, -3.1), (-10.0, 3.1)):
        add_box(bm_props, (vx, vy, 0.42), (1.6, 3.6, 0.65))
        add_box(bm_props, (vx, vy - 0.15, 0.92), (1.4, 1.9, 0.48))
    finalize_mesh("Street_Props_Vehicles", bm_props, mat_prop, col_prop, col_props, bevel_width=0.025)

    # 4. Protagonist Mannequin ("Hero_Mannequin") at (0, 0, 0), facing -Y
    bm_hero = bmesh.new()
    # Hero pedestal disc
    add_cylinder(bm_hero, (0.0, 0.0, 0.06), radius=1.05, depth=0.12, segments=24)
    # Legs
    add_box(bm_hero, (-0.15, 0.0, 0.52), (0.18, 0.20, 0.82), rot_euler=(0.0, -0.06, 0.0))
    add_box(bm_hero, (0.15, 0.0, 0.52), (0.18, 0.20, 0.82), rot_euler=(0.0, 0.06, 0.0))
    # Pelvis & Torso
    add_box(bm_hero, (0.0, 0.0, 1.00), (0.38, 0.24, 0.22))
    add_box(bm_hero, (0.0, 0.0, 1.32), (0.48, 0.28, 0.46))
    # Shoulder pads & Arms in heroic ready pose
    add_box(bm_hero, (-0.33, 0.02, 1.48), (0.20, 0.24, 0.18))
    add_box(bm_hero, (0.33, 0.02, 1.48), (0.20, 0.24, 0.18))
    add_box(bm_hero, (-0.34, -0.06, 1.18), (0.15, 0.16, 0.52), rot_euler=(-0.18, 0.08, 0.0))
    add_box(bm_hero, (0.34, -0.06, 1.18), (0.15, 0.16, 0.52), rot_euler=(-0.18, -0.08, 0.0))
    # Neck & Head + Visor ridge
    add_cylinder(bm_hero, (0.0, 0.0, 1.60), radius=0.075, depth=0.14, segments=12)
    add_box(bm_hero, (0.0, 0.0, 1.76), (0.22, 0.25, 0.26))
    add_box(bm_hero, (0.0, -0.13, 1.78), (0.18, 0.05, 0.07))
    # Back blade / staff silhouette
    add_box(bm_hero, (0.05, 0.19, 1.38), (0.10, 0.06, 1.35), rot_euler=(0.0, 0.42, 0.0))
    finalize_mesh("Hero_Mannequin", bm_hero, mat_hero, col_hero_tone, col_hero, bevel_width=0.018)

    # 5. Bake 120-Frame FPV Camera Dive + Banking Trajectory (24 fps, 5.0 seconds)
    cam_data = bpy.data.cameras.new("Previs_FPV_Cam")
    cam_data.lens = 20.0
    cam_data.clip_start = 0.1
    cam_data.clip_end = 250.0
    cam = bpy.data.objects.new("Previs_FPV_Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    pos_ctrl = [
        Vector((0.0, -39.0, 14.5)),
        Vector((-0.9, -30.0, 8.6)),
        Vector((-1.6, -22.0, 3.6)),
        Vector((1.5, -15.0, 1.9)),
        Vector((-0.5, -7.5, 1.35)),
        Vector((0.0, -2.35, 1.52)),
    ]
    target_ctrl = [
        Vector((0.0, -14.0, 2.2)),
        Vector((-0.4, -10.0, 1.9)),
        Vector((0.3, -6.0, 1.6)),
        Vector((0.0, -2.0, 1.55)),
        Vector((0.0, 0.0, 1.55)),
        Vector((0.0, 0.0, 1.55)),
    ]

    total_frames = 120
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.fps = 24

    prev_x = pos_ctrl[0].x
    path_export = {
        "fps": 24,
        "totalFrames": total_frames,
        "fovDeg": round(math.degrees(cam_data.angle), 2),
        "frames": [],
    }

    for frame in range(1, total_frames + 1):
        u = (frame - 1) / float(total_frames - 1)
        # Mild ease at start & smooth deceleration approaching the protagonist
        u_eased = 0.85 * u + 0.15 * (u * u * (3.0 - 2.0 * u))
        cam_pos = eval_polyline_spline(pos_ctrl, u_eased)
        tgt_pos = eval_polyline_spline(target_ctrl, u_eased)

        vx = (cam_pos.x - prev_x) * 24.0
        prev_x = cam_pos.x

        # Banking envelope ramps up after launch and settles cleanly to 0 before hero close-up
        bank_env = smoothstep(0.05, 0.20, u) * (1.0 - smoothstep(0.72, 0.90, u))
        roll_rad = max(-0.36, min(0.36, -vx * 0.055)) * bank_env

        track_quat = (tgt_pos - cam_pos).to_track_quat("-Z", "Y")
        final_quat = track_quat @ Quaternion((0.0, 0.0, 1.0), roll_rad)

        cam.location = cam_pos
        cam.rotation_mode = "XYZ"
        cam.rotation_euler = final_quat.to_euler("XYZ")
        cam.keyframe_insert(data_path="location", frame=frame)
        cam.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Convert Blender (x, y, z) -> Three.js glTF (x, z, -y)
        path_export["frames"].append({
            "frame": frame,
            "pos": [round(cam_pos.x, 4), round(cam_pos.z, 4), round(-cam_pos.y, 4)],
            "target": [round(tgt_pos.x, 4), round(tgt_pos.z, 4), round(-tgt_pos.y, 4)],
            "roll": round(roll_rad, 5),
        })

    # 6. Render First Frame PNG, Last Frame PNG, and Full 120-frame H.264 MP4
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100

    im = scene.render.image_settings
    im.media_type = "IMAGE"
    im.file_format = "PNG"

    scene.frame_set(1)
    scene.render.filepath = FIRST_FRAME_PATH
    bpy.ops.render.render(write_still=True)

    scene.frame_set(total_frames)
    scene.render.filepath = LAST_FRAME_PATH
    bpy.ops.render.render(write_still=True)

    im.media_type = "VIDEO"
    im.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.filepath = MP4_PATH
    bpy.ops.render.render(animation=True)

    # 7. Save .blend, .glb, and camera trajectory JSON
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        export_apply=True,
        export_materials="EXPORT",
    )
    with open(CAM_PATH_JSON, "w", encoding="utf-8") as f:
        json.dump(path_export, f, ensure_ascii=False)

    print("SUCCESS_FPV_WHITE_MODEL")


if __name__ == "__main__":
    build_fpv_white_model()
