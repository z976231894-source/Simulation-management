"""Original, deterministic audio for ONE MORE DINER management mode.

Writes exclusively beneath D:/idea美术资产详解/idea3/audio/management_v1
and the existing web demo's dist/assets/audio/management_v1 directory.
No external music, samples, services, or paid generation is used.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import wave

import numpy as np

ROOT = Path("D:/idea美术资产详解/idea3")
OUT = ROOT / "audio/management_v1"
GAME = ROOT / "web_demo_v1/dist/assets/audio/management_v1"
MASTER = OUT / "masters"
SR = 44100
RNG = np.random.default_rng(20261013)
for folder in (OUT, GAME, MASTER, OUT / "tmp"):
    folder.mkdir(parents=True, exist_ok=True)
os.environ["TEMP"] = os.environ["TMP"] = str(OUT / "tmp")
sys.path.insert(0, str(OUT / "vendor"))


def hz(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def time_axis(seconds):
    return np.arange(round(seconds * SR), dtype=np.float64) / SR


def smooth_noise(n, window=32, seed=None):
    generator = RNG if seed is None else np.random.default_rng(seed)
    data = generator.normal(0, 1, n)
    if window <= 1:
        return data
    # Periodic smoothing means loop noise has no boundary discontinuity.
    padded = np.pad(data, (window, window), mode="wrap")
    result = np.convolve(padded, np.ones(window) / window, mode="same")[window:-window]
    return result * math.sqrt(window)


def electric_piano(note, duration, velocity=1):
    t = time_axis(duration + 1.15)
    f = hz(note)
    attack = 1 - np.exp(-t * 160)
    release = np.exp(-np.maximum(t - duration, 0) * 8)
    fundamental = np.sin(2 * np.pi * f * t + 1.35 * np.sin(2 * np.pi * f * 2.002 * t) * np.exp(-t * 5))
    upper = .18 * np.sin(2 * np.pi * 3.001 * f * t) * np.exp(-t * 5.5)
    body = (fundamental + upper) * np.exp(-t * 1.8) * attack * release
    return body * velocity


def bass(note, duration, velocity=1):
    t = time_axis(duration + .18)
    f = hz(note)
    body = np.sin(2 * np.pi * f * t) + .18 * np.sin(2 * np.pi * 2 * f * t) + .07 * np.sin(2 * np.pi * 3 * f * t)
    envelope = (1 - np.exp(-t * 180)) * np.exp(-t * 2.6) * np.exp(-np.maximum(t - duration, 0) * 22)
    return body * envelope * velocity


def wood_note(note, duration, velocity=1):
    t = time_axis(duration + .3)
    f = hz(note)
    body = np.sin(2 * np.pi * f * t) * np.exp(-t * 5)
    body += .18 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 13)
    body += .07 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 22)
    envelope = (1 - np.exp(-t * 280)) * np.exp(-np.maximum(t - duration, 0) * 12)
    return body * envelope * velocity


def kick():
    t = time_axis(.25)
    phase = 2 * np.pi * (52 * t + 1.3 * (1 - np.exp(-t * 35)))
    return np.sin(phase) * np.exp(-t * 23) * (1 - np.exp(-t * 700))


def brush(duration=.26):
    t = time_axis(duration)
    noise = smooth_noise(len(t), 14)
    envelope = np.sin(np.pi * np.minimum(t / duration, 1)) ** .75
    return noise * envelope * .7


def hat():
    t = time_axis(.055)
    raw = smooth_noise(len(t), 1)
    high = raw - smooth_noise(len(t), 16)
    return high * np.exp(-t * 80) * (1 - np.exp(-t * 600)) * .5


def add(buffer, sound, at_seconds, gain=1, pan=0):
    start = round(at_seconds * SR)
    n = len(buffer)
    left = math.sqrt((1 - pan) / 2) * gain
    right = math.sqrt((1 + pan) / 2) * gain
    # Notes and reverb wrap, creating a genuinely continuous musical loop.
    sound = np.asarray(sound, dtype=np.float32)
    indices = (start + np.arange(len(sound))) % n
    np.add.at(buffer[:, 0], indices, sound * left)
    np.add.at(buffer[:, 1], indices, sound * right)


def stereo_room(buffer, wet=.13):
    result = buffer.copy()
    for seconds, decay in ((.047, .54), (.083, .38), (.127, .23), (.173, .14)):
        delay = round(seconds * SR)
        result[:, 0] += np.roll(buffer[:, 1], delay) * wet * decay
        result[:, 1] += np.roll(buffer[:, 0], delay + 103) * wet * decay
    return result


def master_audio(data, peak=.7, loop=False):
    if data.ndim == 1:
        data = np.column_stack((data, data))
    data = data.astype(np.float64)
    data -= data.mean(axis=0, keepdims=True)
    if not loop:
        fade = min(round(.008 * SR), len(data) // 8)
        data[:fade] *= np.linspace(0, 1, fade)[:, None]
        data[-fade:] *= np.linspace(1, 0, fade)[:, None]
    actual = float(np.max(np.abs(data)))
    if actual > 0:
        data *= peak / actual
    return data.astype(np.float32)


# One original 8-bar progression and composed four phrase melodies. Service and
# rush have identical note grids and tonal material; rush adds only soft rhythm.
CHORDS = [
    (36, [60, 64, 67, 71]),  # Cmaj7
    (41, [60, 64, 65, 69]),  # Fmaj7/C
    (38, [60, 62, 65, 69]),  # Dm7
    (43, [59, 62, 65, 69]),  # G9
    (40, [59, 62, 64, 67]),  # Em7
    (45, [60, 64, 67, 69]),  # Am7
    (38, [60, 62, 65, 69]),  # Dm7
    (43, [59, 62, 65, 69]),  # G9 -> loop Cmaj7
]
MELODIES = [
    [(0, 76, .65), (.75, 79, .4), (1.5, 81, .55), (2.5, 79, .5), (3.25, 76, .55)],
    [(.5, 77, .45), (1.25, 76, .55), (2, 72, .5), (3, 74, .65)],
    [(0, 74, .65), (1, 77, .55), (2.5, 76, .4), (3.25, 74, .6)],
    [(0, 71, .6), (1.5, 74, .55), (2.5, 77, .4), (3.25, 76, .45)],
    [(.5, 76, .5), (1.25, 79, .45), (2.5, 74, .65)],
    [(0, 72, .75), (1, 76, .4), (1.75, 79, .5), (3, 76, .75)],
    [(.5, 77, .6), (1.5, 74, .6), (2.5, 72, .4), (3.25, 74, .5)],
    [(0, 71, .6), (1.25, 74, .5), (2.5, 72, .55), (3.25, 71, .5)],
]


def compose_music(kind):
    menu = kind == "menu"
    bpm, bars, duration = (80, 16, 48) if menu else (96, 24, 60)
    beat = 60 / bpm
    tonal = np.zeros((round(duration * SR), 2), dtype=np.float32)
    rhythm = np.zeros_like(tonal)
    local_rng = np.random.default_rng(2179 if menu else 6241)
    for bar in range(bars):
        root, chord = CHORDS[bar % 8]
        origin = bar * 4 * beat
        # Chord comping alternates pocketed offbeats and longer chord stabs.
        comps = [(0, 1.45, .14), (1.75, .6, .10), (3, .75, .12)]
        if menu:
            comps = [(0, 1.9, .145), (2.5, 1.1, .09)]
        for off, length, level in comps:
            for j, note in enumerate(chord):
                add(tonal, electric_piano(note, length * beat), origin + (off + j * .018) * beat,
                    level * (1 + local_rng.uniform(-.08, .08)), -.16)
        walking = [root, root + 7, root + 12, root + (2 if bar % 8 in (1, 5) else 7)]
        for pos, note in enumerate(walking):
            add(tonal, bass(note, beat * .72), origin + pos * beat, .33 if menu else .37, .04)
        # A, A', response: different octave and piano/wood timbres; real rests.
        phrase = MELODIES[bar % 8]
        for off, note, length in phrase:
            if menu and bar % 8 in (3, 7) and off > 2:
                continue
            if bar >= 16:
                note -= 12 if bar % 4 < 2 else 0
            sound = electric_piano(note, length * beat) if bar % 4 < 3 else wood_note(note, length * beat)
            add(tonal, sound, origin + off * beat, .22 if menu else .25, .21)
        for pos in (0, 2):
            add(rhythm, kick(), origin + pos * beat, .10 if menu else .13)
        for pos in (1, 3):
            add(rhythm, brush(.22), origin + pos * beat, .095 if menu else .12, -.12)
        for pos in range(4):
            add(rhythm, hat(), origin + (pos + .66) * beat, .038 if menu else .05, .28)
        if kind == "rush":
            for pos in range(4):
                add(rhythm, brush(.11), origin + (pos + .66) * beat, .062, -.18)
                add(rhythm, wood_note(64 if pos % 2 else 67, .05), origin + (pos + .33) * beat, .025, .3)
            if bar % 4 == 3:
                add(rhythm, brush(.13), origin + 3.66 * beat, .075, .12)
    return master_audio(stereo_room(tonal, .12) + rhythm, .72, loop=True)


def noise_burst(duration, window=8, rate=12, peak=.45):
    t = time_axis(duration)
    sound = smooth_noise(len(t), window) * np.exp(-t * rate)
    return master_audio(sound, peak)


def little_melody(notes, duration, peak=.55):
    buf = np.zeros((round(duration * SR), 2), dtype=np.float32)
    for at, note, length, gain in notes:
        sound = wood_note(note, length)[:round((duration - at) * SR)]
        add(buf, sound, at, gain)
    return master_audio(buf, peak)


def build_sfx():
    assets = {}
    t = time_axis(.09)
    assets["ui_click"] = master_audio((np.sin(2 * np.pi * 650 * t) * .3 + smooth_noise(len(t), 5) * .12) * np.exp(-t * 80), .32)
    assets["door_bell"] = little_melody([(0, 88, .34, .7), (.16, 83, .65, .65)], 1.25, .55)
    t = time_axis(.38)
    paper = smooth_noise(len(t), 4) - .3 * smooth_noise(len(t), 60)
    env = np.exp(-((t - .085) / .045) ** 2) + .7 * np.exp(-((t - .23) / .07) ** 2)
    assets["ticket_paper"] = master_audio(paper * env, .48)
    t = time_axis(.26)
    assets["patty_down"] = master_audio((np.sin(2 * np.pi * 92 * t) * .6 + smooth_noise(len(t), 35) * .5) * np.exp(-t * 26), .62)
    t = time_axis(4)
    noise = smooth_noise(len(t), 3, seed=115)
    # Periodic amplitude modulation and wrapped tiny oil crackles.
    sizzle = noise * (.65 + .12 * np.sin(2 * np.pi * t / 4) + .08 * np.sin(2 * np.pi * t * 2))
    buf = np.column_stack((sizzle, np.roll(sizzle, 161)))
    for at in np.linspace(0, 3.95, 31):
        click_t = time_axis(.035)
        click = smooth_noise(len(click_t), 1) * np.exp(-click_t * 150)
        add(buf, click, float(at), .12, float(RNG.uniform(-.6, .6)))
    assets["grill_sizzle"] = master_audio(buf, .5, loop=True)
    assets["food_ready"] = little_melody([(0, 76, .18, .7), (.16, 79, .18, .6), (.34, 84, .28, .55)], .9, .58)
    # Short muted descending reminder, not a horror alarm.
    assets["food_burnt"] = little_melody([(0, 72, .18, .65), (.19, 68, .22, .55)], .75, .58)
    t = time_axis(.34)
    crunch = smooth_noise(len(t), 2) - .3 * smooth_noise(len(t), 24)
    env = sum(np.exp(-((t - x) / .009) ** 2) * g for x, g in ((.018, 1), (.063, .6), (.11, .72), (.20, .42)))
    assets["onion_crunch"] = master_audio(crunch * env, .5)
    t = time_axis(.48)
    rustle = smooth_noise(len(t), 6) - .45 * smooth_noise(len(t), 60)
    env = np.sin(np.pi * t / .48) ** 2 * (.65 + .35 * np.sin(2 * np.pi * 8 * t) ** 2)
    assets["leaf_rustle"] = master_audio(rustle * env, .42)
    t = time_axis(.32)
    wet = smooth_noise(len(t), 72) * np.exp(-t * 22) + .26 * np.sin(2 * np.pi * (210 * t - 80 * t * t)) * np.exp(-t * 26)
    assets["wet_topping"] = master_audio(wet, .48)
    t = time_axis(.4)
    fold = smooth_noise(len(t), 24) * np.exp(-((t - .11) / .07) ** 2)
    fold += .25 * smooth_noise(len(t), 60) * np.exp(-((t - .27) / .04) ** 2)
    assets["cheese_fold"] = master_audio(fold, .36)
    t = time_axis(.45)
    tray = (np.sin(2 * np.pi * 430 * t) + .45 * np.sin(2 * np.pi * 743 * t) + .25 * np.sin(2 * np.pi * 1180 * t)) * np.exp(-t * 22)
    tray += smooth_noise(len(t), 16) * .3 * np.exp(-t * 60)
    assets["tray_pickup"] = master_audio(tray, .5)
    cash = little_melody([(0, 79, .13, .55), (.12, 84, .24, .5)], .9, .58)
    coins_t = time_axis(.17)
    coins = (np.sin(2 * np.pi * 1870 * coins_t) + .7 * np.sin(2 * np.pi * 2830 * coins_t)) * np.exp(-coins_t * 45)
    cash[round(.33 * SR):round(.33 * SR) + len(coins)] += coins[:, None] * .12
    assets["serve_cash"] = master_audio(cash, .62)
    t = time_axis(.27)
    wrong = np.sin(2 * np.pi * (260 * t - 120 * t ** 2)) * (1 - np.exp(-t * 170)) * np.exp(-t * 13)
    assets["wrong_action"] = master_audio(wrong, .43)
    assets["customer_left"] = little_melody([(0, 72, .16, .6), (.16, 67, .20, .48)], .7, .4)
    assets["shift_closed"] = little_melody([(0, 72, .2, .6), (.18, 76, .2, .56), (.36, 79, .24, .5), (.6, 84, .4, .5)], 1.6, .56)
    assets["upgrade"] = little_melody([(0, 72, .13, .65), (.1, 76, .13, .6), (.22, 79, .13, .55), (.34, 84, .3, .5)], 1.1, .54)
    t = time_axis(.21)
    step = (smooth_noise(len(t), 18) * .3 + np.sin(2 * np.pi * 118 * t) * .6) * np.exp(-t * 38)
    assets["footstep_tile"] = master_audio(step, .33)
    return assets


def room_ambience():
    t = time_axis(8)
    low = smooth_noise(len(t), 320, seed=715)
    high = smooth_noise(len(t), 80, seed=925)
    left = low * .7 + high * .12
    right = np.roll(low, 723) * .7 + np.roll(high, 183) * .12
    # Air circulation and refrigerator only; no incomprehensible voices.
    hum = np.sin(2 * np.pi * 120 * t) * .06 + np.sin(2 * np.pi * 180 * t) * .02
    return master_audio(np.column_stack((left + hum, right + hum)), .25, loop=True)


def write_wav(path, data):
    pcm = np.round(np.clip(data, -.9999, .9999) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())


def audit(data, loop):
    peak = float(np.max(np.abs(data)))
    rms = float(np.sqrt(np.mean(data.astype(np.float64) ** 2)))
    diff = np.abs(np.diff(data, axis=0))
    seam = float(np.max(np.abs(data[0] - data[-1])))
    derivative_p999 = float(np.percentile(diff, 99.9))
    report = {
        "sample_frames": len(data), "seconds_exact": len(data) / SR,
        "channels": 2, "sample_rate": SR, "peak_dbfs": round(20 * np.log10(max(peak, 1e-12)), 3),
        "rms_dbfs": round(20 * np.log10(max(rms, 1e-12)), 3),
        "dc_offset_max": float(np.max(np.abs(data.mean(axis=0)))),
        "clipped_samples": int(np.sum(np.abs(data) >= .999)),
        "audible": rms > .0005, "loop": loop,
        "seam_sample_jump": seam, "derivative_p999": derivative_p999,
        "seam_within_normal_transient_range": seam < max(.005, derivative_p999 * 1.25),
    }
    if report["clipped_samples"] or not report["audible"]:
        raise RuntimeError(f"Invalid audio: {report}")
    if loop and not report["seam_within_normal_transient_range"]:
        raise RuntimeError(f"Loop seam exceeds normal adjacent sample differences: {report}")
    return report


def main():
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    manifest = {
        "version": 1, "name": "ONE MORE DINER — Original Management Audio", "created": "2026-10-13",
        "sampleRate": SR, "origin": "Original deterministic DSP composition; no third-party recordings or music.",
        "music": {}, "sfx": {}, "ambience": {},
        "mix": {"musicBus": .34, "sfxBus": .75, "ambienceBus": .08, "master": .8,
                "rushCrossfadeSeconds": 2.5, "syncGroup": "service_96_cmajor_24bars", "alertDuckDb": -5},
    }
    reports = {}
    all_data = {}

    def emit(name, data, category, gain, loop=False, **extra):
        wav = MASTER / f"{name}.wav"
        mp3 = GAME / f"{name}.mp3"
        write_wav(wav, data)
        bitrate = "112k" if category == "music" else "80k" if loop else "64k"
        subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
                        "-codec:a", "libmp3lame", "-b:a", bitrate, "-ar", str(SR), "-write_xing", "1", str(mp3)], check=True)
        # LAME's gapless metadata must survive: independent PCM decode checks it.
        decoded = subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(mp3),
                                  "-f", "f32le", "-acodec", "pcm_f32le", "-ar", str(SR), "-ac", "2", "pipe:1"],
                                 check=True, stdout=subprocess.PIPE).stdout
        decoded = np.frombuffer(decoded, dtype="<f4").reshape((-1, 2))
        report = audit(data, loop)
        report["mp3_decoded_frames"] = len(decoded)
        report["mp3_gapless_exact_frame_count"] = len(decoded) == len(data)
        report["mp3_padding_frames"] = len(decoded) - len(data)
        report["mp3_peak_dbfs"] = round(20 * np.log10(max(float(np.max(np.abs(decoded))), 1e-12)), 3)
        report["mp3_seam_sample_jump"] = float(np.max(np.abs(decoded[0] - decoded[-1])))
        decoded_derivative = float(np.percentile(np.abs(np.diff(decoded, axis=0)), 99.9))
        report["mp3_seam_within_normal_transient_range"] = report["mp3_seam_sample_jump"] < max(.005, decoded_derivative * 1.25)
        if loop and len(decoded) != len(data):
            raise RuntimeError(f"MP3 loop padding not removed for {name}")
        if not loop and abs(len(decoded) - len(data)) > 32:
            raise RuntimeError(f"Excess short one-shot encoder padding for {name}")
        if float(np.max(np.abs(decoded))) >= .999:
            raise RuntimeError(f"MP3 encoder overshoot clips for {name}")
        report["wav_bytes"] = wav.stat().st_size
        report["mp3_bytes"] = mp3.stat().st_size
        report["mp3_sha256"] = hashlib.sha256(mp3.read_bytes()).hexdigest()
        reports[name] = report
        manifest[category][name if category != "ambience" else "room"] = {
            "url": f"./assets/audio/management_v1/{name}.mp3", "seconds": len(data) / SR,
            "gain": gain, "loop": loop, "bytes": mp3.stat().st_size,
            "sha256": report["mp3_sha256"], **extra,
        }
        all_data[name] = data
        print(f"Built {name}: {len(data)/SR:.3f}s, {mp3.stat().st_size} bytes", flush=True)

    for name in ("menu", "service", "rush"):
        emit(name, compose_music(name), "music", 1, True, bpm=80 if name == "menu" else 96,
             bars=16 if name == "menu" else 24, key="C major", beatsPerBar=4,
             syncGroup="menu_80" if name == "menu" else "service_96_cmajor_24bars")
    gains = {
        "ui_click": .45, "door_bell": .7, "ticket_paper": .72, "patty_down": .72,
        "grill_sizzle": .22, "food_ready": .85, "food_burnt": .85, "onion_crunch": .7,
        "leaf_rustle": .72, "wet_topping": .7, "cheese_fold": .72, "tray_pickup": .68,
        "serve_cash": .8, "wrong_action": .7, "customer_left": .55,
        "shift_closed": .78, "upgrade": .78, "footstep_tile": .26,
    }
    for name, data in build_sfx().items():
        emit(name, data, "sfx", gains[name], name == "grill_sizzle")
    emit("ambient_room", room_ambience(), "ambience", 1, True)
    # Contrast the three actual tracks and then identify every short event.
    preview_parts = []
    for name in ("menu", "service", "rush"):
        excerpt = all_data[name][:8 * SR].copy() * .60
        fade = round(.15 * SR)
        excerpt[:fade] *= np.linspace(0, 1, fade)[:, None]
        excerpt[-fade:] *= np.linspace(1, 0, fade)[:, None]
        preview_parts.append(excerpt)
        preview_parts.append(np.zeros((round(.5 * SR), 2), dtype=np.float32))
    write_wav(OUT / "music_comparison_preview.wav", np.concatenate(preview_parts))
    subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(OUT / "music_comparison_preview.wav"),
                    "-codec:a", "libmp3lame", "-b:a", "112k", str(OUT / "music_comparison_preview.mp3")], check=True)
    preview_parts = []
    sfx_names = list(manifest["sfx"])
    for name in sfx_names:
        excerpt = all_data[name] if name != "grill_sizzle" else all_data[name][:SR]
        preview_parts += [excerpt * .8, np.zeros((round(.35 * SR), 2), dtype=np.float32)]
    write_wav(OUT / "sfx_sequence_preview.wav", np.concatenate(preview_parts))
    subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(OUT / "sfx_sequence_preview.wav"),
                    "-codec:a", "libmp3lame", "-b:a", "80k", str(OUT / "sfx_sequence_preview.mp3")], check=True)
    for destination in (OUT / "manifest.json", GAME / "manifest.json"):
        destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "passed": True, "music_count": 3, "sfx_count": 18, "ambience_count": 1, "total_game_assets": 22,
        "game_audio_bytes": sum(x.stat().st_size for x in GAME.glob("*.mp3")),
        "master_wav_bytes": sum(x.stat().st_size for x in MASTER.glob("*.wav")),
        "service_rush_identical_frames": reports["service"]["sample_frames"] == reports["rush"]["sample_frames"],
        "all_masters_non_clipping_non_silent": all(x["clipped_samples"] == 0 and x["audible"] for x in reports.values()),
        "all_loop_mp3_decode_gapless_exact_frames": all(x["mp3_gapless_exact_frame_count"] for x in reports.values() if x["loop"]),
        "non_loop_max_encoder_padding_frames": max(abs(x["mp3_padding_frames"]) for x in reports.values() if not x["loop"]),
        "all_loop_seams_within_normal_transient_range": all(x["seam_within_normal_transient_range"] for x in reports.values() if x["loop"]),
        "all_loop_mp3_seams_within_normal_transient_range": all(x["mp3_seam_within_normal_transient_range"] for x in reports.values() if x["loop"]),
        "reports": reports, "sfx_preview_order": sfx_names,
        "audit_limit": "Technical signal checks are objective; timbre is synthesized rather than field-recorded and musical taste requires listening.",
    }
    (OUT / "audio_qa.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "README_audio_design.txt").write_text(DESIGN_NOTES, encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("reports", "sfx_preview_order")}, ensure_ascii=False), flush=True)


DESIGN_NOTES = """ONE MORE DINER — Original Restaurant Management Audio / 原创经营音频
Created: 2026-10-13. All files generated locally on D drive.

音乐方向 / Music direction
轻松、微微古怪的复古餐厅器乐爵士，无唱词、对白、惊悚段落。
全部音符及节奏为本项目原创 DSP 合成，不使用既有歌曲或第三方录音。
电钢琴负责和声和主旋律，拨弦感贝斯提供行走律动，刷鼓轻拍，木琴少量回应。
旋律有完整问答、留白、八度变化；避免连续单一提示音。
菜单 menu：48 秒，80 BPM，16 小节，C 大调/maj7，温暖慢速，进入游戏前播放。
营业 service：60 秒，96 BPM，24 小节，C 大调，营业时低音量循环。
忙碌 rush：60 秒，96 BPM，完全相同和声、旋律网格；增加轻刷鼓与小木块节奏。
service/rush 需同时运行同一个 AudioContext 时钟并共用循环起点，2.5 秒交叉淡化。
不能从头重新启动 rush；可以持续运行零音量另一轨，或按同一 elapsed % 60 偏移启动。
菜单切营业可以短淡出/淡入。暂停/隐藏页面挂起上下文，恢复后延续时间相位。
Use decoded AudioBuffer loops with LAME gapless metadata; loop lengths are exact.
Two sub-second non-loop effects have at most 29 encoder padding samples (0.66 ms);
this does not affect loop phase or event duration perceptibly.

触发 / Event triggers (all 18 assets are actually generated)
ui_click: valid menu/settings/button press; quiet wooden tap.
door_bell: customer enters through door; two soft shop chimes.
ticket_paper: order accepted at customer's table; short paper tear/rustle.
patty_down: raw patty contacts grill or food placed on prep board; damp low thud.
grill_sizzle: 4-second loop, only while an active patty grills; stop on removal.
food_ready: once when patty becomes cooked; audible ascending three-note cue.
food_burnt: once on burnt threshold; brief low descending reminder.
onion_crunch: diced onion or onion rings added; crisp little crunches.
leaf_rustle: lettuce added; light crinkled leaf rustle.
wet_topping: tomato or pickle slices added; short damp plop.
cheese_fold: cheese slice added; soft flexible-sheet sound.
tray_pickup: completed tray picked up; muted metal tray clink.
serve_cash: correct meal physically handed to table and money charged; tiny cash chime.
wrong_action: rejected action/wrong table/recipe/empty stock; short gentle low cue.
customer_left: only for disappointed departure, no loud punishment sting.
shift_closed: end-of-day accounting shown; short four-note cadence.
upgrade: upgrade successfully paid/applied; small affirmative ascent.
footstep_tile: actual first-person grounded movement, alternate small pitch 0.96/1.04;
limit to about 0.4–0.5 seconds per step, no sounds while paused/stationary.
ambient_room: independent 8-second very quiet air/refrigerator bed; no fake voices.

混音 / Mix
Master 0.8, Music bus 0.34, SFX bus 0.75, Ambient bus 0.08.
Manifest individual music and ambient gain is 1; bus values apply once.
Important food-ready/burnt/customer-door cues briefly duck music about 5 dB.
Limit UI click rate, footsteps and topping overlap; max 8 simultaneous SFX voices.
Grill loop 0.22 local asset gain, ideally position-based attenuation by kitchen distance.
Separate Music / SFX / Ambient settings; all browser sound requires user gesture unlock.
Stock alerts and gameplay cues remain louder and clearer than background music.

交付 / Delivery
masters/: 22 original 44.1 kHz, stereo, 16-bit PCM WAV masters.
web_demo_v1/dist/assets/audio/management_v1/: 22 small MP3 game assets + manifest.json.
music_comparison_preview.mp3: menu/service/rush, eight seconds each, 0.5-second gaps.
sfx_sequence_preview.mp3: manifest order, 0.35-second gaps, sizzle excerpt one second.
audio_qa.json: peak/RMS/no clipping/no silence/sample-exact durations/loop seams/MP3 decode.
Signal checks do not substitute for human taste. Effects are crafted synthetic materials,
not presented as real field recordings. No copyrighted musical quotation or sampled audio.
"""


if __name__ == "__main__":
    main()
