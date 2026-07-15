# Customization Guide

## Required Inputs

The template expects three user inputs:

- `topic`
- `scene`
- `character`

These arrive through the FastAPI form endpoint and are validated with Pydantic.

## Required Runtime Dependencies

- Python 3.11+
- FFmpeg and FFprobe
- OpenAI API key
- Google Drive service account JSON
- Background music file at `assets/background_music.mp3`

## Required Environment Variables

- `OPENAI_API_KEY`
- `OPENAI_IMAGE_MODEL`
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_DRIVE_FOLDER_ID`
- `FFMPEG_PATH`
- `FFPROBE_PATH`
- `IMAGE_COUNT`
- `SECONDS_PER_IMAGE`
- `BACKGROUND_MUSIC_PATH`

## Customization Points

### Prompt Generation

Adjust `app/services/openai_service.py` when the user wants:

- a different frame count
- stronger continuity between frames
- extra prompt style controls
- a separate text-model step for storyboard planning

### Subtitle Strategy

Adjust `app/services/subtitle_service.py` when subtitles should:

- come from generated narration
- use multilingual content
- include timestamps that differ from per-frame duration

### Video Rendering

Adjust `app/services/video_service.py` when the user wants:

- different codecs
- transitions between images
- voice-over audio mixing
- watermarking or logo overlays

### Storage Backend

Adjust `app/services/drive_service.py` when replacing Google Drive with:

- S3
- Azure Blob
- local-only output
- another cloud storage provider

## Validation Checklist

Before full end-to-end generation:

1. Verify imports or run `python -m compileall`.
2. Verify `ffmpeg` and `ffprobe` commands.
3. Confirm `.env` exists and points to real secrets.
4. Confirm the Google Drive credential file exists.
5. Confirm the background music file exists.
6. Start the FastAPI service and load the form page.
