#!/usr/bin/env python3
# A Frostbite cas file decoded block by block into one file (shader_split.py fbcas_shaders' walk), for studying what the decoded chunks hold.
# Usage: DM_OODLE_HOST=<dmhost> DM_OODLE_MODULES=<patched dir> fbcas_dump.py <cas> <out> ; also writes <out>.blocks.tsv: per block, cas offset, decoded offset, decoded size, compression
import os, sys, struct, re, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shader_split as S
cas, outp = sys.argv[1], sys.argv[2]
import mmap
with open(cas, 'rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as d, open(outp, 'wb') as o, open(outp + '.blocks.tsv', 'w') as t:
    i, pos = 0, 0
    while i < len(d):
        h = S.fb_block(d, i)
        if h is None or (i + 8 + h[2] < len(d) and S.fb_block(d, i + 8 + h[2]) is None):
            m = S.FB_HDR.search(d, i + 1)
            if not m: break
            t.write(f'{i:#x}\tgap\t{m.start() - i}\n'); i = m.start(); continue
        n, comp, size = h; raw = d[i + 8:i + 8 + size]; kind = S.FB_COMP[comp]
        try:
            data = raw[:n] if kind == 'stored' else S.oodle_try(raw, n) if kind == 'oodle' else S.zstd_mod().decompress(raw) if kind == 'zstd' else zlib.decompress(raw) if kind == 'zlib' else None
        except Exception: data = None
        if data is None or len(data) != n: t.write(f'{i:#x}\tfail\t{kind}\n'); i += 1; continue
        t.write(f'{i:#x}\t{pos:#x}\t{n:#x}\t{kind}\t{d[i]:#x}\n'); o.write(data); pos += n; i += 8 + size
print(f'{cas}: {pos / 2**20:.1f} MB decoded → {outp}')
