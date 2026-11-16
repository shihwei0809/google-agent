import math
import os
import bpy
import bmesh
from mathutils import Vector

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(OUT_DIR, "warehouse_scene.blend")
GLB_PATH = os.path.join(OUT_DIR, "warehouse_3d.glb")


def make_material(name, base_color, metallic=0.1, roughness=0.5, emission_color=None, emission_strength=0.0):
    """Create a Blender Principled BSDF material compatible with Blender 4.x / 5.x."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")

    if "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = (*base_color[:3], 1.0)
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metallic
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = roughness

    if emission_color is not None and emission_strength > 0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission_color[:3], 1.0)
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (*emission_color[:3], 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def add_box_to_bmesh(bm, center, size, mat_index=0):
    """Add an axis-aligned box into a bmesh with the given material index."""
    sx, sy, sz = size
    cx, cy, cz = center
    ret = bmesh.ops.create_cube(bm, size=1.0)
    verts = ret["verts"]
    for v in verts:
        v.co.x = v.co.x * sx + cx
        v.co.y = v.co.y * sy + cy
        v.co.z = v.co.z * sz + cz

    vert_set = set(verts)
    for f in bm.faces:
        if all(v in vert_set for v in f.verts):
            f.material_index = mat_index


def create_mesh_object(name, bm, materials, collection, bevel_width=0.0):
    """Finalize a bmesh into a Blender mesh object linked to collection."""
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    for mat in materials:
        obj.data.materials.append(mat)
    collection.objects.link(obj)

    if bevel_width > 0:
        mod = obj.modifiers.new(name="Bevel", type="BEVEL")
        mod.width = bevel_width
        mod.segments = 2
        mod.limit_method = "ANGLE"
    return obj


def get_or_create_collection(name, parent=None):
    col = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(col)
    else:
        parent.children.link(col)
    return col


def build_warehouse_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    scene = bpy.context.scene
    # Select lightweight EEVEE engine suitable for integrated graphics (Intel Iris Xe)
    available_engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        if eng in available_engines:
            scene.render.engine = eng
            break

    # Collections
    col_env = get_or_create_collection("01_Environment")
    col_racks = get_or_create_collection("02_Racks")
    col_slots = get_or_create_collection("03_Slots")
    col_agv = get_or_create_collection("04_AGV_Robots")
    col_lights = get_or_create_collection("05_Lights_Camera")

    # Materials
    mat_floor = make_material("Mat_Floor", (0.045, 0.058, 0.082), metallic=0.12, roughness=0.42)
    mat_floor_grid = make_material("Mat_Floor_Line", (0.04, 0.55, 0.78), metallic=0.2, roughness=0.3,
                                   emission_color=(0.05, 0.65, 0.95), emission_strength=1.2)
    mat_aisle_stripe = make_material("Mat_Aisle_Stripe", (0.95, 0.68, 0.05), metallic=0.1, roughness=0.4,
                                     emission_color=(0.95, 0.68, 0.05), emission_strength=0.4)

    mat_upright = make_material("Mat_Rack_Upright", (0.07, 0.22, 0.52), metallic=0.78, roughness=0.32)
    mat_beam = make_material("Mat_Rack_Beam", (0.92, 0.34, 0.04), metallic=0.45, roughness=0.38)
    mat_shelf_deck = make_material("Mat_Shelf_Deck", (0.20, 0.23, 0.28), metallic=0.55, roughness=0.55)

    mat_pallet = make_material("Mat_Wood_Pallet", (0.52, 0.36, 0.19), metallic=0.0, roughness=0.78)
    mat_normal = make_material("Mat_Slot_Normal", (0.08, 0.68, 0.48), metallic=0.08, roughness=0.38)
    mat_full = make_material("Mat_Slot_Full", (0.92, 0.24, 0.18), metallic=0.12, roughness=0.35,
                             emission_color=(0.92, 0.20, 0.12), emission_strength=0.18)
    mat_low = make_material("Mat_Slot_Low", (0.95, 0.72, 0.10), metallic=0.08, roughness=0.38)
    mat_empty = make_material("Mat_Slot_Empty", (0.24, 0.29, 0.36), metallic=0.2, roughness=0.65)
    mat_cardboard = make_material("Mat_Cardboard_Band", (0.76, 0.62, 0.42), metallic=0.0, roughness=0.75)

    mat_agv_body = make_material("Mat_AGV_Body", (0.12, 0.15, 0.20), metallic=0.65, roughness=0.28)
    mat_agv_accent = make_material("Mat_AGV_Accent", (0.95, 0.42, 0.06), metallic=0.35, roughness=0.32)
    mat_agv_glow = make_material("Mat_AGV_Glow", (0.05, 0.85, 1.0), metallic=0.0, roughness=0.1,
                                 emission_color=(0.05, 0.90, 1.0), emission_strength=3.0)
    mat_wheel = make_material("Mat_Wheel", (0.03, 0.03, 0.035), metallic=0.1, roughness=0.8)

    # 1. Floor Platform + Aisle Markings
    bm_floor = bmesh.new()
    add_box_to_bmesh(bm_floor, (0.0, 0.0, -0.10), (16.5, 13.0, 0.20), mat_index=0)
    # Perimeter trim
    add_box_to_bmesh(bm_floor, (0.0, 6.45, 0.01), (16.5, 0.08, 0.02), mat_index=1)
    add_box_to_bmesh(bm_floor, (0.0, -6.45, 0.01), (16.5, 0.08, 0.02), mat_index=1)
    add_box_to_bmesh(bm_floor, (-8.20, 0.0, 0.01), (0.08, 13.0, 0.02), mat_index=1)
    add_box_to_bmesh(bm_floor, (8.20, 0.0, 0.01), (0.08, 13.0, 0.02), mat_index=1)
    # AGV guide path along Aisle 1 (y = -2.1) and Aisle 2 (y = 2.1)
    for ay in (-2.1, 2.1):
        add_box_to_bmesh(bm_floor, (0.0, ay, 0.004), (13.4, 0.09, 0.008), mat_index=1)
        add_box_to_bmesh(bm_floor, (0.0, ay - 0.85, 0.003), (13.0, 0.05, 0.006), mat_index=2)
        add_box_to_bmesh(bm_floor, (0.0, ay + 0.85, 0.003), (13.0, 0.05, 0.006), mat_index=2)
    create_mesh_object("Floor_Platform", bm_floor, [mat_floor, mat_floor_grid, mat_aisle_stripe], col_env)

    # 2. Rack Layout Definition (3 rows x 4 bays x 3 tiers = 36 slots)
    rows = [("A", -4.2), ("B", 0.0), ("C", 4.2)]
    bay_centers_x = [-4.5, -1.5, 1.5, 4.5]
    bay_width = 2.8
    rack_depth = 1.45
    tier_heights = [0.22, 1.62, 3.02]
    rack_total_h = 4.35

    # Deterministic realistic warehouse status map
    slot_states = {
        "A-01-1": "normal", "A-01-2": "full",   "A-01-3": "normal",
        "A-02-1": "full",   "A-02-2": "normal", "A-02-3": "low",
        "A-03-1": "normal", "A-03-2": "empty",  "A-03-3": "normal",
        "A-04-1": "low",    "A-04-2": "full",   "A-04-3": "empty",

        "B-01-1": "full",   "B-01-2": "full",   "B-01-3": "normal",
        "B-02-1": "normal", "B-02-2": "low",    "B-02-3": "normal",
        "B-03-1": "normal", "B-03-2": "normal", "B-03-3": "full",
        "B-04-1": "empty",  "B-04-2": "normal", "B-04-3": "low",

        "C-01-1": "normal", "C-01-2": "normal", "C-01-3": "empty",
        "C-02-1": "low",    "C-02-2": "normal", "C-02-3": "normal",
        "C-03-1": "full",   "C-03-2": "full",   "C-03-3": "low",
        "C-04-1": "normal", "C-04-2": "empty",  "C-04-3": "normal",
    }

    for row_label, ry in rows:
        bm_rack = bmesh.new()
        # Uprights (5 frames per 4-bay row)
        frame_xs = [bay_centers_x[0] - bay_width / 2.0] + [bx + bay_width / 2.0 for bx in bay_centers_x]
        for fx in frame_xs:
            for dy in (-rack_depth / 2.0, rack_depth / 2.0):
                add_box_to_bmesh(bm_rack, (fx, ry + dy, rack_total_h / 2.0), (0.09, 0.09, rack_total_h), mat_index=0)
                # Base footplate
                add_box_to_bmesh(bm_rack, (fx, ry + dy, 0.015), (0.18, 0.18, 0.03), mat_index=0)
            # Cross tie bars per frame
            for tz in (0.9, 2.3, 3.7):
                add_box_to_bmesh(bm_rack, (fx, ry, tz), (0.05, rack_depth, 0.05), mat_index=0)

        # Horizontal beams & deck plates
        for bx in bay_centers_x:
            for tz in tier_heights:
                for dy in (-rack_depth / 2.0, rack_depth / 2.0):
                    add_box_to_bmesh(bm_rack, (bx, ry + dy, tz), (bay_width - 0.08, 0.07, 0.11), mat_index=1)
                # Wire mesh / steel deck plate
                add_box_to_bmesh(bm_rack, (bx, ry, tz + 0.04), (bay_width - 0.14, rack_depth - 0.06, 0.03), mat_index=2)

        # Zone beacon pillar at left end of row
        add_box_to_bmesh(bm_rack, (-6.6, ry, 1.3), (0.18, 0.18, 2.6), mat_index=0)
        add_box_to_bmesh(bm_rack, (-6.6, ry, 2.68), (0.28, 0.28, 0.18), mat_index=1)

        create_mesh_object(
            f"Rack_{row_label}",
            bm_rack,
            [mat_upright, mat_beam, mat_shelf_deck],
            col_racks,
        )

        # 3. Create individual clickable Slot objects in this row
        for bay_idx, bx in enumerate(bay_centers_x, start=1):
            for tier_idx, tz in enumerate(tier_heights, start=1):
                slot_id = f"{row_label}-{bay_idx:02d}-{tier_idx}"
                state = slot_states.get(slot_id, "normal")
                bm_slot = bmesh.new()

                deck_top_z = tz + 0.055
                # Base pallet (always present as physical slot footprint)
                if state == "empty":
                    add_box_to_bmesh(bm_slot, (bx, ry, deck_top_z + 0.03), (2.15, 1.10, 0.06), mat_index=0)
                    slot_mats = [mat_empty]
                else:
                    # Wooden pallet
                    add_box_to_bmesh(bm_slot, (bx, ry, deck_top_z + 0.055), (2.10, 1.12, 0.11), mat_index=0)
                    pallet_top = deck_top_z + 0.11

                    if state == "full":
                        # Two tall stacked crates filling the bay
                        add_box_to_bmesh(bm_slot, (bx - 0.52, ry, pallet_top + 0.48), (0.92, 0.98, 0.96), mat_index=1)
                        add_box_to_bmesh(bm_slot, (bx + 0.52, ry, pallet_top + 0.48), (0.92, 0.98, 0.96), mat_index=1)
                        add_box_to_bmesh(bm_slot, (bx - 0.52, ry, pallet_top + 0.48), (0.95, 0.30, 0.22), mat_index=2)
                        add_box_to_bmesh(bm_slot, (bx + 0.52, ry, pallet_top + 0.48), (0.95, 0.30, 0.22), mat_index=2)
                        slot_mats = [mat_pallet, mat_full, mat_cardboard]
                    elif state == "low":
                        # One smaller partial crate
                        add_box_to_bmesh(bm_slot, (bx - 0.38, ry, pallet_top + 0.28), (0.96, 0.90, 0.56), mat_index=1)
                        add_box_to_bmesh(bm_slot, (bx - 0.38, ry, pallet_top + 0.28), (0.99, 0.28, 0.18), mat_index=2)
                        slot_mats = [mat_pallet, mat_low, mat_cardboard]
                    else:  # normal
                        # Two medium standard crates
                        add_box_to_bmesh(bm_slot, (bx - 0.50, ry, pallet_top + 0.38), (0.88, 0.94, 0.76), mat_index=1)
                        add_box_to_bmesh(bm_slot, (bx + 0.50, ry, pallet_top + 0.32), (0.88, 0.94, 0.64), mat_index=1)
                        add_box_to_bmesh(bm_slot, (bx - 0.50, ry, pallet_top + 0.38), (0.91, 0.26, 0.18), mat_index=2)
                        slot_mats = [mat_pallet, mat_normal, mat_cardboard]

                create_mesh_object(f"Slot_{slot_id}", bm_slot, slot_mats, col_slots, bevel_width=0.015)

    # 4. AGV Smart Robot in Aisle 1
    bm_agv = bmesh.new()
    ax, ay = -1.5, -2.1
    # Main chassis
    add_box_to_bmesh(bm_agv, (ax, ay, 0.20), (1.35, 0.92, 0.26), mat_index=0)
    # Orange bumper / accent frame
    add_box_to_bmesh(bm_agv, (ax, ay, 0.14), (1.40, 0.96, 0.08), mat_index=1)
    # Glowing cyan LED light strips & LiDAR sensor
    add_box_to_bmesh(bm_agv, (ax + 0.68, ay, 0.25), (0.04, 0.76, 0.05), mat_index=2)
    add_box_to_bmesh(bm_agv, (ax - 0.68, ay, 0.25), (0.04, 0.76, 0.05), mat_index=2)
    add_box_to_bmesh(bm_agv, (ax + 0.45, ay, 0.38), (0.16, 0.16, 0.10), mat_index=2)
    # Wheels
    for wx in (-0.42, 0.42):
        for wy in (-0.42, 0.42):
            add_box_to_bmesh(bm_agv, (ax + wx, ay + wy, 0.07), (0.22, 0.10, 0.14), mat_index=3)
    # Cargo payload carried by AGV
    add_box_to_bmesh(bm_agv, (ax - 0.08, ay, 0.37), (0.85, 0.78, 0.08), mat_index=4)
    add_box_to_bmesh(bm_agv, (ax - 0.08, ay, 0.66), (0.76, 0.70, 0.50), mat_index=5)
    create_mesh_object(
        "AGV_Robot_01",
        bm_agv,
        [mat_agv_body, mat_agv_accent, mat_agv_glow, mat_wheel, mat_pallet, mat_normal],
        col_agv,
        bevel_width=0.012,
    )

    # 5. Lighting & Camera for Blender GUI inspection
    sun_data = bpy.data.lights.new(name="Main_Sun", type="SUN")
    sun_data.energy = 2.4
    sun_obj = bpy.data.objects.new(name="Main_Sun", object_data=sun_data)
    sun_obj.rotation_euler = (math.radians(48), math.radians(15), math.radians(-35))
    col_lights.objects.link(sun_obj)

    area_data = bpy.data.lights.new(name="Overhead_Area", type="AREA")
    area_data.energy = 450.0
    area_data.size = 10.0
    area_obj = bpy.data.objects.new(name="Overhead_Area", object_data=area_data)
    area_obj.location = (0.0, 0.0, 9.5)
    col_lights.objects.link(area_obj)

    cam_data = bpy.data.cameras.new(name="Warehouse_Cam")
    cam_obj = bpy.data.objects.new(name="Warehouse_Cam", object_data=cam_data)
    cam_obj.location = (11.5, -10.5, 8.2)
    direction = Vector((0.0, 0.0, 1.5)) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    col_lights.objects.link(cam_obj)
    scene.camera = cam_obj

    # World background color
    if scene.world is None:
        scene.world = bpy.data.worlds.new("WarehouseWorld")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.025, 0.035, 0.055, 1.0)
        bg.inputs["Strength"].default_value = 0.8

    # Save .blend and export .glb
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        export_apply=True,
        export_materials="EXPORT",
    )
    print(f"SUCCESS: Saved {BLEND_PATH} and exported {GLB_PATH}")


if __name__ == "__main__":
    build_warehouse_scene()
