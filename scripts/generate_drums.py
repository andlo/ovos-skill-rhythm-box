#!/usr/bin/env python3
"""Regenerates sounds/{kick,snare,hihat_closed,hihat_open}.wav - short
generated percussion hits (no external samples, nothing to source or
license), same philosophy as ovos-skill-metronome's generated clicks.

Usage: python3 scripts/generate_drums.py
"""
import wave
import struct
import math
import random
from pathlib import Path

SOUNDS_DIR = Path(__file__).resolve().parent.parent / "sounds"
SR = 44100


def _write_wav(path, samples, sr=SR):
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        clamped = (max(-1.0, min(1.0, s)) for s in samples)
        f.writeframes(b"".join(struct.pack("<h", int(s * 32767)) for s in clamped))


def _kick(duration_ms=150, sr=SR):
    """Pitch-swept low sine, mimics a bass drum's thump."""
    n = int(sr * duration_ms / 1000)
    samples = []
    for i in range(n):
        t = i / sr
        env = math.exp(-i / (n * 0.25))
        freq = 40 + 150 * math.exp(-i / (n * 0.15))  # sweeps down fast
        samples.append(0.9 * env * math.sin(2 * math.pi * freq * t))
    return samples


def _snare(duration_ms=120, sr=SR):
    """Tone + noise mix, mimics a snare's crack-and-buzz."""
    n = int(sr * duration_ms / 1000)
    rng = random.Random(42)
    samples = []
    for i in range(n):
        t = i / sr
        env = math.exp(-i / (n * 0.2))
        tone = 0.3 * math.sin(2 * math.pi * 180 * t)
        noise = 0.7 * rng.uniform(-1, 1)
        samples.append(0.8 * env * (tone + noise))
    return samples


def _hihat(duration_ms, seed, sr=SR):
    """Filtered-feeling noise burst - short duration = closed, longer = open."""
    n = int(sr * duration_ms / 1000)
    rng = random.Random(seed)
    samples = []
    for i in range(n):
        env = math.exp(-i / (n * 0.2))
        samples.append(0.5 * env * rng.uniform(-1, 1))
    return samples


if __name__ == "__main__":
    SOUNDS_DIR.mkdir(exist_ok=True)
    _write_wav(SOUNDS_DIR / "kick.wav", _kick())
    _write_wav(SOUNDS_DIR / "snare.wav", _snare())
    _write_wav(SOUNDS_DIR / "hihat_closed.wav", _hihat(30, seed=7))
    _write_wav(SOUNDS_DIR / "hihat_open.wav", _hihat(200, seed=11))
    print(f"wrote 4 drum sounds to {SOUNDS_DIR}")
