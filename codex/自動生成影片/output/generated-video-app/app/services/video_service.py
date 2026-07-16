import math
from pathlib import Path

from app.core.config import settings
from app.models.schemas import StoryboardFrame
from app.utils.command_utils import run_command


class VideoService:
    """Render a storyboard-driven MP4 with motion, burnt-in subtitles, and audio."""

    def create_video_from_images(
        self,
        frames: list[StoryboardFrame],
        image_paths: list[Path],
        subtitle_path: Path,
        background_music_path: Path,
        work_dir: Path,
    ) -> Path:
        if not image_paths:
            raise ValueError("找不到可用圖片，無法合成影片。")
        if len(frames) != len(image_paths):
            raise ValueError("分鏡資料與圖片數量不一致，無法合成影片。")
        if not subtitle_path.exists():
            raise FileNotFoundError(f"字幕檔不存在: {subtitle_path}")

        clip_paths = self._render_motion_clips(frames, image_paths, work_dir)
        video_only_path = self._concat_video_clips(clip_paths, work_dir / "video_no_audio.mp4")

        generated_audio = work_dir / "generated_soundtrack.wav"
        self.create_storyboard_audio(frames, generated_audio)

        final_audio = generated_audio
        if background_music_path.exists():
            mixed_audio = work_dir / "mixed_soundtrack.wav"
            self._mix_audio_tracks(generated_audio, background_music_path, mixed_audio)
            final_audio = mixed_audio

        final_video = work_dir / "final_video.mp4"
        run_command(
            [
                settings.ffmpeg_path,
                "-y",
                "-i",
                str(video_only_path),
                "-i",
                str(final_audio),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(final_video),
            ]
        )
        return final_video

    def create_silent_audio(self, output_path: Path, duration_seconds: int) -> Path:
        run_command(
            [
                settings.ffmpeg_path,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=stereo",
                "-t",
                str(duration_seconds),
                "-q:a",
                "9",
                "-acodec",
                "libmp3lame",
                str(output_path),
            ]
        )
        return output_path

    def create_storyboard_audio(
        self,
        frames: list[StoryboardFrame],
        output_path: Path,
    ) -> Path:
        segment_files: list[Path] = []
        for frame in frames:
            segment_path = output_path.parent / f"audio_{frame.index:03d}.wav"
            filter_expr = self._build_audio_filter(frame)
            run_command(
                [
                    settings.ffmpeg_path,
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    filter_expr,
                    "-t",
                    str(frame.duration_seconds),
                    str(segment_path),
                ]
            )
            segment_files.append(segment_path)

        concat_file = output_path.parent / "audio_segments.txt"
        concat_file.write_text(
            "\n".join(f"file '{path.resolve().as_posix()}'" for path in segment_files),
            encoding="utf-8",
        )
        run_command(
            [
                settings.ffmpeg_path,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(output_path),
            ]
        )
        return output_path

    def _render_motion_clips(
        self,
        frames: list[StoryboardFrame],
        image_paths: list[Path],
        work_dir: Path,
    ) -> list[Path]:
        clip_paths: list[Path] = []

        for frame, image_path in zip(frames, image_paths, strict=False):
            clip_path = work_dir / f"clip_{frame.index:03d}.mp4"
            text_path = work_dir / f"subtitle_{frame.index:03d}.txt"
            fps = 30
            total_frames = max(1, math.ceil(frame.duration_seconds * fps))
            zoom_expr, x_expr, y_expr = self._motion_expressions(frame)

            text_path.write_text(frame.subtitle_text, encoding="utf-8")
            subtitle_textfile = text_path.as_posix()

            vf = (
                "scale=1920:1080:force_original_aspect_ratio=increase,"
                "crop=1920:1080,"
                f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
                f"d={total_frames}:s=1920x1080:fps={fps},"
                "drawbox=x=80:y=890:w=1760:h=110:color=black@0.45:t=fill,"
                f"drawtext=fontfile='C\\:/Windows/Fonts/msjh.ttc':textfile='{subtitle_textfile}':"
                "fontcolor=white:fontsize=38:line_spacing=8:"
                "x=(w-text_w)/2:y=h-135"
            )

            run_command(
                [
                    settings.ffmpeg_path,
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    str(image_path),
                    "-t",
                    str(frame.duration_seconds),
                    "-vf",
                    vf,
                    "-r",
                    str(fps),
                    "-pix_fmt",
                    "yuv420p",
                    "-c:v",
                    "libx264",
                    str(clip_path),
                ]
            )
            clip_paths.append(clip_path)

        return clip_paths

    def _concat_video_clips(self, clip_paths: list[Path], output_path: Path) -> Path:
        concat_file = output_path.parent / "video_clips.txt"
        concat_file.write_text(
            "\n".join(f"file '{path.resolve().as_posix()}'" for path in clip_paths),
            encoding="utf-8",
        )
        run_command(
            [
                settings.ffmpeg_path,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(output_path),
            ]
        )
        return output_path

    def _mix_audio_tracks(
        self,
        generated_audio: Path,
        background_music_path: Path,
        output_path: Path,
    ) -> Path:
        run_command(
            [
                settings.ffmpeg_path,
                "-y",
                "-i",
                str(generated_audio),
                "-stream_loop",
                "-1",
                "-i",
                str(background_music_path),
                "-filter_complex",
                "[0:a]volume=1.0[a0];[1:a]volume=0.18[a1];[a0][a1]amix=inputs=2:duration=first",
                "-c:a",
                "pcm_s16le",
                str(output_path),
            ]
        )
        return output_path

    def _motion_expressions(self, frame: StoryboardFrame) -> tuple[str, str, str]:
        move = f"{frame.camera_move} {frame.motion_line}".lower()
        shot = frame.shot_size.lower()

        if any(token in move for token in ["push", "dolly in", "推進", "推近", "zoom in"]):
            zoom_expr = "min(zoom+0.0015,1.18)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif any(token in move for token in ["pull", "orbit", "拉遠", "環繞", "zoom out"]):
            zoom_expr = "if(eq(on,1),1.15,max(1.0,zoom-0.0012))"
            x_expr = "iw/2-(iw/zoom/2)+sin(on/12)*18"
            y_expr = "ih/2-(ih/zoom/2)"
        elif any(token in move for token in ["tracking", "跟拍", "前移", "speed", "snap"]):
            zoom_expr = "min(zoom+0.0009,1.08)"
            x_expr = "iw/2-(iw/zoom/2)+on*1.8"
            y_expr = "ih/2-(ih/zoom/2)"
        else:
            zoom_expr = "min(zoom+0.0007,1.06)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        if any(token in shot for token in ["特寫", "close"]):
            zoom_expr = "min(zoom+0.0017,1.22)"
        return zoom_expr, x_expr, y_expr

    def _build_audio_filter(self, frame: StoryboardFrame) -> str:
        energy_text = f"{frame.music_tempo} {frame.sound_effect} {frame.camera_move}".lower()
        if any(token in energy_text for token in ["高潮", "加快", "密集", "fast", "beat drop", "高頻"]):
            freq = 220
            volume = 0.08
        elif any(token in energy_text for token in ["開始", "steady", "鼓點", "lo-fi", "hiphop"]):
            freq = 160
            volume = 0.06
        else:
            freq = 120
            volume = 0.05
        return f"sine=frequency={freq}:sample_rate=44100,volume={volume}"
