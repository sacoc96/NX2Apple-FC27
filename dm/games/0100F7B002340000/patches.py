# FIFA 18 (0100F7B002340000): the rewriter's patches of this game's own builds. dm/tools/patch_nso.py loads every profile's patches.py and applies those of a module's
# NSO build ID; CUTS as described there ("Registered patches").
CUTS = {
  # FIFA 18 1.0.0 (v0) main: RNA's back buffer size. Device init (main+0x1189bcc, the stack config passed to main+0x109f4a8) and the operation-mode handler (main+0x118a420, passed to
  # DevicePlatC's resize at main+0x10a41d0) pick {1920, 1080} docked and {1280, 720} handheld; the size reaches the window textures and the globals the render framework sizes its
  # targets from (main+0x10a14ec → GOT main+0x48f1100 / +0x48f1108). Docked becomes 2560x1440:
  # every scene target follows (a pass dump of a match: 28 attachments at 2560x1440, the quarter-size ones at 640x360, none left at 1920x1080), the HUD and the menus scale with it, and a
  # match holds 60 fps on an M-series Mac (GPU p50 8.5 ms). Handheld stays 1280x720, so the iOS launcher's console mode chooses between the two
  '36cffaaac1363c53a9aafb9488b502cd': [
    (0x1189bcc, 'e80f19b2', '084081d2', 'device init docked back buffer: mov x8,#0x78000000780 → mov x8,#0xa00 (width 2560)'),
    (0x1189bd0, '0887c0f2', '08b4c0f2', 'device init docked back buffer: movk x8,#0x438,lsl #32 → movk x8,#0x5a0,lsl #32 (height 1440)'),
    (0x118a420, 'eb0f1932', '0b408152', 'operation-mode change docked width: orr w11,wzr,#0x780 → mov w11,#0xa00 (2560)'),
    (0x118a430, '09878052', '09b48052', 'operation-mode change docked height: mov w9,#0x438 → mov w9,#0x5a0 (1440)'),
  ],
}
