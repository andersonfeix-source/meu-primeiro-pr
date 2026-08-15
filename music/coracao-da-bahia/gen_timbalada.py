#!/usr/bin/env python3
"""
Gera "Coracao da Bahia": uma faixa de percussao inspirada na Timbalada
(samba-reggae / afoxe da Bahia) construida em cima de um MP3 de batimento
cardiaco, que funciona como o "pulso" que sustenta o groove.

Uso:
    python3 gen_timbalada.py <heartbeat.f32 (f32le, 44100, stereo)> <saida.wav>
"""
import sys
import numpy as np
from scipy.signal import butter, lfilter

SR = 44100
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- utilities
def env_exp(n, decay):
    t = np.arange(n) / SR
    return np.exp(-decay * t)

def _filt_coeffs(kind, *freqs, order=4):
    nyq = SR / 2
    if kind == "band":
        return butter(order, [freqs[0] / nyq, freqs[1] / nyq], btype="band")
    if kind == "low":
        return butter(order, freqs[0] / nyq, btype="low")
    return butter(order, freqs[0] / nyq, btype="high")

_BP = {}
def bandpass(x, low, high):
    key = (low, high)
    if key not in _BP:
        _BP[key] = _filt_coeffs("band", low, high)
    b, a = _BP[key]
    return lfilter(b, a, x)

_LP = {}
def lowpass(x, cutoff):
    if cutoff not in _LP:
        _LP[cutoff] = _filt_coeffs("low", cutoff)
    b, a = _LP[cutoff]
    return lfilter(b, a, x)

_HP = {}
def highpass(x, cutoff):
    if cutoff not in _HP:
        _HP[cutoff] = _filt_coeffs("high", cutoff)
    b, a = _HP[cutoff]
    return lfilter(b, a, x)

def norm(x):
    m = np.max(np.abs(x)) + 1e-9
    return x / m

def pan(mono, p):
    """p in [-1,1] equal-power pan -> stereo (n,2)"""
    theta = (p + 1) * np.pi / 4
    return np.stack([mono * np.cos(theta), mono * np.sin(theta)], axis=1)

# ---------------------------------------------------------- instrument bank
def surdo(dur=0.55, freq=72, amp=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = freq + 32 * np.exp(-t * 16)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    e = env_exp(n, 7.5)
    click = np.pad(rng.standard_normal(int(SR * 0.004)), (0, max(0, n - int(SR * 0.004))))
    click = click[:n] * env_exp(n, 450)
    return amp * norm(tone * e + 0.35 * click)

def timbau(dur=0.32, freq=230, amp=0.85, slap=False):
    n = int(SR * dur)
    t = np.arange(n) / SR
    pdrop = 25 if slap else 65
    f = freq + pdrop * np.exp(-t * 32)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.7
    noise = bandpass(rng.standard_normal(n), 700, 4200)
    ne = env_exp(n, 22 if slap else 55)
    te = env_exp(n, 10 if slap else 13)
    out = tone * te + (0.55 if slap else 0.22) * noise * ne
    return amp * norm(out)

def caixa(dur=0.11, amp=0.45):
    n = int(SR * dur)
    noise = bandpass(rng.standard_normal(n), 1600, 6500)
    e = env_exp(n, 65)
    return amp * norm(noise * e)

def repique(dur=0.16, amp=0.55):
    n = int(SR * dur)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * (420 + 120 * np.exp(-t * 25)) * t)
    noise = bandpass(rng.standard_normal(n), 1200, 5000)
    e = env_exp(n, 35)
    return amp * norm(tone * e * 0.6 + 0.5 * noise * e)

def agogo(dur=0.22, freq=880, amp=0.4):
    n = int(SR * dur)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 1.5 * t)
    e = env_exp(n, 22)
    return amp * norm(tone * e)

def shaker(dur=0.085, amp=0.22):
    n = int(SR * dur)
    noise = highpass(rng.standard_normal(n), 4500)
    e = env_exp(n, 48)
    return amp * norm(noise * e)

# ------------------------------------------------------------- sequencer
BPM = 104.0
BEAT = 60.0 / BPM          # seconds per quarter note
STEP = BEAT / 4.0          # 16th note
BAR = STEP * 16

def stamp(buf, pos_sample, sound_mono, pan_pos, gain):
    n = len(sound_mono)
    if n == 0 or gain <= 0 or pos_sample < 0 or pos_sample >= len(buf):
        return
    st = pan(sound_mono * gain, pan_pos)
    end = min(pos_sample + n, len(buf))
    st = st[: end - pos_sample]
    buf[pos_sample:end] += st

# 16-step patterns (velocity 0..1). 0 = step 1 of the bar.
PAT = {
    "surdo1":  [1.0,0,0,0,0,0,0,0, 0.85,0,0,0,0,0,0,0],   # beats 1 & 3 (grave)
    "surdo2":  [0,0,0,0, 0.9,0,0,0, 0,0,0,0, 0.75,0,0,0], # beats 2 & 4 (contratempo)
    "timbau":  [0.9,0,0,0.55, 0.8,0,0.65,0, 0.9,0,0.55,0.8, 0,0.65,0,0.5],
    "caixa":   [0.25,0.4,0.25,0.5, 0.25,0.4,0.25,0.6, 0.25,0.4,0.25,0.5, 0.25,0.4,0.25,0.7],
    "agogo":   [0.6,0,0,0.4, 0,0,0.6,0, 0,0.4,0,0, 0.6,0,0.4,0],
    "shaker":  [0.3]*16,
}

def humanize(v):
    return max(0.0, v * (1 + rng.normal(0, 0.06)))

def jitter_samples():
    return int(rng.normal(0, SR * 0.0025))

def build_track(total_samples):
    buf = np.zeros((total_samples, 2), dtype=np.float64)

    # Precompute a small pool of hit variants per instrument (avoids identical
    # repeats, keeps a "live" feel).
    pools = {
        "surdo1": [surdo(amp=1.0) for _ in range(4)],
        "surdo2": [surdo(freq=88, amp=0.85) for _ in range(4)],
        "timbau": [timbau(amp=0.9) for _ in range(6)] + [timbau(amp=0.95, slap=True) for _ in range(3)],
        "caixa":  [caixa(amp=0.5) for _ in range(6)],
        "repique": [repique(amp=0.55) for _ in range(6)],
        "agogo":  [agogo(freq=880, amp=0.42) for _ in range(3)] + [agogo(freq=1180, amp=0.4) for _ in range(3)],
        "shaker": [shaker(amp=0.22) for _ in range(6)],
    }
    def pick(name):
        pool = pools[name]
        return pool[rng.integers(0, len(pool))]

    n_bars = int(np.ceil(total_samples / SR / BAR)) + 1

    # ---- arrangement: (start_bar, end_bar, {instrument: gain or 0}, heartbeat_gain, heartbeat_lp)
    # heartbeat_lp: None = full spectrum, otherwise lowpass cutoff Hz
    sections = [
        (0,   4,  dict(surdo1=0,    surdo2=0,   timbau=0,    caixa=0,   agogo=0,   shaker=0),                1.00, None),   # intro: so o coracao
        (4,   8,  dict(surdo1=0,    surdo2=0,   timbau=0.35, caixa=0,   agogo=0.5, shaker=0.6),               0.70, None),   # entra agogo/shaker/timbau leve
        (8,  20,  dict(surdo1=1.0,  surdo2=1.0, timbau=1.0,  caixa=0.9, agogo=0.9, shaker=1.0),               0.22, 220),    # groove cheio 1
        (20, 22,  dict(surdo1=0,    surdo2=0,   timbau=0.9,  caixa=0.7, agogo=0,   shaker=0.5),               0.55, None),   # break/chamada
        (22, 34,  dict(surdo1=1.0,  surdo2=1.0, timbau=1.0,  caixa=1.0, agogo=1.0, shaker=1.0),               0.20, 220),    # groove cheio 2 (com repique extra)
        (34, 38,  dict(surdo1=0.3,  surdo2=0.2, timbau=1.1,  caixa=0.4, agogo=0.2, shaker=0.4),               0.40, None),   # solo de timbau
        (38, 48,  dict(surdo1=1.1,  surdo2=1.1, timbau=1.1,  caixa=1.05, agogo=1.05, shaker=1.05),            0.18, 220),    # climax
        (48, n_bars, dict(surdo1=0, surdo2=0,   timbau=0,    caixa=0,   agogo=0,   shaker=0.15),              1.00, None),   # outro: volta o coracao
    ]

    def section_for_bar(bar):
        for s0, s1, gains, hb, lp in sections:
            if s0 <= bar < s1:
                return gains, hb, lp
        return sections[-1][2], sections[-1][3], sections[-1][4]

    for bar in range(n_bars):
        gains, _, _ = section_for_bar(bar)
        bar_start = bar * BAR

        # extra fills every 4th bar inside "groove" sections for realism
        fill_bar = (bar % 4 == 3) and gains.get("caixa", 0) > 0

        for step in range(16):
            step_time = bar_start + step * STEP
            pos = int(step_time * SR) + jitter_samples()

            v = PAT["surdo1"][step] * gains.get("surdo1", 0)
            if v > 0:
                stamp(buf, pos, pick("surdo1"), -0.05, humanize(v))

            v = PAT["surdo2"][step] * gains.get("surdo2", 0)
            if v > 0:
                stamp(buf, pos, pick("surdo2"), 0.15, humanize(v))

            v = PAT["timbau"][step] * gains.get("timbau", 0)
            if v > 0:
                stamp(buf, pos, pick("timbau"), -0.35, humanize(v))

            v = PAT["caixa"][step] * gains.get("caixa", 0)
            if fill_bar and step >= 12:
                v = max(v, 0.55) * gains.get("caixa", 0)
            if v > 0:
                stamp(buf, pos, pick("caixa"), 0.45, humanize(v))

            v = PAT["agogo"][step] * gains.get("agogo", 0)
            if v > 0:
                stamp(buf, pos, pick("agogo"), 0.6, humanize(v))

            v = PAT["shaker"][step] * gains.get("shaker", 0)
            if v > 0:
                stamp(buf, pos, pick("shaker"), -0.6, humanize(v))

        # repique flourish near the end of certain bars in full-groove sections
        if gains.get("caixa", 0) >= 0.9 and bar % 8 in (6, 7):
            for k, step in enumerate([13, 14, 14, 15]):
                pos = int((bar_start + step * STEP + k * STEP * 0.22) * SR)
                stamp(buf, pos, pick("repique"), 0.3, 0.5 + 0.1 * k)

    return buf, sections, n_bars

def main():
    hb_path, out_path = sys.argv[1], sys.argv[2]
    hb = np.fromfile(hb_path, dtype=np.float32).astype(np.float64).reshape(-1, 2)
    total = len(hb)
    duration = total / SR
    print(f"heartbeat duration: {duration:.2f}s ({total} samples)")

    perc, sections, n_bars = build_track(total)
    print(f"arrangement: {n_bars} bars @ {BPM} BPM ({BAR:.3f}s/bar)")

    # Build heartbeat gain envelope + optional per-section lowpass, bar by bar
    hb_out = np.zeros_like(hb)
    def section_for_bar(bar):
        for s0, s1, gains, hbg, lp in sections:
            if s0 <= bar < s1:
                return hbg, lp
        return sections[-1][3], sections[-1][4]

    n_bars_hb = int(np.ceil(total / SR / BAR)) + 1
    prev_gain, prev_lp = None, "INIT"
    for bar in range(n_bars_hb):
        hbg, lp = section_for_bar(bar)
        start = int(bar * BAR * SR)
        end = int(min(total, (bar + 1) * BAR * SR))
        if start >= total:
            break
        seg = hb[start:end].copy()
        if lp is not None:
            seg[:, 0] = lowpass(seg[:, 0], lp)
            seg[:, 1] = lowpass(seg[:, 1], lp)
        hb_out[start:end] = seg * hbg

    # smooth the gain steps a bit to avoid clicks: light moving-average crossfade
    win = int(SR * 0.05)
    if win > 1:
        kernel = np.ones(win) / win
        for ch in range(2):
            hb_out[:, ch] = np.convolve(hb_out[:, ch], kernel, mode="same")

    mix = perc[:total] + hb_out

    # gentle bus compression / soft-clip limiter for punch without harsh clipping
    peak = np.max(np.abs(mix)) + 1e-9
    mix = mix / peak * 0.98
    mix = np.tanh(mix * 1.15) / np.tanh(1.15)

    mix32 = mix.astype(np.float32)
    import scipy.io.wavfile as wavfile
    wavfile.write(out_path, SR, mix32)
    print(f"wrote {out_path}: peak={np.max(np.abs(mix32)):.3f}")

if __name__ == "__main__":
    main()
