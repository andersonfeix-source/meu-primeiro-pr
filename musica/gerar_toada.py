"""Gera uma base de toada/baião modal no estilo Zé Ramalho (84 BPM, Mi menor
dórico) com a estrutura das estrofes da letra, inserindo o áudio de voz
como declamação nas introduções, interlúdios e final.

Uso: python3 gerar_toada.py voz.wav saida.wav
Requer: numpy, scipy
"""
import sys
from functools import lru_cache
import numpy as np
from scipy.io import wavfile

from gerar_musica import (SR, midi_hz, env_adsr, lp, hp, reverb, place,
                          load_voice, pitch, fade)
from gerar_reggae import tape_echo

BPM = 84
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(11)


# ---------- instrumentos ----------
@lru_cache(maxsize=None)
def ks_string(note, secs=2.5, decay=0.996, bright=0.5):
    """Corda dedilhada (Karplus-Strong), vetorizado por período."""
    n = int(secs * SR)
    P = max(2, int(round(SR / midi_hz(note) - 0.5)))
    y = np.zeros(n + P + 1)
    y[:P + 1] = lp(rng.uniform(-1, 1, P + 1), 2000 + 8000 * bright)
    i = P + 1
    while i < len(y):
        j = min(i + P, len(y))
        y[i:j] = decay * 0.5 * (y[i - P:j - P] + y[i - P - 1:j - P - 1])
        i = j
    y = y[P + 1:]
    return y / (np.abs(y).max() + 1e-9)


def viola12(note, dur, vel=1.0):
    """Violão de 12 cordas: nota + oitava acima levemente atrasada."""
    n = int(dur * SR)
    x = ks_string(note)[:n] + 0.55 * np.concatenate([np.zeros(90), ks_string(note + 12)[:n - 90]])
    x = x * env_adsr(n, 0.001, 0.0, 1.0, min(0.08, dur / 3))
    return hp(x, 90) * 0.16 * vel


def bass_note(note, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi_hz(note)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.1 * np.sin(6 * np.pi * f * t)
    return lp(x, 500) * env_adsr(n, 0.01, 0.2, 0.6, 0.08) * 0.5


def zabumba(open_=True):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 62 + 55 * np.exp(-t * 18)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (5 if open_ else 14))
    x[:250] += rng.standard_normal(250) * np.linspace(0.6, 0, 250)  # batida da maceta
    return np.tanh(1.3 * x) * (0.75 if open_ else 0.5)


def bacalhau():
    """Vareta no aro de baixo da zabumba."""
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 2500) * np.exp(-t * 70) * 0.25


def triangulo(aberto):
    n = int((0.5 if aberto else 0.07) * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((4200, 1), (6900, 0.6), (9300, 0.4)))
    return x * np.exp(-t * (7 if aberto else 60)) * 0.06


def rabeca(note, dur):
    """Rabeca: serra com vibrato atrasado, formantes nasais e ataque de arco."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.009 * np.sin(2 * np.pi * 5.8 * t) * np.clip(t * 2.5, 0, 1)
    f = midi_hz(note) * vib
    ph = np.cumsum(f) / SR
    x = sum((2 * ((ph * (1 + d)) % 1) - 1) for d in (-0.003, 0.003)) / 2
    x = lp(hp(x, 350), 3200)
    from scipy.signal import butter, sosfilt
    x += 0.8 * sosfilt(butter(2, [900 / (SR / 2), 1400 / (SR / 2)], 'band', output='sos'), x)
    x += hp(rng.standard_normal(n), 3000) * 0.04  # ruído do arco
    return x * env_adsr(n, 0.06, 0.1, 0.85, 0.1) * 0.2


def strings70(notes, dur):
    """Cordas de sintetizador anos 70 (string machine)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in notes:
        for d in (-0.004, 0, 0.004):
            ph = midi_hz(m) * (1 + d) * t
            x += 2 * (ph % 1) - 1
    x = lp(x / (len(notes) * 3), 2200)
    return x * env_adsr(n, 0.6, 0.3, 0.8, 0.8) * 0.12


# ---------- harmonia ----------
Em = (40, [40, 47, 52, 55, 59, 64])
D = (38, [38, 45, 50, 54, 57, 62])
C = (36, [36, 43, 48, 52, 55, 64])
Am = (45, [45, 52, 57, 60, 64, 69])
A = (45, [45, 52, 57, 61, 64, 69])     # Lá maior: a 6ª maior do Mi dórico
B7 = (47, [47, 51, 57, 59, 63, 66])

VERSO = [Em, D, Em, D, C, A, Em, Em]     # 8 compassos = 1 estrofe (4 versos)
REFRAO = [C, D, Em, Em, Am, D, Em, Em]   # "E sei que não será surpresa..."
TAG = [C, B7, Em, Em]                    # "O passado de volta..."

# dedilhado (índice da corda, posição em colcheias) — padrão de toada
DEDILHADO = [(0, 0), (3, 1), (4, 2), (5, 3), (2, 4), (4, 5), (3, 6), (5, 7)]

# frase da rabeca em Mi dórico (nota MIDI, início em batidas, duração)
RABECA_TEMA = [(76, 0, 1), (79, 1, 0.5), (78, 1.5, 0.5), (76, 2, 1), (74, 3, 1),
               (73, 4, 1.5), (74, 5.5, 0.5), (76, 6, 2),
               (71, 8, 1), (74, 9, 1), (76, 10, 0.5), (78, 10.5, 0.5), (79, 11, 1),
               (78, 12, 1), (76, 13, 0.5), (74, 13.5, 0.5), (76, 14, 2)]


def main(voice_path, out_path):
    voice = load_voice(voice_path)

    # (nome, progressão, flags)
    sections = [
        ('Intro (declamação)', VERSO, 'intro'),
        ('Estrofe 1 — "Há um brilho de faca"', VERSO, 'v1'),
        ('Estrofe 2 — "Ninguém sai com o coração"', VERSO, 'v2'),
        ('Interlúdio (rabeca + voz)', VERSO[:4] + VERSO[:4], 'inter'),
        ('Estrofe 3 — "Um grande amor do passado"', VERSO, 'v3'),
        ('Estrofe 4 — "Não existe saudade mais cortante"', VERSO, 'v3'),
        ('Estrofe 5 — "Toco a vida pra frente"', VERSO, 'v5'),
        ('Refrão 1 — "E sei que não será surpresa"', REFRAO + TAG + TAG, 'ref'),
        ('Interlúdio 2 (rabeca)', VERSO[:4], 'inter2'),
        ('Refrão 2 — "E sei que não será surpresa"', REFRAO + TAG + TAG, 'ref'),
        ('Final (declamação)', [Em, D, Em, Em], 'outro'),
    ]
    total = sum(len(p) for _, p, _ in sections)
    L = int((total * BAR + 6) * SR)
    gtr = np.zeros(L); bass = np.zeros(L); perc = np.zeros(L)
    lead = np.zeros(L); pad = np.zeros(L); vox = np.zeros(L)

    Z, Zc, BC = zabumba(), zabumba(False), bacalhau()
    guia = []
    bar = 0
    for name, prog, tag in sections:
        guia.append((bar * BAR, name))
        t0 = bar * BAR
        for b, (root, shape) in enumerate(prog):
            tb = t0 + b * BAR
            # violão 12 cordas
            vel = 0.7 if tag in ('intro', 'outro') else 1.0
            for s, e in DEDILHADO:
                place(gtr, viola12(shape[s], BEAT * 1.6, vel * (1.15 if e == 0 else 1)),
                      tb + e * BEAT / 2 + rng.uniform(0, 0.008))
            # baixo: fundamental + quinta, com passagem no fim do compasso
            if tag not in ('intro',):
                place(bass, bass_note(root, BEAT * 1.4), tb)
                place(bass, bass_note(root + 7, BEAT * 0.9), tb + 1.5 * BEAT)
                place(bass, bass_note(root, BEAT * 0.9), tb + 2 * BEAT)
                nxt = prog[(b + 1) % len(prog)][0]
                place(bass, bass_note(nxt - 1 if nxt > root else nxt + 2, BEAT * 0.9), tb + 3.5 * BEAT)
            # percussão: toada leve nas primeiras estrofes, baião cheio depois
            if tag in ('v2', 'inter', 'v3', 'v5', 'ref', 'inter2'):
                baiao = tag not in ('v2',)
                for q in range(4):
                    tq = tb + q * BEAT
                    for s in range(4):
                        place(perc, triangulo(s == 2), tq + s * BEAT / 4)
                    if baiao:
                        if q in (0, 2):
                            place(perc, Z, tq)
                            place(perc, Z * 0.8, tq + 0.75 * BEAT)
                        else:
                            place(perc, Zc, tq + 0.5 * BEAT)
                        place(perc, BC, tq + 0.5 * BEAT)
                    elif q in (0, 2):
                        place(perc, Z * 0.7, tq)
            # cordas anos 70 nos refrões e estrofe 5
            if tag in ('ref', 'v5', 'outro') and (b % 2 == 0):
                place(pad, strings70([n + 12 for n in shape[2:5]], 2 * BAR), tb)

        # rabeca nos interlúdios e contracantos
        if tag in ('intro', 'inter', 'inter2', 'outro'):
            reps = 2 if tag == 'inter' else 1
            for r in range(reps):
                for nt, pos, dur in RABECA_TEMA[: (17 if tag != 'inter2' else 8)]:
                    if tag == 'intro' and pos < 8:
                        continue  # na intro a rabeca só responde à declamação
                    place(lead, rabeca(nt, dur * BEAT), t0 + r * 4 * BAR + pos * BEAT)
        if tag == 'v3':
            for k in range(0, 8, 2):  # respostas curtas no fim dos versos
                place(lead, rabeca(71, BEAT) * 0.6, t0 + (k + 1) * BAR + 2 * BEAT)
                place(lead, rabeca(74, BEAT) * 0.6, t0 + (k + 1) * BAR + 3 * BEAT)

        # voz (declamação)
        if tag == 'intro':
            place(vox, voice * 0.9, t0 + BAR)
        if tag == 'inter':
            place(vox, lp(voice, 2500) * 0.8, t0 + 4 * BAR + BEAT)
        if tag == 'inter2':
            rev = reverb(voice[::-1], 2.5, 0.5)
            place(vox, rev[-int(2 * BAR * SR):] * 0.6, t0 + 2 * BAR)
        if tag == 'outro':
            place(vox, voice * 0.9, t0 + BEAT)
            place(vox, fade(pitch(voice, -2)) * 0.4, t0 + 2 * BAR + BEAT)
        bar += len(prog)

    # tratamento: salão com reverb, eco na voz
    gtr = reverb(gtr, 1.6, 0.18)
    lead = tape_echo(reverb(lead, 2.2, 0.3), BEAT * 1.5, 0.3, 3, 0.3)
    vox = reverb(tape_echo(vox, BEAT * 0.75, 0.35, 4, 0.35), 2.8, 0.3)
    pad = reverb(pad, 3, 0.4)

    center = bass * 0.45 + perc * 0.45 + vox * 1.5
    left = center + gtr * 3.0 + lead * 1.1 + pad * 1.0
    d = int(0.014 * SR)
    gtr_r = np.concatenate([np.zeros(d), gtr[:-d]])  # abre o 12 cordas
    right = center + gtr_r * 3.0 + lead * 1.3 + pad * 1.2

    st = hp(np.stack([left, right], 1), 35)
    st = np.tanh(st / np.abs(st).max() * 1.2)
    st = st / np.abs(st).max() * 0.95
    st = st[:int((total * BAR + 5) * SR)]
    fo = int(5 * SR)
    st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    wavfile.write(out_path, SR, (st * 32767).astype(np.int16))

    print(f'{out_path}: {len(st) / SR:.1f}s')
    for t, name in guia:
        print(f'{int(t // 60)}:{int(t % 60):02d}  {name}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
