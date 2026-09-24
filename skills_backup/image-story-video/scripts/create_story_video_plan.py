#!/usr/bin/env python3
"""Scaffold an image-to-video storyboard package from a story file.

This script is deterministic and does not call image/video APIs.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？.!?])\s+|\n+", text.strip())
    cleaned = [p.strip() for p in parts if p.strip()]
    return cleaned or [text.strip() or "A quiet opening moment introduces the story."]


def pick_scene_text(sentences: list[str], scene_count: int, index: int) -> str:
    if not sentences:
        return "The story continues with a clear emotional beat."
    pos = round(index * (len(sentences) - 1) / max(scene_count - 1, 1))
    return sentences[pos]


def srt_time(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02},000"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", required=True, help="Path to UTF-8 story text.")
    parser.add_argument("--title", default="image-story-video")
    parser.add_argument("--scenes", type=int, default=6)
    parser.add_argument("--duration", type=int, default=30)
    parser.add_argument("--aspect", default="9:16")
    parser.add_argument("--style", default="warm cinematic documentary")
    parser.add_argument("--character-anchor", default="[same person from the reference photo, use only face identity, hairstyle, age impression, and facial expression; story-generated outfit, props, pose, background, and lighting]")
    parser.add_argument("--out", default="image-story-video-output")
    args = parser.parse_args()

    story_path = Path(args.story)
    story = story_path.read_text(encoding="utf-8") if story_path.exists() else args.story
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for folder in ["reference", "images", "video-clips", "audio", "final"]:
        (out / folder).mkdir(exist_ok=True)

    scenes = max(1, args.scenes)
    per_scene = max(1, round(args.duration / scenes))
    sentences = split_sentences(story)
    rows = []
    prompts = []

    for i in range(scenes):
        scene_id = f"scene-{i + 1:02}"
        beat = pick_scene_text(sentences, scenes, i)
        start = i * per_scene
        end = min(args.duration, start + per_scene)
        subtitle = beat[:38] + ("..." if len(beat) > 38 else "")
        image_prompt = (
            f"{args.character_anchor}, {beat}, still frame for a {args.aspect} video, "
            f"{args.style}, clean composition, do not copy original photo clothing or background, no text, no watermark"
        )
        video_prompt = (
            f"Using images/{scene_id}-still.png as reference, create a {per_scene}-second "
            f"smooth cinematic shot. Same character, same face, same hairstyle, same facial expression baseline, same story-generated outfit. "
            f"Action: subtle natural movement matching this beat: {beat}. "
            "Keep lighting, color palette, and location continuity. No scene cut, no face change, no expression drift, no accidental reuse of original photo clothing or background."
        )
        row = {
            "scene_id": scene_id,
            "duration_seconds": per_scene,
            "scene_goal": beat,
            "visual_description": beat,
            "image_file": f"images/{scene_id}-still.png",
            "video_file": f"video-clips/{scene_id}-clip.mp4",
            "image_prompt": image_prompt,
            "image_to_video_prompt": video_prompt,
            "camera_motion": "slow dolly-in or locked-off close-up",
            "narration": beat,
            "subtitle": subtitle,
            "transition_from_previous": "continue from previous final frame" if i else "opening reference shot",
            "quality_check": "same face and expression baseline, same story-generated outfit, stable hands, no original photo clothing/background, no text artifacts",
        }
        rows.append(row)
        prompts.append(row)

    with (out / "storyboard.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    (out / "prompts.json").write_text(
        json.dumps(
            {
                "title": args.title,
                "aspect": args.aspect,
                "duration_seconds": args.duration,
                "style_anchor": args.style,
                "character_anchor": args.character_anchor,
                "scenes": prompts,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (out / "narration.txt").write_text(
        "\n".join(f"{r['scene_id']}: {r['narration']}" for r in rows),
        encoding="utf-8",
    )

    srt_blocks = []
    for idx, r in enumerate(rows, 1):
        start = (idx - 1) * per_scene
        end = min(args.duration, start + per_scene)
        srt_blocks.append(f"{idx}\n{srt_time(start)} --> {srt_time(end)}\n{r['subtitle']}\n")
    (out / "subtitles.srt").write_text("\n".join(srt_blocks), encoding="utf-8")

    (out / "production-notes.md").write_text(
        f"""# {args.title}

## Next Steps

1. Put reference photos in `reference/`.
2. Generate stills from `prompts.json` into `images/`.
3. Generate clips from each still into `video-clips/`.
4. Assemble clips in scene order.
5. Add `subtitles.srt` and narration from `narration.txt`.

## Continuity Rule

Reuse the same face/expression character anchor and style anchor in every generation pass. The uploaded photo should guide face identity and facial expression only; clothing, props, pose, background, and lighting should come from the story unless explicitly requested.
Use the previous clip's final frame as the next reference when available.
""",
        encoding="utf-8",
    )

    print(json.dumps({"output": str(out.resolve()), "scenes": scenes}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
