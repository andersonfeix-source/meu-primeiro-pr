# Coração da Bahia

Uma faixa de percussão inspirada na **Timbalada** (samba-reggae / afoxé
baiano), composta e sintetizada por código a partir de um MP3 de batimento
cardíaco que serve como base ("o pulso") da música.

- **Arquivo final:** [`coracao-da-bahia.mp3`](./coracao-da-bahia.mp3) (~2min)
- **Script de geração:** [`gen_timbalada.py`](./gen_timbalada.py)

## Ideia

O batimento cardíaco entra sozinho na introdução, some sob a batucada nos
trechos de groove cheio (filtrado como um sub grave que ainda se sente) e
volta a aparecer puro no final — representando o "coração coletivo" que a
Timbalada evoca nos blocos afro da Bahia.

## Instrumentação sintetizada

| Instrumento        | Papel no groove                                    |
|---------------------|-----------------------------------------------------|
| Surdo 1 / Surdo 2   | Marcação grave nos tempos 1&3 e contratempo 2&4      |
| Timbau              | Groove sincopado característico da Timbalada         |
| Caixa               | Subdivisão rápida em 16 avos, com viradas a cada 4 compassos |
| Repique             | Floreios/viradas nos finais de frase                |
| Agogô               | Figura melódica de sino em duas alturas              |
| Chocalho/Ganza      | Textura contínua em 16 avos                          |

## Estrutura (54 compassos, 104 BPM)

1. **Intro** — só o batimento cardíaco
2. **Build** — agogô, chocalho e timbau leve entram
3. **Groove cheio 1** — ensemble completo
4. **Break/chamada** — cai para timbau + caixa
5. **Groove cheio 2** — ensemble completo com viradas de repique
6. **Solo de timbau** — percussão principal em destaque
7. **Clímax** — groove no volume máximo
8. **Outro** — a batucada se apaga e o coração volta sozinho

## Reprodutibilidade

Todo o áudio é sintetizado em Python (`numpy` + `scipy`), sem samples
externos — cada instrumento é gerado por síntese de onda/ruído filtrado.

```bash
pip install numpy scipy
# heartbeat.f32: PCM float32, 44100 Hz, estéreo, extraído do MP3 original
ffmpeg -i heartbeat_only.mp3 -ac 2 -ar 44100 -f f32le heartbeat.f32
python3 gen_timbalada.py heartbeat.f32 saida.wav
ffmpeg -i saida.wav -codec:a libmp3lame -qscale:a 2 coracao-da-bahia.mp3
```
