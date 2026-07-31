from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDERS = ROOT / "renders"
RENDERS.mkdir(exist_ok=True)

SAMPLE_RATE = 44100
DURATION = 75.0


def env(t: float, attack: float, release: float, dur: float) -> float:
    if t < 0 or t > dur:
        return 0.0
    if t < attack:
        return t / attack
    if t > dur - release:
        return max(0.0, (dur - t) / release)
    return 1.0


def sine(freq: float, t: float) -> float:
    return math.sin(2 * math.pi * freq * t)


def bell(freq: float, t: float, dur: float) -> float:
    amp = math.exp(-4.6 * t / dur)
    return (
        sine(freq, t) * 0.70
        + sine(freq * 2.01, t) * 0.22
        + sine(freq * 3.02, t) * 0.08
    ) * amp


def soft_square(freq: float, t: float) -> float:
    return (
        sine(freq, t)
        + 0.33 * sine(freq * 3, t)
        + 0.18 * sine(freq * 5, t)
    ) / 1.51


def note_freq(name: str) -> float:
    notes = {
        "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00, "A3": 220.00,
        "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00,
        "C5": 523.25, "D5": 587.33, "E5": 659.25, "G5": 783.99,
    }
    return notes[name]


CHORDS = [
    ("C", ["C4", "E4", "G4"], "C3"),
    ("G", ["G3", "D4", "G4"], "G3"),
    ("Am", ["A3", "C4", "E4"], "A3"),
    ("F", ["F3", "C4", "F4"], "F3"),
]

MELODY = [
    "E5", "D5", "C5", "D5",
    "G4", "A4", "C5", "D5",
    "E5", "G5", "E5", "D5",
    "C5", "D5", "E5", "C5",
]


def make_music() -> None:
    random.seed(7)
    total = int(SAMPLE_RATE * DURATION)
    out = RENDERS / "better_bgm.wav"
    beat = 0.5
    bar = beat * 4
    section = bar * 4

    with wave.open(str(out), "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)

        frames = bytearray()
        for i in range(total):
            t = i / SAMPLE_RATE
            fade = env(t, 2.0, 5.0, DURATION)
            chord_i = int(t // section) % len(CHORDS)
            _, chord, bass_note = CHORDS[chord_i]
            local = t % section

            # Warm pad.
            pad = 0.0
            for n in chord:
                f = note_freq(n)
                pad += soft_square(f, t) * 0.055
                pad += sine(f * 0.5, t) * 0.025
            pad *= 0.75 + 0.15 * sine(0.08, t)

            # Soft bass pulse on beats 1 and 3.
            beat_pos = t % bar
            bass = 0.0
            if beat_pos < 0.22 or (2.0 <= beat_pos < 2.22):
                bass_env = math.exp(-10 * (beat_pos % 2.0))
                bass = sine(note_freq(bass_note), t) * 0.10 * bass_env

            # Bell arpeggio.
            arp_step = int((t % section) / beat)
            arp_note = chord[arp_step % len(chord)]
            arp_t = (t % beat)
            arp = bell(note_freq(arp_note) * 2, arp_t, beat) * 0.17

            # Simple hopeful melody after intro.
            mel = 0.0
            if t > 8:
                mel_step = int((t - 8) / beat) % len(MELODY)
                mel_t = (t - 8) % beat
                if mel_step % 2 == 0 or t > 42:
                    mel = bell(note_freq(MELODY[mel_step]), mel_t, beat * 1.2) * 0.11

            # Very soft travel rhythm.
            hat = 0.0
            if (t % 0.25) < 0.018:
                hat = (random.random() * 2 - 1) * 0.025 * math.exp(-90 * (t % 0.25))
            kick = 0.0
            if (t % 1.0) < 0.045:
                kick = sine(80 - 30 * (t % 1.0), t) * 0.08 * math.exp(-55 * (t % 1.0))

            sample = (pad + bass + arp + mel + hat + kick) * fade
            sample = max(-0.95, min(0.95, sample))

            # Gentle stereo width.
            left = sample * (0.96 + 0.04 * sine(0.13, t))
            right = sample * (0.96 - 0.04 * sine(0.11, t))
            frames.extend(struct.pack("<hh", int(left * 32767), int(right * 32767)))

        wav.writeframes(frames)
    print(out)


if __name__ == "__main__":
    make_music()
