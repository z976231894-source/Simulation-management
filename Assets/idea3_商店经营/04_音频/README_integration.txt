ONE MORE DINER — Management audio, 2026-10-13

The active management demo uses original, locally composed audio assets.
The old audio.js is retained for historical story source; management-app.js
imports management-audio.js instead.

MUSIC
Menu: 48-second warm electric-piano / bass / brushed-drum loop at 80 BPM.
Service: 60-second light diner groove at 96 BPM.
Rush: the same 60-second chord/melody grid with extra percussion, selected
when two or more accepted orders are waiting. Both service tracks share
one AudioContext start time and crossfade without restarting.

SOUND EFFECTS
18 effects cover UI, door arrivals, accepted orders, patty placement,
grill sizzling, food-ready / burnt thresholds, onion / lettuce / wet
toppings / cheese, tray pickup, paid delivery, rejected actions,
disappointed departures, shift summary, upgrades and actual footsteps.
The 8-second room loop has no voice recordings.

PLAYBACK
First real click or key press unlocks browser sound. All 22 small MP3s
(about 2.57 MB) are fetched once and decoded into reusable buffers.
Music, sound effects, ambience and master volume are separate controls,
saved with look sensitivity under one_more.management.preferences.v1.
Explicit pause fades game audio to silence. Hiding the page immediately
silences audio, clears pending one-shots and suspends the audio context.
Test Audio is a bounded 2.8-second audition, with the ordinary mix muted.
It respects volume settings and does not resume paused cooking/customers.
Grill sound only runs for active cooking and attenuates with distance.
Successful actions and natural state transitions trigger cues; rejected
actions do not play success sounds. Event IDs are scoped per game run.

FILES ON D DRIVE
Game assets: dist/assets/audio/management_v1/manifest.json
Original WAV masters, two previews, design notes and asset QA:
D:/idea美术资产详解/idea3/audio/management_v1/
Generator: D:/idea美术资产详解/idea3/tools/build_management_audio.py

VALIDATION
Nine audio lifecycle tests and eight management tests pass.
Independent asset audit: hashes, decode lengths, finite samples,
no clipping and sample-exact seamless loops.
Native browser checks: real output signal, menu/service switch, arrival
chimes, movement-only footsteps, pause silence, paused preview,
independent volumes, master mute and persisted settings after reload.
Native evidence: qa/audio_management_v1/native_browser.json
