# EA SPORTS FC 27 (0100C49025D3E000): the rewriter's patches of this game's own builds (provisional profile). CUTS as in dm/tools/patch_nso.py ("Registered patches").
# None: 60 fps comes from the time regulator's render frequency, which the host holds at the profile's fps_target (dm/host/hle_fpslock.c). Two cuts tried before it are gone:
#   main+0x99ea5a0 (the pacer's 1.0 → 0.5): 60 presents of 30 pictures, the interpolation still stepped at 30;
#   main+0x7feb434 / main+0x9a8d10 (a settings mode word read as 1): the first only feeds a reported metric ("renFrameRate", main+0x99d6d0), the frame rate stayed 30
CUTS = {}
