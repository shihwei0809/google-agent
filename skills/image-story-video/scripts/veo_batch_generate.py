#!/usr/bin/env python3
"""Submit image-to-video scenes to Google Veo on Vertex AI and assemble clips.

This script uses gcloud Application Default Credentials and does not print
tokens, image base64, or returned video base64.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


def access_token(gcloud: str) -> str:
    result = subprocess.run(
        [gcloud, "auth", "application-default", "print-access-token"],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def post_json(url: str, payload: dict, token: str) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def redacted_status(status: dict) -> dict:
    compact = json.loads(json.dumps(status))
    for video in compact.get("response", {}).get("videos", []):
        if "bytesBase64Encoded" in video:
            video["bytesBase64Encoded"] = "<redacted video bytes>"
    return compact


def scene_prompt(scene: dict) -> str:
    return (
        scene.get("image_to_video_prompt")
        or scene.get("video_prompt")
        or scene.get("prompt")
        or scene.get("visual_description")
        or scene.get("scene_goal")
        or "Create a short realistic image-to-video clip with stable character continuity."
    )


def load_scenes(plan_path: Path) -> list[dict]:
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("prompts.json must contain a non-empty scenes array")
    return scenes


def submit_scene(scene: dict, args: argparse.Namespace, token: str, base_url: str) -> str:
    scene_id = scene.get("scene_id") or scene.get("id")
    if not scene_id:
        raise ValueError("Every scene needs scene_id or id")
    image_rel = scene.get("image_file") or f"images/{scene_id}-still.png"
    image_path = (args.root / image_rel).resolve()
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    payload = {
        "instances": [
            {
                "prompt": scene_prompt(scene),
                "image": {
                    "bytesBase64Encoded": image_b64,
                    "mimeType": args.mime_type,
                },
            }
        ],
        "parameters": {
            "aspectRatio": args.aspect,
            "durationSeconds": args.duration,
            "sampleCount": 1,
            "personGeneration": args.person_generation,
            "enhancePrompt": args.enhance_prompt,
        },
    }
    redacted = json.loads(json.dumps(payload))
    redacted["instances"][0]["image"]["bytesBase64Encoded"] = "<redacted base64 image>"
    write_json(args.veo_dir / f"{scene_id}-request-redacted.json", redacted)

    response = post_json(f"{base_url}:predictLongRunning", payload, token)
    write_json(args.veo_dir / f"{scene_id}-submit-response.json", response)
    op_name = response.get("name")
    if not op_name:
        raise RuntimeError(f"No operation name returned for {scene_id}")
    print(f"{scene_id} submitted")
    return op_name


def poll_scene(scene: dict, operation_name: str, args: argparse.Namespace, token: str, base_url: str) -> Path:
    scene_id = scene.get("scene_id") or scene.get("id")
    payload = {"operationName": operation_name}
    status_path = args.veo_dir / f"{scene_id}-operation-status.json"
    for attempt in range(1, args.max_polls + 1):
        time.sleep(args.poll_seconds)
        status = post_json(f"{base_url}:fetchPredictOperation", payload, token)
        write_json(status_path, redacted_status(status))
        print(f"{scene_id} poll={attempt} done={status.get('done', False)}")
        if status.get("done"):
            if "error" in status:
                raise RuntimeError(f"{scene_id} failed: {status['error']}")
            videos = status.get("response", {}).get("videos", [])
            if not videos:
                raise RuntimeError(f"{scene_id} returned no video")
            clip_name = Path(scene.get("video_file") or f"video-clips/{scene_id}-veo.mp4").name
            if not clip_name.endswith(".mp4"):
                clip_name = f"{scene_id}-veo.mp4"
            if not clip_name.endswith("-veo.mp4"):
                clip_name = clip_name.replace(".mp4", "-veo.mp4")
            clip_path = args.clips_dir / clip_name
            clip_path.write_bytes(base64.b64decode(videos[0]["bytesBase64Encoded"]))
            return clip_path
    raise TimeoutError(f"{scene_id} did not finish")


def find_ffmpeg() -> str:
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def concat_clips(clips: list[Path], args: argparse.Namespace) -> None:
    concat_file = args.veo_dir / "concat-list.txt"
    lines = []
    for clip in clips:
        safe_path = clip.resolve().as_posix().replace("'", "'\\''")
        lines.append(f"file '{safe_path}'")
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ffmpeg = args.ffmpeg or find_ffmpeg()
    args.final_video.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(args.final_video),
    ]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode == 0:
        return

    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        str(args.final_video),
    ]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path, help="Path to prompts.json.")
    parser.add_argument("--root", required=True, type=Path, help="Production package root.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--location", default="us-central1")
    parser.add_argument("--model", default="veo-3.1-fast-generate-001")
    parser.add_argument("--gcloud", default=r"C:\Users\C606\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd")
    parser.add_argument("--aspect", default="9:16")
    parser.add_argument("--duration", type=int, default=4)
    parser.add_argument("--mime-type", default="image/png")
    parser.add_argument("--person-generation", default="allow_adult")
    parser.add_argument("--enhance-prompt", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--max-polls", type=int, default=60)
    parser.add_argument("--ffmpeg", default="")
    parser.add_argument("--final-name", default="final-veo.mp4")
    args = parser.parse_args()

    args.root = args.root.resolve()
    args.plan = args.plan.resolve()
    args.veo_dir = args.root / "veo-batch"
    args.clips_dir = args.root / "video-clips"
    args.final_video = args.root / "final" / args.final_name
    args.veo_dir.mkdir(parents=True, exist_ok=True)
    args.clips_dir.mkdir(parents=True, exist_ok=True)
    args.final_video.parent.mkdir(parents=True, exist_ok=True)

    scenes = load_scenes(args.plan)
    token = access_token(args.gcloud)
    base_url = (
        f"https://{args.location}-aiplatform.googleapis.com/v1/projects/{args.project}"
        f"/locations/{args.location}/publishers/google/models/{args.model}"
    )
    operations_path = args.veo_dir / "operations.json"
    operations: dict[str, str] = {}
    if operations_path.exists():
        operations = json.loads(operations_path.read_text(encoding="utf-8"))

    for scene in scenes:
        scene_id = scene.get("scene_id") or scene.get("id")
        if scene_id not in operations:
            operations[scene_id] = submit_scene(scene, args, token, base_url)
            write_json(operations_path, operations)

    clips: list[Path] = []
    for scene in scenes:
        scene_id = scene.get("scene_id") or scene.get("id")
        existing = sorted(args.clips_dir.glob(f"{scene_id}*-veo.mp4"))
        clip = existing[0] if existing else poll_scene(scene, operations[scene_id], args, token, base_url)
        clips.append(clip)

    concat_clips(clips, args)
    print(json.dumps(
        {
            "final": str(args.final_video.resolve()),
            "clips": [str(c.resolve()) for c in clips],
            "scene_count": len(clips),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
