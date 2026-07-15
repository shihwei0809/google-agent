---
name: ai-video-generator-project
description: Scaffold or adapt a reusable Python project that accepts a topic, scene, and character; generates storyboard images with the OpenAI Image API; combines them into an FFmpeg video with SRT subtitles and background music; uploads the MP4 to Google Drive; and returns a shareable link. Use when Codex needs to create, templatize, or generalize an AI image-to-video automation service for local or cloud deployment.
---

# AI Video Generator Project

Use this skill to create a reusable starter project for AI-driven image-to-video automation.

## Workflow

1. Confirm whether the user wants a new scaffold or wants to adapt an existing Python project.
2. For a new scaffold, copy `assets/project-template/` into the target directory with `scripts/scaffold_project.py`.
3. Update `.env`, branding text, prompt logic, and deployment settings based on the user's stack and runtime constraints.
4. Keep the core pipeline intact unless the user explicitly asks to swap providers:
   - FastAPI form input
   - OpenAI image generation
   - SRT subtitle generation
   - FFmpeg video rendering
   - Google Drive upload
5. Read [references/customization.md](references/customization.md) when you need the expected configuration points, required secrets, or deployment notes.
6. After scaffolding or adapting, validate by checking imports, environment files, and FFmpeg availability. Run lightweight verification before attempting full media generation.

## Scaffold

Run the scaffold script instead of manually recreating the same boilerplate:

```bash
python skills/ai-video-generator-project/scripts/scaffold_project.py --target <target-dir>
```

Useful flags:

- `--force`: overwrite an existing target directory
- `--project-name`: replace the default display name in `.env.example`

## Adaptation Rules

- Preserve modular separation between API, config, services, and utilities.
- Keep environment-bound secrets in `.env` or secret managers, never inline in source.
- Fail early when `background_music.mp3`, Google Drive credentials, or required env vars are missing.
- Treat image generation count, seconds per image, and storage destination as configuration, not hardcoded business logic.
- If the user wants another storage backend, adapt only the upload service and keep the rest of the pipeline stable.

## Resources

- `scripts/scaffold_project.py`: copy the reusable starter into a destination folder
- `references/customization.md`: required secrets, folders, runtime expectations, and customization points
- `assets/project-template/`: reusable FastAPI + OpenAI + FFmpeg + Google Drive project template
