"""Gera uma faixa de música eletrônica (melodic house, 124 BPM, Mi menor)
usando o áudio de voz enviado como sample principal.

Uso: python3 gerar_musica.py voz.wav saida.wav
Requer: numpy, scipy
"""
import sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, resample

SR = 44100
BPM = 124
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(7)


def midi_hz(n):
    return 440 * 2 ** ((n - 69) / 12)


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.1):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    e = np.full(n, s)
    e[:a] = np.linspace(0, 1, a) if a else 1
    e[a:a + d] = np.linspace(1, s, len(e[a:a + d]))
    if r:
        e[-r:] *= np.linspace(1, 0, len(e[-r:]))
    return e


def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR / 2 - 100) / (SR / 2), 'low', output='sos'), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc / (SR / 2), 'high', output='sos'), x)


def sweep_lp(x, f0, f1, block=512):
    """Filtro passa-baixa com cutoff variando no tempo (automação)."""
    out = np.zeros_like(x)
    fcs = np.geomspace(f0, f1, len(x) // block + 1)
    zi = np.zeros((1, 2))
    for i, fc in enumerate(fcs):
        seg = x[i * block:(i + 1) * block]
        if not len(seg):
            break
        sos = butter(2, min(fc, SR / 2 - 100) / (SR / 2), 'low', output='sos')
        y, zi = sosfilt(sos, seg, zi=zi)
        out[i * block:i * block + len(seg)] = y
    return out


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f * (1 + detune)) % 1) - 1


def supersaw(f, n):
    return sum(saw(f, n, d) for d in (-0.012, -0.005, 0, 0.005, 0.012)) / 5


def reverb(x, secs=2.5, mix=0.3):
    n = int(secs * SR)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir = lp(ir, 6000)
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n))[:len(x)]
    wet /= np.abs(wet).max() + 1e-9
    return (1 - mix) * x + mix * wet * np.abs(x).max()


def delay(x, t=BEAT * 0.75, fb=0.4, mix=0.35):
    d = int(t * SR)
    y = x.copy()
    for k in range(1, 6):
        y[d * k:] += x[:-d * k] * (fb ** k) * mix
    return y


def place(buf, sig, t):
    i = int(t * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[:j - i]


# ---------- instrumentos ----------
def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 30)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    x[:300] += rng.standard_normal(300) * np.linspace(0.4, 0, 300)
    return np.tanh(1.8 * x)


def clap():
    n = int(0.25 * SR)
    e = np.zeros(n)
    for o in (0, 0.011, 0.022):
        i = int(o * SR)
        e[i:] += np.exp(-np.arange(n - i) / SR * 45)
    x = rng.standard_normal(n) * e
    return hp(lp(x, 5000), 900) * 0.6


def hat(open_=False):
    n = int((0.22 if open_ else 0.05) * SR)
    x = hp(rng.standard_normal(n), 8000, 4) * np.exp(-np.arange(n) / SR * (14 if open_ else 80))
    return x * 0.35


def bass_note(note, dur):
    n = int(dur * SR)
    x = lp(saw(midi_hz(note), n) + 0.6 * np.sin(2 * np.pi * midi_hz(note - 12) * np.arange(n) / SR), 400)
    return np.tanh(2 * x) * env_adsr(n, 0.005, 0.08, 0.6, 0.03) * 0.5


def pad_chord(notes, dur, bright=1800):
    n = int(dur * SR)
    x = sum(supersaw(midi_hz(m), n) for m in notes) / len(notes)
    return lp(x, bright) * env_adsr(n, 0.4, 0.3, 0.8, 0.5) * 0.35


def pluck(note, dur=BEAT / 2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = supersaw(midi_hz(note), n)
    x = sweep_lp(x, 5000, 400)
    return x * np.exp(-t * 9) * 0.3


def riser(dur):
    n = int(dur * SR)
    x = sweep_lp(rng.standard_normal(n), 200, 12000, 256)
    return x * np.linspace(0, 1, n) ** 2 * 0.25


def impact():
    n = int(2 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-t * 6)) / SR) * np.exp(-t * 2)
    return reverb(x + lp(rng.standard_normal(n), 800) * np.exp(-t * 4) * 0.3, 3, 0.5) * 0.7


# ---------- vocal ----------
def load_voice(path):
    sr, v = wavfile.read(path)
    v = v.astype(float)
    if v.ndim > 1:
        v = v.mean(axis=1)
    if sr != SR:
        v = resample(v, int(len(v) * SR / sr))
    v /= np.abs(v).max() + 1e-9
    # recorta silêncio inicial/final pelo envelope RMS
    h = int(0.02 * SR)
    rms = np.sqrt(np.convolve(v ** 2, np.ones(h) / h, 'same'))
    idx = np.where(rms > 0.08)[0]
    v = v[max(0, idx[0] - h):idx[-1] + h]
    return hp(v, 120)


def pitch(x, semis):
    """Pitch shift simples por reamostragem (muda duração junto)."""
    r = 2 ** (semis / 12)
    return resample(x, int(len(x) / r))


def fade(x, ms=8):
    k = min(int(ms / 1000 * SR), len(x) // 2)
    x = x.copy()
    x[:k] *= np.linspace(0, 1, k)
    x[-k:] *= np.linspace(1, 0, k)
    return x


def chops(v, n):
    """Divide a voz em n fatias com fade (vocal chops)."""
    L = len(v) // n
    return [fade(v[i * L:(i + 1) * L]) for i in range(n)]


# ---------- arranjo ----------
def main(voice_path, out_path):
    voice = load_voice(voice_path)
    ch = chops(voice, 8)

    # Mi menor: Em - C - G - D
    prog = [(40, [52, 55, 59, 64]), (36, [48, 52, 55, 60]),
            (43, [50, 55, 59, 62]), (38, [50, 54, 57, 62])]
    arp_pat = [0, 2, 1, 3, 2, 1, 3, 2]

    sections = [  # (nome, compassos)
        ('intro', 8), ('build', 8), ('drop1', 16),
        ('break', 8), ('build2', 4), ('drop2', 16), ('outro', 8)]
    total_bars = sum(b for _, b in sections)
    L = int((total_bars * BAR + 3) * SR)

    drums = np.zeros(L); bass = np.zeros(L); pads = np.zeros(L)
    lead = np.zeros(L); vox = np.zeros(L); fx = np.zeros(L)
    sc = np.ones(L)  # envelope de sidechain

    K, C, H, OH = kick(), clap(), hat(), hat(True)
    duck = 1 - 0.75 * np.exp(-np.arange(int(BEAT * SR)) / SR * 14)

    bar = 0
    for name, nb in sections:
        t0 = bar * BAR
        for b in range(nb):
            tb = t0 + b * BAR
            root, chord = prog[(b // 2) % 4]
            first_of_chord = b % 2 == 0
            dense = name in ('drop1', 'drop2')

            # pads
            if first_of_chord:
                bright = {'intro': 900, 'build': 1400, 'break': 1200, 'build2': 1800}.get(name, 2600)
                place(pads, pad_chord(chord, 2 * BAR, bright), tb)

            # bateria
            for q in range(4):
                tq = tb + q * BEAT
                if name in ('build', 'drop1', 'drop2', 'outro') or (name == 'intro' and b >= 4):
                    place(drums, K, tq)
                    i = int(tq * SR)
                    sc[i:i + len(duck)] = np.minimum(sc[i:i + len(duck)], duck[:max(0, min(len(duck), L - i))])
                if name == 'build2':
                    # rufada acelerando
                    div = 1 if b < 2 else (2 if b < 3 else 4)
                    for k in range(div):
                        place(drums, C * (0.5 + 0.5 * (b + q / 4) / 4), tq + k * BEAT / div)
                if dense or (name == 'build' and b >= 4):
                    if q in (1, 3):
                        place(drums, C, tq)
                    place(drums, OH, tq + BEAT / 2)
                if dense or name in ('intro', 'outro'):
                    for s in range(4):
                        if s != 2:
                            place(drums, H * (1 if s % 2 else 0.6), tq + s * BEAT / 4)

            # baixo (offbeat, estilo house)
            if name in ('drop1', 'drop2', 'outro') or (name == 'build' and b >= 4):
                for q in range(4):
                    place(bass, bass_note(root, BEAT / 2 * 0.9), tb + q * BEAT + BEAT / 2)
                    if dense and q == 3:
                        place(bass, bass_note(root + 12, BEAT / 4), tb + q * BEAT + BEAT * 0.75)

            # arpejo / lead
            if name in ('drop1', 'drop2', 'break', 'build2') or (name == 'build' and b >= 4):
                for s in range(8):
                    nt = chord[arp_pat[s] % 4] + 12
                    g = 0.6 if name in ('break', 'build') else 1.0
                    place(lead, pluck(nt) * g, tb + s * BEAT / 2)

            # vocal
            if name == 'intro' and b in (0, 4):
                place(vox, lp(voice, 1500) * 0.7, tb)
            if name == 'build' and b % 2 == 0:
                for s in range(4):
                    place(vox, ch[(b + s) % 8] * 0.8, tb + s * BEAT)
            if dense:
                # hook: chops rítmicos com variação de altura
                pat = [(0, 0, 0), (0.75, 1, 0), (1.5, 2, 3), (2.5, 3, 0), (3, 1, 5), (3.5, 2, 7)]
                for pos, c, st in pat:
                    s = pitch(ch[c], st)[:int(BEAT * 0.7 * SR)]
                    place(vox, fade(s) * 0.9, tb + pos * BEAT)
                if b % 4 == 0:
                    place(vox, voice * 0.35, tb)  # frase completa por cima
            if name == 'break' and b in (0, 4):
                rev = reverb(voice[::-1], 3, 0.6)
                place(vox, rev * 0.6, tb)
                place(vox, reverb(pitch(voice, -5), 3, 0.5) * 0.6, tb + 2 * BAR)
            if name == 'build2':
                for s in range(8):
                    place(vox, pitch(ch[0], b * 2 + s * 0.5)[:int(BEAT / 2 * SR)] * 0.8, tb + s * BEAT / 2)

        # efeitos de transição
        if name in ('build', 'build2'):
            place(fx, riser(nb * BAR), t0)
        if name in ('drop1', 'drop2'):
            place(fx, impact(), t0)
        bar += nb

    # pós-processamento dos grupos
    lead = delay(reverb(lead, 1.8, 0.25))
    vox = delay(reverb(vox, 1.6, 0.2), BEAT / 2, 0.3, 0.25)
    pads = reverb(pads, 3, 0.35)

    mix = (drums * 0.9 + bass * sc * 0.9 + pads * sc * 0.6
           + lead * sc * 0.45 + vox * 0.9 + fx * 0.6)
    mix = hp(mix, 30)

    # estéreo: pads/lead abertos via Haas, graves centralizados
    d = int(0.012 * SR)
    wide = pads * sc * 0.6 + lead * sc * 0.45
    left = mix.copy()
    right = mix - wide + np.concatenate([np.zeros(d), wide[:-d]])

    st = np.stack([left, right], 1)
    st = np.tanh(st / np.abs(st).max() * 1.2)  # saturação/limiter suave
    st /= np.abs(st).max()
    st *= 0.95

    # fade-out final
    fo = int(4 * SR)
    st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    wavfile.write(out_path, SR, (st * 32767).astype(np.int16))
    print(f'{out_path}: {len(st) / SR:.1f}s')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
