#!/usr/bin/env python3
"""Completes the run-time shader capture of a game whose shaders exist only as NVN programs the game sets at run time (EA SPORTS FC 27; the game profile's nvn_capture.tsv lists them).

Run it after a build (build_ipa_from_nsp.py, any --platform) of the same NSP folder: it starts the game in a window with sound, with the shaders captured so far, and saves every
program the game sets that is not captured yet to <build>/extract/<version>/nvn_capture. Play through what the automatic pass of the build did not reach (the menus, the Manager and
Player Career, cutscenes, a full match): the console line says how many shaders are captured. When the capture is complete, close the game and run the build again.

Usage: python3 scripts/nvn_capture_play.py "<NSP folder>" [-l <language, e.g. it>] [--work-dir <build folder>]
"""
import argparse, os, shutil, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def profile_dir(tid, work):
    for d in (REPO / 'dm/games' / tid, work / 'profile' / tid):
        if (d / 'game.tsv').is_file(): return d
    return None


def keys_of(t):
    return {l.strip() for l in open(t) if l.strip() and not l.startswith('#')}


def done(cap):
    return ({p.stem for p in cap.glob('*.ctl')} & {p.stem for p in cap.glob('*.code')}) if cap.is_dir() else set()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('nsp_dir', help='the folder holding the game\'s NSPs (the one the build ran on)')
    ap.add_argument('-l', '--language', default=os.environ.get('DM_LANG', 'en-US'), help='game language code (default en-US): it, fr, de, es, ...')
    ap.add_argument('--work-dir', help='the build folder (default: the only <title ID>_build folder in the NSP folder with a run-time capture profile)')
    a = ap.parse_args()
    nsp = Path(os.path.expanduser(a.nsp_dir)).resolve()
    works = [Path(os.path.expanduser(a.work_dir)).resolve()] if a.work_dir else sorted(p for p in nsp.glob('*_build') if p.is_dir())
    work = next((w for w in works if (p := profile_dir(w.name.split('_')[0], w)) and (p / 'nvn_capture.tsv').is_file()), None)
    if not work: sys.exit(f'no build folder of a game with a run-time shader capture (nvn_capture.tsv) in {nsp}: run scripts/build_ipa_from_nsp.py on it first')
    tid = work.name.split('_')[0]; prof = profile_dir(tid, work)
    vers = sorted(p.name for p in (work / 'extract').iterdir() if (p / 'RomFS').is_dir()) if (work / 'extract').is_dir() else []
    ver = next((v for v in vers if (work / f'patched_{v}').is_dir()), None)
    host, patched = work / 'tools/dmhost', work / f'patched_{ver}'
    if not ver or not host.is_file() or not (work / 'shader/cache').is_dir():
        sys.exit(f'{work} has no complete build yet (extracted files, patched code, Mac host and shader libraries): run scripts/build_ipa_from_nsp.py on {nsp} first')
    want = keys_of(prof / 'nvn_capture.tsv'); cap = work / 'extract' / ver / 'nvn_capture'; cap.mkdir(parents=True, exist_ok=True)
    have = done(cap) & want
    print(f'shader capture: {len(have)} of {len(want)} shaders captured ({cap})')
    if have >= want:
        print('the capture is already complete: run the build again to use it'); return 0
    # The shader map the host gets: only the captured shaders (their libraries exist), so the host saves every other program the game sets; c1_full.tsv and cb_extent.tsv go beside it
    rd = work / 'run'; tmp = work / 'tmp/nvn_capture_play'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    for d in ('save', 'temp'): (rd / d).mkdir(parents=True, exist_ok=True)
    rows = [l for l in open(prof / 'shader_map.tsv') if l.startswith('#') or (len(c := l.split('\t')) > 4 and (c[3] in have or c[3] == 'dm_ctl_sha16'))]
    (tmp / 'shader_map.tsv').write_text(''.join(rows))
    for n in ('c1_full.tsv', 'cb_extent.tsv', 'shader_facts.tsv', 'pso_manifest.tsv', 'pso_pairs.tsv', 'shader_pairs.tsv'):
        if (prof / n).is_file(): shutil.copyfile(prof / n, tmp / n)
    env = dict(os.environ, DM_ROOT=str(work), DM_ROMFS=str(work / 'extract' / ver / 'RomFS'), DM_SAVE=str(rd / 'save'), DM_TEMP=str(rd / 'temp'), DM_MSL_DIR=str(work / 'shader/cache'),
               DM_NVN_SHMAP=str(tmp / 'shader_map.tsv'), DM_NVN_SHDUMP=str(cap), DM_LANG=a.language, DM_WINDOW='1', DM_AUDIO='1', DM_PRESENT_UPSCALE='metalfx')
    if (work / 'font').is_dir(): env['DM_FONT_DIR'] = str(work / 'font')
    if (work / 'aoc').is_dir(): env['DM_AOC_DIR'] = str(work / 'aoc')
    log = work / 'logs/nvn_capture_play.log'; log.parent.mkdir(exist_ok=True)
    print('starting the game: play through the menus, the careers, the cutscenes and a full match; close the game window when the capture is complete')
    with open(log, 'w') as f:
        p = subprocess.Popen([str(host), str(patched)], env=env, cwd=rd, stdout=f, stderr=subprocess.STDOUT)
        shown = len(have)
        try:
            while p.poll() is None:
                time.sleep(5)
                n = len(done(cap) & want)
                if n != shown:
                    shown = n; print(f'  {n} of {len(want)} shaders captured' + ('  — complete: close the game and run the build again' if n >= len(want) else ''), flush=True)
        except KeyboardInterrupt:
            p.terminate(); p.wait()
    n = len(done(cap) & want)
    print(f'shader capture: {n} of {len(want)} shaders captured.' + (' Complete: run the build again.' if n >= len(want) else ' Run this again later to capture the rest; the next build uses what is there.'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
