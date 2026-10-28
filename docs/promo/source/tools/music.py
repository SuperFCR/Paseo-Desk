#!/usr/bin/env python3
"""程序合成背景音乐（无采样、无版权素材）：和弦铺底 + 拨弦琶音 + 低音 + 轻鼓点 + 混响。

段落随场景起伏：开场只有铺底，进入“怎么跑”后加入低音与鼓点，部署 / 边界段落收一些，
结尾回到主和弦并淡出。用法：python music.py --seconds 220 --out audio/music.wav
"""
from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np

SR = 44100
BPM = 84
BEAT = 60 / BPM
BAR = 4 * BEAT
CHORD = 2 * BAR  # 每个和弦两小节

# C 大调：Fmaj7 → G6 → Em7 → Am7 循环，结尾 Cmaj7
LOOP = [
    (41, [53, 57, 60, 64]),
    (43, [55, 59, 62, 64]),
    (40, [52, 55, 59, 62]),
    (45, [57, 60, 64, 67]),
]
HOME = (36, [48, 55, 60, 64, 71])


def hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def env_adsr(n: int, a: float, r: float) -> np.ndarray:
    t = np.arange(n) / SR
    dur = n / SR
    e = np.minimum(1.0, t / a)
    e *= np.clip((dur - t) / r, 0.0, 1.0)
    return e


def pad_note(m: float, n: int, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for ch, cents in ((0, -5), (1, 5)):
        f = hz(m) * 2 ** (cents / 1200)
        ph = rng.uniform(0, 2 * np.pi)
        s = np.zeros(n)
        for h in range(1, 7):
            s += np.sin(2 * np.pi * f * h * t + ph * h) / h ** 1.6
        out[:, ch] = s
    trem = 1 + 0.06 * np.sin(2 * np.pi * 0.23 * t + rng.uniform(0, 6))
    return out * trem[:, None]


def pluck(m: float, n: int) -> np.ndarray:
    t = np.arange(n) / SR
    f = hz(m)
    s = np.zeros(n)
    for h, amp in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.1)):
        s += amp * np.sin(2 * np.pi * f * h * t) * np.exp(-t * (3.2 + 2.2 * h))
    s *= np.minimum(1.0, t / 0.004)
    return s


def kick(n: int) -> np.ndarray:
    t = np.arange(n) / SR
    f = 45 + 75 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.22)


def hat(n: int, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(n) / SR
    x = np.diff(rng.standard_normal(n + 1))
    return x * np.exp(-t / 0.03)


def add(buf: np.ndarray, at: float, sig: np.ndarray, gain: float, pan: float = 0.0) -> None:
    i = int(at * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l, sig * r], axis=1) * np.sqrt(2)
    buf[i: i + len(sig)] += gain * sig


def reverb(x: np.ndarray, seconds: float, rng: np.random.Generator) -> np.ndarray:
    m = int(seconds * SR)
    t = np.arange(m) / SR
    size = 1 << int(np.ceil(np.log2(len(x) + m)))
    out = np.zeros_like(x)
    for ch in range(2):
        ir = rng.standard_normal(m) * np.exp(-t * 6.9 / seconds)
        ir = np.convolve(ir, np.ones(6) / 6, mode="same")  # 柔化高频
        ir /= np.sqrt(np.sum(ir ** 2))
        y = np.fft.irfft(np.fft.rfft(x[:, ch], size) * np.fft.rfft(ir, size), size)
        out[:, ch] = y[: len(x)]
    return out


def level(t: float, marks: dict[str, float], total: float) -> dict[str, float]:
    """各声部随时间的音量（0..1）。"""
    main, calm, outro = marks["main"], marks["calm"], marks["outro"]
    ramp = lambda a, b: float(np.clip((t - a) / (b - a), 0, 1))
    arp = 0.35 + 0.65 * ramp(8, 30)
    bass = ramp(main - 4, main + 2) * (1 - 0.35 * ramp(calm, calm + 4))
    drums = ramp(main, main + 6) * (1 - ramp(calm - 2, calm + 2))
    if t > outro:
        arp *= 1 - 0.6 * ramp(outro, outro + 6)
        bass *= 1 - ramp(outro, outro + 6)
    return {"arp": arp, "bass": bass, "drums": drums}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=220)
    ap.add_argument("--main", type=float, default=36, help="进入主段的时刻（过场结束）")
    ap.add_argument("--calm", type=float, default=156, help="部署段开始，收鼓点")
    ap.add_argument("--outro", type=float, default=196, help="尾声开始")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    total = args.seconds
    marks = {"main": args.main, "calm": args.calm, "outro": args.outro}
    rng = np.random.default_rng(20261027)
    n = int((total + 4) * SR)
    dry_pad, dry_arp, dry_low = (np.zeros((n, 2)) for _ in range(3))

    # 和弦表：尾声最后一个整和弦落到主和弦
    chords, t = [], 0.0
    while t < total:
        k = len(chords)
        chords.append((t, HOME if t >= args.outro + CHORD else LOOP[k % len(LOOP)]))
        t += CHORD

    for i, (t0, (root, notes)) in enumerate(chords):
        last = i == len(chords) - 1
        dur = (total + 3 - t0) if last else CHORD + 1.6
        seg = int(dur * SR)
        e = env_adsr(seg, 1.4, 2.4 if last else 1.6)
        for m in notes:
            add(dry_pad, t0, pad_note(m, seg, rng) * e[:, None], 0.075)
        # 拨弦琶音：八分音符，和弦音上移八度
        pattern = [0, 1, 2, 3, 2, 1, 2, 3] * 2
        steps = 16 if not last else 8
        for s in range(steps):
            at = t0 + s * BEAT / 2
            if at >= total - 1.5:
                break
            lv = level(at, marks, total)
            if at < 10 and s % 4:  # 开场稀疏
                continue
            m = notes[pattern[s] % len(notes)] + 12 + (12 if s % 8 == 7 else 0)
            vel = 0.75 + 0.25 * rng.random()
            add(dry_arp, at, pluck(m, int(0.9 * SR)), 0.11 * vel * lv["arp"], pan=0.35 if s % 2 else -0.35)
        # 低音：每小节第 1、3 拍
        for b in range(4 if not last else 2):
            at = t0 + b * 2 * BEAT
            lv = level(at, marks, total)
            if lv["bass"] <= 0:
                continue
            seg_b = int(2 * BEAT * SR)
            tb = np.arange(seg_b) / SR
            f = hz(root)
            sig = (np.sin(2 * np.pi * f * tb) + 0.3 * np.sin(4 * np.pi * f * tb)) * env_adsr(seg_b, 0.02, 0.3) * np.exp(-tb * 0.8)
            add(dry_low, at, sig, 0.16 * lv["bass"])
    # 鼓：第 1、3 拍底鼓，反拍轻踩镲
    beat = 0.0
    while beat < total:
        lv = level(beat, marks, total)
        if lv["drums"] > 0:
            k = round(beat / BEAT)
            if k % 2 == 0:
                add(dry_low, beat, kick(int(0.5 * SR)), 0.30 * lv["drums"])
            add(dry_arp, beat + BEAT / 2, hat(int(0.12 * SR), rng), 0.022 * lv["drums"], pan=0.2)
        beat += BEAT

    wet = reverb(dry_pad + dry_arp, 3.2, rng)
    mix = 0.85 * dry_pad + 0.8 * dry_arp + dry_low + 0.55 * wet
    mix = mix[: int(total * SR)]
    t = np.arange(len(mix)) / SR
    fade = np.minimum(1, t / 3.0) * np.clip((total - t) / 7.0, 0, 1)
    mix *= fade[:, None]
    rms = np.sqrt(np.mean(mix ** 2))
    mix *= 10 ** (-17 / 20) / rms  # 约 -17 dBFS RMS，背景音乐响度
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    peak = np.max(np.abs(mix))
    if peak > 0.89:
        mix *= 0.89 / peak
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(args.out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    print(f"{args.out}: {total:.1f}s, peak {np.max(np.abs(mix)):.3f}, rms {20 * np.log10(np.sqrt(np.mean(mix ** 2))):.1f} dBFS")


if __name__ == "__main__":
    main()
