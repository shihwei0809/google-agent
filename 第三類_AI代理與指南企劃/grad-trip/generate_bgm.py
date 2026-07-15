# 純 Python 程式化合成畢業旅行溫暖氛圍背景音樂
import math, struct, os, subprocess

SAMPLE_RATE = 44100
DURATION = 115  # 115 秒以完整覆蓋 107.7 秒的影片
NUM_SAMPLES = SAMPLE_RATE * DURATION

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

# 音符頻率定義
NOTES = {
    'C3': 130.81, 'E3': 164.81, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'G5': 783.99, 'A5': 880.00
}

# 溫暖抒情的和弦進行 (Fmaj7 - G6 - Em7 - Am7)
CHORDS = [
    ['A3', 'C4', 'E4', 'G4', 'C5'],  # Am7 / Fmaj7-like
    ['B3', 'D4', 'G4', 'B4', 'E5'],  # G6
    ['G3', 'B3', 'E4', 'G4', 'D5'],  # Em7
    ['A3', 'C4', 'E4', 'A4', 'E5']   # Am7
]

# 產生合成音軌
print("Synthesizing ambient graduation BGM (CD Quality, Stereo)...")
left_channel = [0.0] * NUM_SAMPLES
right_channel = [0.0] * NUM_SAMPLES

# 模擬一個溫暖的主音合成器 + 延遲回饋 (Delay / Echo)
chord_dur = 4.0  # 每個和弦 4 秒
beat_len = SAMPLE_RATE * chord_dur

for sample_idx in range(NUM_SAMPLES):
    t_sec = sample_idx / SAMPLE_RATE
    chord_idx = int(t_sec / chord_dur) % len(CHORDS)
    chord = CHORDS[chord_idx]
    
    # 每個和弦內的微小起奏時間 (Arpeggio)
    t_in_chord = t_sec % chord_dur
    
    # 產生多個諧波以達到溫和的鋼琴/合成墊 (Synth Pad) 質感
    for i, note in enumerate(chord):
        freq = NOTES[note]
        # 琶音延遲：音符依序淡入
        note_delay = i * 0.25
        if t_in_chord < note_delay:
            continue
            
        t_note = t_in_chord - note_delay
        # 慢淡入 (0.2s) 與 指數衰減 (3.0s)
        envelope = (1.0 - math.exp(-t_note / 0.2)) * math.exp(-t_note / 2.2)
        
        # 基礎正弦波 + 些許溫和的三角波諧波，增添溫潤感
        val = 0.6 * math.sin(2 * math.pi * freq * t_note) + \
              0.15 * math.sin(2 * math.pi * (freq * 2) * t_note) + \
              0.05 * math.sin(2 * math.pi * (freq * 3) * t_note)
              
        # 左右聲道立體聲分布
        pan = 0.3 + (i / len(chord)) * 0.4  # pan between 0.3 (left-ish) and 0.7 (right-ish)
        
        left_channel[sample_idx] += val * envelope * (1.0 - pan)
        right_channel[sample_idx] += val * envelope * pan

# 套用回音效應 (Stereo Echo Delay) 以營造大氣、寬廣的空間感
delay_samples = int(SAMPLE_RATE * 0.4)  # 0.4 秒的延遲
decay = 0.5  # 50% 衰減回饋

for sample_idx in range(delay_samples, NUM_SAMPLES):
    left_channel[sample_idx] += left_channel[sample_idx - delay_samples] * decay
    right_channel[sample_idx] += right_channel[sample_idx - delay_samples] * decay

# 套用開場與結尾的全局淡入淡出
fade_in_len = SAMPLE_RATE * 3   # 3 秒淡入
fade_out_len = SAMPLE_RATE * 5  # 5 秒淡出

for sample_idx in range(NUM_SAMPLES):
    factor = 1.0
    if sample_idx < fade_in_len:
        factor = sample_idx / fade_in_len
    elif sample_idx > NUM_SAMPLES - fade_out_len:
        factor = (NUM_SAMPLES - sample_idx) / fade_out_len
        
    left_channel[sample_idx] *= factor
    right_channel[sample_idx] *= factor

# 輸出 WAV 檔
os.makedirs("assets/audio", exist_ok=True)
wav_path = "assets/audio/bgm_temp.wav"
mp3_path = "assets/audio/bgm.mp3"

import wave
with wave.open(wav_path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SAMPLE_RATE)
    
    # 限制音量在安全範圍內，避免破音
    max_amplitude = 32767 * 0.35
    
    frames = []
    for sample_idx in range(NUM_SAMPLES):
        l_val = int(clamp(left_channel[sample_idx], -1.0, 1.0) * max_amplitude)
        r_val = int(clamp(right_channel[sample_idx], -1.0, 1.0) * max_amplitude)
        frames.append(struct.pack("<hh", l_val, r_val))
        
    w.writeframes(b"".join(frames))

print(f"✓ WAV 產生完成：{wav_path}")

# 將 WAV 轉換為高效能 MP3 並清理暫存檔
print("Converting to high quality MP3 via FFmpeg...")
subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.remove(wav_path)
print(f"✓ BGM 合成與壓制完成：{mp3_path}")
