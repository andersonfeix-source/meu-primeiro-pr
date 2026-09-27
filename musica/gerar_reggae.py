"""Gera um reggae roots/dub (one drop, 76 BPM, Mi menor) usando o áudio
de voz enviado como vocal principal, com ecos de fita no estilo dub.

Uso: python3 gerar_reggae.py voz.wav saida.wav
Requer: numpy, scipy
"""
import sys
import numpy as np
from scipy.io import wavfile

from gerar_musica import (SR, midi_hz, env_adsr, lp, hp, reverb, place,
                          load_voice, pitch, fade, chops)

BPM = 76
BEAT = 60 / BPM
BAR = 4 * BEAT
SWING = 0.12  # atraso das colcheias fracas, em fração de batida
rng = np.random.default_rng(3)


def sw(pos):
    """Aplica swing a uma posição em batidas (colcheias no contratempo)."""
    frac = pos % 1
    return pos + SWING if abs(frac - 0.5) < 1e-6 else pos


def tape_echo(x, t=BEAT * 0.75, fb=0.55, n=7, mix=0.6):
    """Eco de fita: cada repetição mais escura e mais baixa (estilo King Tubby)."""
    d = int(t * SR)
    y = x.copy()
    rep = x
    for k in range(1, n + 1):
        rep = lp(rep, 3500 - 350 * k) * fb
        y[d * k:] += rep[:len(y) - d * k] * mix
    return y


# ---------- instrumentos ----------
def kick():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 50 + 70 * np.exp(-t * 25)
    return np.tanh(1.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)) * 0.9


def rim():
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 1700 * t) + 0.5 * np.sin(2 * np.pi * 820 * t)
    x = (tone * 0.6 + hp(rng.standard_normal(n), 2000) * 0.5) * np.exp(-t * 60)
    return x * 0.55


def snare():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    x = body * 0.5 + hp(lp(rng.standard_normal(n), 7000), 1200) * np.exp(-t * 16)
    return reverb(x, 1.2, 0.35) * 0.5


def hat(open_=False):
    n = int((0.25 if open_ else 0.06) * SR)
    x = hp(rng.standard_normal(n), 7500, 4) * np.exp(-np.arange(n) / SR * (12 if open_ else 70))
    return x * 0.22


def bass_note(note, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi_hz(note)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    x = lp(np.tanh(1.4 * x), 350)
    return x * env_adsr(n, 0.01, 0.15, 0.75, 0.06) * 0.8


def skank(notes, dur=BEAT * 0.22):
    """Guitarra 'chop' curta nos tempos 2 e 4: cordas pinçadas bem abafadas."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for i, m in enumerate(notes):
        f = midi_hz(m)
        o = int(i * 0.004 * SR)  # palhetada para baixo (strum)
        s = sum(np.sin(2 * np.pi * f * h * t[:n - o]) / h ** 1.3 for h in range(1, 7))
        x[o:] += s
    x = hp(x, 450) * np.exp(-t * 28)
    return reverb(x / len(notes), 0.8, 0.2) * 0.35


def organ(notes, dur):
    """Órgão drawbar (888000000) para o 'bubble'."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 6 * t)
    x = sum(np.sin(2 * np.pi * midi_hz(m) * h * vib * t) * a
            for m in notes for h, a in ((0.5, 0.6), (1, 1), (2, 0.5), (3, 0.25)))
    return x / len(notes) * env_adsr(n, 0.005, 0.05, 0.8, 0.03) * 0.18


def melodica(note, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi_hz(note) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t * 3, 0, 1))
    ph = np.cumsum(f) / SR
    x = np.sign(np.sin(2 * np.pi * ph)) * 0.6 + np.sin(4 * np.pi * ph) * 0.3
    x += rng.standard_normal(n) * 0.05  # sopro
    return lp(x, 2600) * env_adsr(n, 0.04, 0.1, 0.8, 0.08) * 0.16


# ---------- arranjo ----------
def main(voice_path, out_path):
    voice = load_voice(voice_path)
    ch = chops(voice, 8)

    # acordes (baixo, voicing do skank, voicing do órgão)
    Em = (40, [64, 67, 71, 76], [55, 59, 64])
    Am = (45, [64, 69, 72, 76], [57, 60, 64])
    C = (36, [64, 67, 72, 76], [55, 60, 64])
    D = (38, [62, 66, 69, 74], [54, 57, 62])
    verso = [Em, Em, Am, Am]
    refrao = [C, D, Em, Em]

    # linha de baixo: (posição em batidas, intervalo sobre a fundamental, duração)
    # o tempo 1 fica vazio — marca registrada do one drop
    bass_line = [(0.5, 0, 0.9), (1.5, 0, 0.4), (2, 7, 0.4), (2.5, 10, 0.4),
                 (3, 12, 0.4), (3.5, 7, 0.45)]
    mel_refrao = [(0, 76, 1.5), (1.5, 74, 0.5), (2, 71, 1), (3, 67, 1)]

    sections = [('intro', 4), ('verso', 8), ('refrao', 8), ('dub', 8),
                ('verso2', 8), ('refrao2', 8), ('outro', 4)]
    total = sum(b for _, b in sections)
    L = int((total * BAR + 6) * SR)
    drums = np.zeros(L); bass = np.zeros(L); gtr = np.zeros(L)
    org = np.zeros(L); mel = np.zeros(L); vox = np.zeros(L); dubfx = np.zeros(L)

    K, R, SN, H, OH = kick(), rim(), snare(), hat(), hat(True)
    bar = 0
    for name, nb in sections:
        for b in range(nb):
            tb = (bar + b) * BAR
            prog = refrao if name.startswith('refrao') else verso
            root, sk, og = prog[b % 4]
            full = name not in ('intro', 'dub', 'outro')

            # bateria one drop: bumbo + aro no tempo 3
            if name != 'intro' or b >= 2:
                place(drums, K, tb + 2 * BEAT)
                place(drums, R if b % 4 != 3 else SN, tb + 2 * BEAT)
                for q in range(8):
                    pos = sw(q / 2)
                    if name == 'dub' and q % 2 == 0:
                        continue
                    place(drums, OH if q == 7 and b % 2 else H * (0.6 + 0.4 * (q % 2)), tb + pos * BEAT)
            if full and b % 4 == 3:  # virada no fim da frase
                for k, pos in enumerate((3, 3.25, 3.5, 3.75)):
                    place(drums, SN * (0.5 + 0.12 * k), tb + pos * BEAT)

            # baixo
            if name != 'intro' or b >= 2:
                for pos, iv, dur in bass_line:
                    if name == 'dub' and b % 2 and pos > 2:
                        continue  # buracos no dub
                    place(bass, bass_note(root + iv, dur * BEAT), tb + sw(pos) * BEAT)

            # skank (tempos 2 e 4) e bubble do órgão
            if name != 'dub' or b >= 6:
                for q in (1, 3):
                    place(gtr, skank(sk), tb + q * BEAT)
            if full or name == 'outro':
                for q in range(4):
                    place(org, organ(og, BEAT * 0.3), tb + sw(q + 0.5) * BEAT)
                    place(org, organ([m - 12 for m in og], BEAT * 0.2) * 0.6, tb + q * BEAT)

            # melódica no refrão (responde ao vocal)
            if name.startswith('refrao') and b % 2 == 1:
                for pos, nt, dur in mel_refrao:
                    place(mel, melodica(nt, dur * BEAT), tb + pos * BEAT)

            # vocal
            if name == 'intro' and b == 0:
                place(dubfx, reverb(lp(voice, 1800), 3, 0.5) * 0.7, tb)
            if name.startswith('verso') and b % 4 == 0:
                place(vox, voice, tb + BEAT)
            if name.startswith('refrao'):
                if b % 2 == 0:
                    for pos, c, st in ((0, 0, 0), (1, 1, 0), (1.5, 1, 0), (2.5, 2, 2), (3, 3, -2)):
                        s = fade(pitch(ch[c], st)[:int(BEAT * 0.9 * SR)])
                        place(vox, s * 0.9, tb + sw(pos) * BEAT)
                    place(dubfx, fade(ch[3][:int(BEAT * 0.5 * SR)]), tb + 3.5 * BEAT)
            if name == 'dub':
                if b in (0, 4):
                    place(dubfx, voice * 0.8, tb)
                if b in (2, 6):
                    place(dubfx, fade(pitch(ch[b // 2], -3)) * 0.8, tb + 2 * BEAT)
                if b == 7:
                    place(dubfx, reverb(voice[::-1], 2.5, 0.5)[-int(BAR * SR):] * 0.7, tb)
            if name == 'outro' and b == 0:
                place(dubfx, voice * 0.8, tb)
        bar += nb

    # mix dub: vocal seco + envios de eco, graves em mono
    vox = reverb(tape_echo(vox, BEAT * 0.75, 0.35, 3, 0.35), 1.8, 0.2)
    dubfx = reverb(tape_echo(dubfx, BEAT * 0.75, 0.6, 8, 0.7), 3, 0.35)
    mel = tape_echo(reverb(mel, 2, 0.3), BEAT, 0.3, 3, 0.3)
    drums = drums + tape_echo(drums, BEAT * 0.75, 0.35, 3, 0.2) * 0.3

    center = drums * 0.8 + bass * 0.7 + vox * 1.6
    left = center + gtr * 1.3 + org * 0.8 + mel * 1.2 + dubfx * 1.3
    right = center + gtr * 0.8 + org * 1.3 + mel * 0.9
    d = int(0.017 * SR)
    right[d:] += dubfx[:-d] * 1.3  # eco atrasado no lado direito (ping-pong)

    st = hp(np.stack([left, right], 1), 28)
    st = np.tanh(st / np.abs(st).max() * 1.3)
    st = st / np.abs(st).max() * 0.95
    end = int((total * BAR + 5) * SR)
    st = st[:end]
    fo = int(5 * SR)
    st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    wavfile.write(out_path, SR, (st * 32767).astype(np.int16))
    print(f'{out_path}: {len(st) / SR:.1f}s')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
