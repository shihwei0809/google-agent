r"""
MV 專用 Blender 白模多運鏡模板產生器 (Headless BLENDER_WORKBENCH)
=================================================================
支援 4 種 MV 高價值運鏡預設，直接輸出首幀、尾幀 PNG、白模預覽 MP4 與軌跡 JSON，
可直接送入 Google Flow (Frames to Video) 或作為 MV storyboard 參考構圖。

用法（須透過 Blender CLI 呼叫，注意 `--` 分隔符）：
  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b -P generate_mv_white_models.py -- --preset orbit_stage
  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b -P generate_mv_white_models.py -- --preset all --out mv_white_models
  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b -P generate_mv_white_models.py -- --preset dolly_zoom --frames 96 --no-mp4

可用預設 (--preset)：
  - orbit_stage    : 180° 舞台環繞運鏡（副歌大景）
  - dolly_zoom     : 希區考克變焦 Vertigo（情緒爆發 / 橋段轉折）
  - top_down_dive  : 高空垂直俯衝拉平（Intro / Drop）
  - low_angle_push : 低角度貼地仰拍推進（主歌氣勢進場）
  - all            : 一次產生以上 4 種預設
"""

import argparse
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Vector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser(description="MV White-Model Camera Presets")
    parser.add_argument(
        "--preset",
        default="orbit_stage",
        choices=["orbit_stage", "dolly_zoom", "top_down_dive", "low_angle_push", "all"],
        help="運鏡模板名稱",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(BASE_DIR, "mv_white_models"),
        help="輸出資料夾路徑",
    )
    parser.add_argument("--frames", type=int, default=72, help="總格數（24fps，預設 72 格 = 3 秒）")
    parser.add_argument("--no-mp4", action="store_true", help="只算首尾幀 PNG，略過 MP4（極速模式）")
    return parser.parse_args(argv)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "OBJECT"
    scene.display.shading.show_shadows = True
    scene.display.shading.shadow_intensity = 0.62
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.cavity_ridge_factor = 0.8
    scene.display.shading.cavity_valley_factor = 0.8
    if hasattr(scene.display.shading, "studio_light"):
        scene.display.shading.studio_light = "studio.sl"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    return scene


def add_box(bm, center, size, rot_euler=(0.0, 0.0, 0.0)):
    sx, sy, sz = size
    cx, cy, cz = center
    ret = bmesh.ops.create_cube(bm, size=1.0)
    verts = ret["verts"]
    for v in verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    if any(abs(a) > 1e-6 for a in rot_euler):
        rot_mat = Euler(rot_euler, "XYZ").to_matrix()
        bmesh.ops.rotate(bm, verts=verts, cent=(0.0, 0.0, 0.0), matrix=rot_mat)
    for v in verts:
        v.co.x += cx
        v.co.y += cy
        v.co.z += cz


def add_cylinder(bm, center, radius, depth, segments=24):
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


def finalize_mesh(name, bm, color, collection, bevel=0.0):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.color = (*color[:3], 1.0)
    collection.objects.link(obj)
    if bevel > 0:
        mod = obj.modifiers.new(name="Bevel", type="BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    return obj


def build_hero_figure(collection, origin=(0.0, 0.0, 0.0)):
    ox, oy, oz = origin
    bm = bmesh.new()
    add_cylinder(bm, (ox, oy, oz + 0.06), radius=0.9, depth=0.12, segments=28)
    add_box(bm, (ox - 0.14, oy, oz + 0.52), (0.16, 0.18, 0.80))
    add_box(bm, (ox + 0.14, oy, oz + 0.52), (0.16, 0.18, 0.80))
    add_box(bm, (ox, oy, oz + 1.00), (0.36, 0.22, 0.22))
    add_box(bm, (ox, oy, oz + 1.32), (0.44, 0.25, 0.46))
    add_box(bm, (ox - 0.31, oy, oz + 1.24), (0.14, 0.16, 0.52), rot_euler=(0.0, 0.08, 0.0))
    add_box(bm, (ox + 0.31, oy, oz + 1.24), (0.14, 0.16, 0.52), rot_euler=(0.0, -0.08, 0.0))
    add_cylinder(bm, (ox, oy, oz + 1.60), radius=0.07, depth=0.14, segments=12)
    add_box(bm, (ox, oy, oz + 1.76), (0.20, 0.22, 0.24))
    finalize_mesh("Hero_Mannequin", bm, (0.94, 0.90, 0.84), collection, bevel=0.015)


def build_stage_environment(collection):
    # 地板與圓形舞台
    bm_floor = bmesh.new()
    add_box(bm_floor, (0.0, 0.0, -0.15), (90.0, 90.0, 0.30))
    add_cylinder(bm_floor, (0.0, 0.0, 0.10), radius=4.2, depth=0.20, segments=48)
    add_cylinder(bm_floor, (0.0, 0.0, 0.04), radius=6.4, depth=0.08, segments=48)
    finalize_mesh("Stage_Floor", bm_floor, (0.76, 0.78, 0.82), collection)

    # 環形柱陣 / 空間透視參照物
    bm_pillars = bmesh.new()
    for i in range(12):
        ang = (2.0 * math.pi * i) / 12.0
        r = 10.5
        px, py = r * math.cos(ang), r * math.sin(ang)
        h = 6.0 + (i % 3) * 1.8
        add_box(bm_pillars, (px, py, h * 0.5), (0.85, 0.85, h), rot_euler=(0.0, 0.0, ang))
    # 遠景城市/背景方塊群，強化 Dolly Zoom 與俯衝視差
    for k in range(-4, 5):
        if k == 0:
            continue
        add_box(bm_pillars, (k * 4.5, 18.0 + abs(k) * 1.5, 4.5 + abs(k)), (2.6, 2.6, 9.0 + abs(k) * 2.0))
        add_box(bm_pillars, (k * 4.5, -18.0 - abs(k) * 1.5, 4.0 + abs(k)), (2.6, 2.6, 8.0 + abs(k) * 2.0))
    finalize_mesh("Stage_Pillars", bm_pillars, (0.86, 0.87, 0.90), collection, bevel=0.03)


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def animate_camera(scene, preset, total_frames):
    cam_data = bpy.data.cameras.new(f"MV_{preset}_Cam")
    cam_data.clip_start = 0.1
    cam_data.clip_end = 300.0
    cam = bpy.data.objects.new(f"MV_{preset}_Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.fps = 24

    target_base = Vector((0.0, 0.0, 1.35))
    frames_meta = []

    for frame in range(1, total_frames + 1):
        u = (frame - 1) / float(max(1, total_frames - 1))
        ue = 0.25 * u + 0.75 * smoothstep(u)

        if preset == "orbit_stage":
            # 從正面偏右環繞 180 度至左側，微升仰角
            theta = -0.5 * math.pi + math.pi * ue
            radius = 5.4 - 0.8 * math.sin(math.pi * ue)
            cam_pos = Vector((radius * math.cos(theta), radius * math.sin(theta), 1.55 + 0.9 * ue))
            tgt_pos = target_base
            lens = 28.0
        elif preset == "dolly_zoom":
            # 希區考克變焦：焦距 24mm -> 85mm，距離等比例後退維持主角高度
            lens_start, lens_end = 24.0, 85.0
            lens = lens_start + (lens_end - lens_start) * ue
            dist_start = 3.2
            dist = dist_start * (lens / lens_start)
            cam_pos = Vector((0.0, -dist, 1.42))
            tgt_pos = Vector((0.0, 0.0, 1.38))
        elif preset == "top_down_dive":
            # 高空 Z=24m 垂直俯衝並弧線拉平至平視中景
            z = 24.0 * ((1.0 - ue) ** 1.8) + 1.48
            y = -0.6 - 3.6 * smoothstep(ue)
            cam_pos = Vector((0.0, y, z))
            tgt_pos = Vector((0.0, 0.0, 1.35))
            lens = 24.0 + 11.0 * ue
        elif preset == "low_angle_push":
            # 低角度貼地 0.35m 推近仰拍，強化主角氣勢
            y = -11.5 + 8.6 * ue
            z = 0.38 + 0.85 * (ue ** 1.5)
            cam_pos = Vector((0.0, y, z))
            tgt_pos = Vector((0.0, 0.0, 1.52))
            lens = 22.0
        else:
            raise ValueError(f"Unknown preset: {preset}")

        cam_data.lens = lens
        cam_data.keyframe_insert(data_path="lens", frame=frame)

        track_quat = (tgt_pos - cam_pos).to_track_quat("-Z", "Y")
        cam.location = cam_pos
        cam.rotation_mode = "XYZ"
        cam.rotation_euler = track_quat.to_euler("XYZ")
        cam.keyframe_insert(data_path="location", frame=frame)
        cam.keyframe_insert(data_path="rotation_euler", frame=frame)

        frames_meta.append(
            {
                "frame": frame,
                "lens_mm": round(lens, 2),
                "pos": [round(cam_pos.x, 4), round(cam_pos.z, 4), round(-cam_pos.y, 4)],
                "target": [round(tgt_pos.x, 4), round(tgt_pos.z, 4), round(-tgt_pos.y, 4)],
            }
        )

    return cam_data, frames_meta


def render_preset(preset, out_dir, total_frames, no_mp4):
    os.makedirs(out_dir, exist_ok=True)
    scene = reset_scene()
    col = bpy.data.collections.new("MV_Stage")
    scene.collection.children.link(col)

    build_stage_environment(col)
    build_hero_figure(col, origin=(0.0, 0.0, 0.20))
    _, frames_meta = animate_camera(scene, preset, total_frames)

    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100

    first_png = os.path.join(out_dir, f"{preset}_first_frame.png")
    last_png = os.path.join(out_dir, f"{preset}_last_frame.png")
    mp4_path = os.path.join(out_dir, f"{preset}.mp4")
    json_path = os.path.join(out_dir, f"{preset}_camera_path.json")

    im = scene.render.image_settings
    im.media_type = "IMAGE"
    im.file_format = "PNG"

    scene.frame_set(1)
    scene.render.filepath = first_png
    bpy.ops.render.render(write_still=True)

    scene.frame_set(total_frames)
    scene.render.filepath = last_png
    bpy.ops.render.render(write_still=True)

    if not no_mp4:
        im.media_type = "VIDEO"
        im.file_format = "FFMPEG"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        scene.render.ffmpeg.constant_rate_factor = "HIGH"
        scene.render.ffmpeg.ffmpeg_preset = "GOOD"
        scene.render.filepath = mp4_path
        bpy.ops.render.render(animation=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"preset": preset, "fps": 24, "totalFrames": total_frames, "frames": frames_meta}, f, ensure_ascii=False)

    print(f"[OK] {preset} -> {first_png}, {last_png}")


def main():
    args = parse_args()
    presets = (
        ["orbit_stage", "dolly_zoom", "top_down_dive", "low_angle_push"]
        if args.preset == "all"
        else [args.preset]
    )
    for p in presets:
        render_preset(p, args.out, args.frames, args.no_mp4)
    print("SUCCESS_MV_WHITE_MODELS")


if __name__ == "__main__":
    main()
