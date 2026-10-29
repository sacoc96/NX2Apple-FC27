# FIFA 18 (`0100F7B002340000`)

Base game 1.0.0 (v0), SDK 3.4.0: EA's RNA renderer (SportsRNA, `RNA::DevicePlatC`) on NVN, the Reveal / Apt front end, EA's audio core. Modules `main`, `subsdk0` (GLSLC) and `sdk`. Plays on the Mac from the base NSP (packed with `--platform mac`): boot, menus, kit and team selection and full matches at 60 fps with sound, rendered at 2560x1440 docked. Not tested on the iPhone yet.

## What it needs

| Setting | Where | Why |
|---|---|---|
| Back buffer 2560x1440 docked | [`patches.py`](patches.py) | RNA picks {1920, 1080} docked / {1280, 720} handheld at device init (`main+0x1189bcc`) and on an operation-mode change (`main+0x118a420`); the four cuts raise the docked size, and every scene target follows (see [Resolution](#resolution)) |
| `tex_dyn_slots on` | [`game.tsv`](game.tsv) | `texcompface.fxo`, which composes the players' faces at run time, picks one of 8 combined handles from the driver table by its loop index; without the key the shader does not load and generated faces stay blank |
| Pool arrays for `815a1b91fe6f921b`, `84559f9769271907`, `01446bfafa5a2637` | [`shader_facts_manual.tsv`](shader_facts_manual.tsv) | the player cursor and markers (`indicator`, `indicator_luminance`) and the flags read a handle that names a pool entry directly ([handles that name a pool entry directly](../../../docs/reference/shaders.md#handles-that-name-a-pool-entry-directly-pool-arrays)); 4096 textures and 1024 samplers cover the IDs the game registers (about 2,040 and 620) |
| 4 GB layout: `mem_reserve 0x100000000`, `mem_alias 0x10000000`, `mem_stack 0x10000000`, `app_pool 0xCD500000`, `mem_used 0x7000000` | `game.tsv` | the NSP script's guess: no system resource in the NPDM, `main` sets a heap; no allocation failure through full matches |

## Files and shaders

- The data is in EA BIG4 archives (`data*.big`; `data3.big` is the `romfs_marker`). The shader archives `data/fifarna/shader.big` and `shaderboot.big` are wrapped in EASF: AES-128-CBC with the IV equal to the key, the key stored in `main` after the name `datax   ` and checked against the SHA-256 in the header, then chunkzip (raw deflate chunks). [`eabig.py`](../../gfx/tools/eabig.py) lists and unwraps them, and `shader_split.py` reads the GLSLC outputs inside ([GLSLC outputs in EA's encrypted BIG archives](../../../docs/reference/shaders.md#glslc-outputs-in-eas-encrypted-big-archives)). chunzstd (method 6) is not read; the game's shaders do not use it.
- Some compute shaders carry a control section longer than its +0x20 field says, with headerless code after it; the section headers give the right code offset ([headerless compute code](../../../docs/reference/shaders.md#headerless-compute-code-after-a-control-section-longer-than-its-0x20)). The SH irradiance prefilter (`ad6448a83337e2ef`) is one: with the wrong offset the light probe came out NaN and the players were black.

## Resolution

The window textures and RNA's back buffer globals (`main+0x10a14ec` → GOT `main+0x48f1100` / `+0x48f1108`) take the size the cuts set, and the render framework sizes its targets from those. A pass dump of a match shows 28 attachments at 2560x1440, the quarter-size ones at 640x360 and none left at 1920x1080; the HUD, the radar and the menus scale with it. On an M-series Mac a match holds 60 fps (frame p50 16.7 ms, GPU p50 8.5 ms). Handheld stays 1280x720, so on the iPhone the launcher's **Console mode** chooses between 1440p (Docked, the default) and 720p (Handheld).

## Found on this game

- [Index zero-extended by an and with 0xffffffff](../../../docs/reference/rewriter.md#index-zero-extended-by-an-and-with-0xffffffff): a jump table whose index is masked by `and xD, xS, #0xffffffff` stopped the rewriter (`jump table 25442e4`).
- [AudioUnit start on a small guest stack](../../../docs/reference/audio.md#audiounit-start-on-a-small-guest-stack): `AudioOutputUnitStart` crashed in `___chkstk_darwin` on the game's audio thread; it now runs on a host thread.
- [Integer views for images a shader declares uint or int](../../../docs/reference/rendering.md#integer-views-for-images-a-shader-declares-uint-or-int), compute dispatches: `compress_bc3` reads an RGBA8 image as `r32ui`; without the upgrade before the dispatch the first face composed came out yellow.
- [Handles that name a pool entry directly (pool arrays)](../../../docs/reference/shaders.md#handles-that-name-a-pool-entry-directly-pool-arrays): the player cursor, markers and flags (a translation chain change).
- The two EA shader-container entries above.

## Checked and left as is

- **Menu animations.** They looked faster than on the Switch. The front end's thread hands Apt the time that passed (16 ms per update at 60 fps), and its accumulated clocks advanced 2,976 ms in 3.09 s of wall time; a 30 Hz present cap (`DM_PRESENT_HZ=30`) did not change how they looked, so nothing counts frames. The tile highlight completes in about 0.1 s, as the game times it. On the Switch, loading stalls hold the front end (it skips updates whose render time passed 250 ms, `MAX_ELAPSED_ION_RENDER_TIME_MS`).
- **The 30 Hz request.** The game sets `gVsync` 2 in menus (`main+0x503f7e4`), but `RenderFramework::BeginFrame` (`main+0x105efc8`) follows it with `SetVSyncInterval(5)`, which `main+0x10a13d4` maps to interval 1: the game presents at interval 1 everywhere, on the Switch too.
- The EA Stopwatch frequency is the system tick's 19.2 MHz (`main+0x4775550`); its conversion factors match.

## Open

- **MetalFX present upscaling crashes the game.** Two runs with `DM_PRESENT_UPSCALE=metalfx` (1440p and 1080p) crashed in game code reading objects whose fields an EA allocation fill (`0xcd`) or another write had replaced (`main+0xbc4df0`, `main+0x1c8394`); the same builds without it ran a full match. The scaler adds about 5 ms of GPU per present on the game's queue and only touches its own textures, so the crash is likely a host timing issue the extra GPU latency exposes. Keep upscaling off for this game until it is found.
- **Fullscreen on the Mac drops to 30 fps.** Going fullscreen stalled the display link for 5.4 s; after the recovery the presents stayed at 33.3 ms with the game at interval 1 and the GPU at 9 ms. Windowed, or `DM_PRESENT_LINK=0`, keeps 60 fps.
- **A guest thread (`0x100f`, priority 45) spins at 100% of a core** from the middle of a match on; the frame rate is unaffected, but it costs power on a phone.
- The `combiner` bloom pass binds a cube texture to slot 2 of `590c135fc414c2ee` (one `[RED] texture type mismatch` line), and one cube view of 1 + 1 layers past the 6 faces; no visible effect found.
- `nvnQueueGetTotal*MemoryUsed`, `nvnQueueResetMemoryUsageCounts`, `nvnCommandBufferGetControlMemoryFree` and `nvnCommandBufferSetSubpixelPrecisionBias` are unimplemented (logged every frame; the game only reads statistics from them).
- Flags in the stadium not checked closely.
- `pso_manifest.tsv` is not recorded (no prewarm). Not tested on the iPhone. Only the base game was packed; no update is known.
