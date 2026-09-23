# Veo / Vertex AI Bulk Generation

Use this reference when the user wants true motion video instead of a local
Ken Burns / slideshow-style edit.

## Capability Boundary

Codex can plan, submit, poll, download, and assemble Veo clips when Google Cloud
credentials are available. Veo generation itself is a Google Cloud billable
service. Local Codex does not generate true human motion without an external
video model.

## Required Setup

- Google Cloud CLI is installed.
- `gcloud auth login` has authenticated the user.
- `gcloud auth application-default login` has created ADC credentials.
- `gcloud config set project PROJECT_ID` points to the intended project.
- Billing is enabled for the project.
- Vertex AI API is enabled:

```powershell
gcloud services enable aiplatform.googleapis.com
```

If the API returns `BILLING_DISABLED`, link a billing account or ask the user to
enable billing in Google Cloud Console before retrying. If the API returns model,
quota, location, or permission errors, report the exact blocker and do not keep
retrying blindly.

## Recommended Defaults

- Model: `veo-3.1-fast-generate-001` for low-cost iteration.
- Location: `us-central1` unless the user's project requires another region.
- Aspect ratio: `9:16` for Shorts/Reels/TikTok.
- Scene duration: 4 seconds for smoke tests; adjust only after confirming cost.
- `personGeneration`: `allow_adult` for adult real-person references.
- `sampleCount`: `1` for cost control.
- `enhancePrompt`: `true` unless the user asks for literal prompt adherence.

## Cost Discipline

Before submitting a batch, state that Veo is billable and that cost usually
scales with generated seconds. Prefer a one-scene smoke test before generating a
full batch for a new project, region, model, or account.

Do not print access tokens, refresh tokens, image base64, or returned video
base64. Save redacted JSON request/status files.

## Production Flow

1. Build or load `prompts.json`.
2. Ensure every scene has:
   - `scene_id`
   - `image_file`
   - `video_file` or a predictable output name
   - `image_to_video_prompt`
3. Confirm scene stills exist under `images/`.
4. Run `scripts/veo_batch_generate.py`.
5. Check each clip for face drift, outfit drift, hand artifacts, unsafe imagery,
   and ignored camera motion.
6. Assemble clips into `final/`.
7. Report final path, total duration, resolution, codec, and any failed scenes.

## Prompt Rules for Veo

Each scene prompt should contain:

- one camera move
- one actor action
- the continuity anchor: same face, same expression baseline, same
  story-generated outfit
- safety and text negatives: no readable text, no logo, no disaster

Avoid asking one clip to do many story beats. If the clip must show complex
action, split it into multiple scenes.
