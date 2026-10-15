ONE MORE DINER — Original Restaurant Management Audio / 原创经营音频
Created: 2026-10-13. All files generated locally on D drive.

音乐方向 / Music direction
轻松、微微古怪的复古餐厅器乐爵士，无唱词、对白、惊悚段落。
全部音符及节奏为本项目原创 DSP 合成，不使用既有歌曲或第三方录音。
电钢琴负责和声和主旋律，拨弦感贝斯提供行走律动，刷鼓轻拍，木琴少量回应。
旋律有完整问答、留白、八度变化；避免连续单一提示音。
菜单 menu：48 秒，80 BPM，16 小节，C 大调/maj7，温暖慢速，进入游戏前播放。
营业 service：60 秒，96 BPM，24 小节，C 大调，营业时低音量循环。
忙碌 rush：60 秒，96 BPM，完全相同和声、旋律网格；增加轻刷鼓与小木块节奏。
service/rush 同时运行同一个 AudioContext 时钟并共用循环起点，使用 0.6 秒时间常数的指数交叉淡化。
不能从头重新启动 rush；可以持续运行零音量另一轨，或按同一 elapsed % 60 偏移启动。
菜单切营业平滑淡出/淡入。明确暂停时静音游戏声；隐藏页面时挂起上下文，恢复后保留循环相位。
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
footstep_tile: actual first-person grounded movement, one step per 0.68 m travel,
with a minimum 0.22-second interval; no sound while paused/stationary or after a camera reset.
ambient_room: independent 8-second very quiet air/refrigerator bed; no fake voices.

混音 / Mix
Default user controls: Master 0.65, Music 0.40, Sound effects 0.80, Ambience 0.30.
Music also applies the manifest musicBus 0.34; the room loop applies ambienceBus 0.08.
Manifest individual music and room gain is 1; each corresponding bus factor applies once.
Food-ready, food-burnt, serve and wrong-action cues duck music to 0.52 amplitude
(approximately -5.7 dB) for 0.8 seconds. Customer arrival does not duck music.
UI clicks, steps and repeated warnings have cooldowns; there is no eight-voice hard cap.
Grill loop 0.22 local asset gain, ideally position-based attenuation by kitchen distance.
Separate Music / SFX / Ambient settings; all browser sound requires user gesture unlock.
Settings are saved on the device; a 2.8-second Test Audio audition temporarily
mutes the normal mix, respects all volume controls, and preserves paused game state.
Stock alerts and gameplay cues remain louder and clearer than background music.

交付 / Delivery
masters/: 22 original 44.1 kHz, stereo, 16-bit PCM WAV masters.
web_demo_v1/dist/assets/audio/management_v1/: 22 small MP3 game assets + manifest.json.
music_comparison_preview.mp3: menu/service/rush, eight seconds each, 0.5-second gaps.
sfx_sequence_preview.mp3: manifest order, 0.35-second gaps, sizzle excerpt one second.
audio_qa.json: peak/RMS/no clipping/no silence/sample-exact durations/loop seams/MP3 decode.
Signal checks do not substitute for human taste. Effects are crafted synthetic materials,
not presented as real field recordings. No copyrighted musical quotation or sampled audio.
