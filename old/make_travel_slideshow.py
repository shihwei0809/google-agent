import os
import sys
import glob
import math
import struct
import shutil
import wave
import subprocess
from PIL import Image, ImageFilter

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

def synthesize_bgm(output_mp3_path, duration_seconds=120):
    """
    Synthesizes a warm, ambient piano-like background music track (100% Python).
    Converts the output WAV to MP3 using FFmpeg.
    """
    sample_rate = 44100
    num_samples = sample_rate * duration_seconds
    
    notes = {
        'C3': 130.81, 'E3': 164.81, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
        'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
        'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'G5': 783.99, 'A5': 880.00
    }
    
    # Emotional chord progression: Fmaj7 - G6 - Em7 - Am7 (warm vacation vibe)
    chords = [
        ['A3', 'C4', 'E4', 'G4', 'C5'],  # Fmaj7/Am7 vibe
        ['B3', 'D4', 'G4', 'B4', 'E5'],  # G6
        ['G3', 'B3', 'E4', 'G4', 'D5'],  # Em7
        ['A3', 'C4', 'E4', 'A4', 'E5']   # Am7
    ]
    
    print("[INFO] Synthesizing travel BGM track...")
    left_channel = [0.0] * num_samples
    right_channel = [0.0] * num_samples
    
    chord_dur = 4.0  # seconds per chord
    
    for sample_idx in range(num_samples):
        t_sec = sample_idx / sample_rate
        chord_idx = int(t_sec / chord_dur) % len(chords)
        chord = chords[chord_idx]
        
        t_in_chord = t_sec % chord_dur
        
        for i, note in enumerate(chord):
            freq = notes[note]
            # Arpeggio delay: notes play sequentially
            note_delay = i * 0.25
            if t_in_chord < note_delay:
                continue
                
            t_note = t_in_chord - note_delay
            # Slow fade-in and exponential decay
            envelope = (1.0 - math.exp(-t_note / 0.15)) * math.exp(-t_note / 2.0)
            
            # Fundamental sine wave + warm harmonics
            val = 0.6 * math.sin(2 * math.pi * freq * t_note) + \
                  0.15 * math.sin(2 * math.pi * (freq * 2) * t_note) + \
                  0.05 * math.sin(2 * math.pi * (freq * 3) * t_note)
                  
            # Stereo panning distribution
            pan = 0.3 + (i / len(chord)) * 0.4
            
            left_channel[sample_idx] += val * envelope * (1.0 - pan)
            right_channel[sample_idx] += val * envelope * pan

    # Stereo echo delay
    delay_samples = int(sample_rate * 0.4)
    decay = 0.4
    for sample_idx in range(delay_samples, num_samples):
        left_channel[sample_idx] += left_channel[sample_idx - delay_samples] * decay
        right_channel[sample_idx] += right_channel[sample_idx - delay_samples] * decay

    # Global fade-in and fade-out
    fade_in = sample_rate * 3
    fade_out = sample_rate * 5
    for sample_idx in range(num_samples):
        factor = 1.0
        if sample_idx < fade_in:
            factor = sample_idx / fade_in
        elif sample_idx > num_samples - fade_out:
            factor = (num_samples - sample_idx) / fade_out
        left_channel[sample_idx] *= factor
        right_channel[sample_idx] *= factor

    # Output to WAV
    wav_temp_path = output_mp3_path + ".temp.wav"
    with wave.open(wav_temp_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        
        max_amplitude = 32767 * 0.35
        frames = []
        for sample_idx in range(num_samples):
            l_val = int(clamp(left_channel[sample_idx], -1.0, 1.0) * max_amplitude)
            r_val = int(clamp(right_channel[sample_idx], -1.0, 1.0) * max_amplitude)
            frames.append(struct.pack("<hh", l_val, r_val))
        w.writeframes(b"".join(frames))
        
    # Convert WAV to MP3 using FFmpeg
    subprocess.run([
        "ffmpeg", "-y", "-i", wav_temp_path, 
        "-codec:a", "libmp3lame", "-qscale:a", "2", 
        output_mp3_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(wav_temp_path):
        os.remove(wav_temp_path)
    print(f"[OK] BGM saved to: {output_mp3_path}")

def process_image_blurred_bg(img_path, target_width=1920, target_height=1080):
    """
    Loads an image, creates a blurred background matching the aspect ratio,
    and pastes the original image centered over it. Returns a PIL Image object.
    """
    img = Image.open(img_path)
    
    # 1. Generate blurred background
    bg = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    
    # 2. Scale original image keeping aspect ratio
    img_w, img_h = img.size
    aspect_ratio = img_w / img_h
    target_aspect = target_width / target_height
    
    if aspect_ratio > target_aspect:
        # Image is wider than 16:9
        new_w = target_width
        new_h = int(target_width / aspect_ratio)
    else:
        # Image is taller than 16:9
        new_h = target_height
        new_w = int(target_height * aspect_ratio)
        
    resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # 3. Paste centered
    x_offset = (target_width - new_w) // 2
    y_offset = (target_height - new_h) // 2
    bg.paste(resized_img, (x_offset, y_offset))
    
    return bg

def make_video_slideshow(photos_dir, output_mp4_path, display_seconds=3, transition_seconds=1, fps=30):
    """
    Loads images from photos_dir, creates crossfade transitions,
    generates a BGM audio file, and combines them into output_mp4_path.
    """
    # Find all images
    img_extensions = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
    img_files = []
    for ext in img_extensions:
        img_files.extend(glob.glob(os.path.join(photos_dir, ext)))
        
    # Sort images by filename (so chronological if from Google Photos)
    img_files.sort()
    
    if not img_files:
        print(f"[ERROR] No images found in {photos_dir}")
        return False
        
    print(f"[INFO] Found {len(img_files)} images. Processing...")
    
    # Create temp directory for frames
    temp_dir = os.path.join(photos_dir, "temp_slideshow_frames")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Process all images to 1920x1080 blurred background format
    processed_images = []
    for idx, path in enumerate(img_files):
        print(f"[INFO] Processing image [{idx+1}/{len(img_files)}]: {os.path.basename(path)}")
        processed_img = process_image_blurred_bg(path)
        processed_images.append(processed_img)
        
    # Calculate frames
    display_frames = int(display_seconds * fps)
    transition_frames = int(transition_seconds * fps)
    
    frame_counter = 0
    num_images = len(processed_images)
    
    print("[INFO] Creating blended transition frames (Crossfade)...")
    
    for i in range(num_images):
        current_img = processed_images[i]
        next_img = processed_images[(i + 1) % num_images]
        
        # 1. Solid display frames
        for _ in range(display_frames):
            frame_path = os.path.join(temp_dir, f"frame_{frame_counter:05d}.jpg")
            current_img.save(frame_path, "JPEG", quality=92)
            frame_counter += 1
            
        # 2. Transition frames
        if i < num_images - 1:
            for f in range(transition_frames):
                alpha = f / transition_frames
                blended_img = Image.blend(current_img, next_img, alpha)
                frame_path = os.path.join(temp_dir, f"frame_{frame_counter:05d}.jpg")
                blended_img.save(frame_path, "JPEG", quality=92)
                frame_counter += 1
        else:
            # Fade to black for last frame
            black_img = Image.new("RGB", (1920, 1080), (0, 0, 0))
            for f in range(transition_frames):
                alpha = f / transition_frames
                blended_img = Image.blend(current_img, black_img, alpha)
                frame_path = os.path.join(temp_dir, f"frame_{frame_counter:05d}.jpg")
                blended_img.save(frame_path, "JPEG", quality=92)
                frame_counter += 1
                
    # Calculate video duration
    total_seconds = frame_counter / fps
    print(f"[OK] Total frames generated: {frame_counter} (approx. {total_seconds:.1f} seconds)")
    
    # Generate BGM
    bgm_path = os.path.join(photos_dir, "temp_bgm.mp3")
    synthesize_bgm(bgm_path, duration_seconds=int(total_seconds + 3))
    
    # Run FFmpeg to compile
    print("[INFO] Running FFmpeg to encode final video and mix audio...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(temp_dir, "frame_%05d.jpg"),
        "-i", bgm_path,
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4_path
    ]
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    
    # Cleanup temp files
    shutil.rmtree(temp_dir)
    if os.path.exists(bgm_path):
        os.remove(bgm_path)
        
    if result.returncode == 0:
        print(f"\n[SUCCESS] Video slideshow generated successfully at:\n{output_mp4_path}")
        return True
    else:
        print("[ERROR] FFmpeg failed:")
        print(result.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python make_travel_slideshow.py [input_photos_dir] [output_video_path]")
        sys.exit(1)
        
    photos_dir = sys.argv[1]
    output_mp4 = sys.argv[2]
    
    if not os.path.exists(photos_dir):
        print(f"[ERROR] Directory does not exist: {photos_dir}")
        sys.exit(1)
        
    make_video_slideshow(photos_dir, output_mp4)
