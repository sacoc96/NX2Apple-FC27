#!/usr/bin/env python3
# NSO modules with ZBIC-compressed segments → the same modules with their segments stored uncompressed, so every tool that reads an NSO (LZ4 or stored segments) reads them.
# Flags bit 7 (system 22.0.0 on, UseZbicCompression): the compressed segments (bits 0-2) are ZBIC instead of LZ4: a zstd variant with its own frame magic 'ZBIC' and binary
# interpolative coding of the entropy tables (EA SPORTS FC 27 1.8d's main: all three segments, the text 194 MB from 69 MB). Decoded with kinnay's zbic package (pip install zbic: zstd
# from Atmosphère built with ZSTD_ZBIC_SUPPORT). Each decoded segment is checked against the SHA-256 the header records for it; the rewritten module keeps the header's other fields
# (module ID, hashes and their check bits, bit 6 ExecuteOnlyMemory, the dynamic symbol table offsets) with bits 0-2 and 7 cleared, segments stored at new file offsets.
# Usage: nso_unzbic.py <ExeFS dir or NSO file>... (rewrites in place; modules without bit 7 are left as they are)
import hashlib, os, struct, sys

ZBIC_FLAG = 0x80

def is_zbic(path):
    try:
        with open(path, 'rb') as f: h = f.read(0x10)
    except OSError: return False
    return len(h) == 0x10 and h[:4] == b'NSO0' and struct.unpack_from('<I', h, 0xc)[0] & ZBIC_FLAG != 0

def unzbic(path):
    """rewrites one NSO in place; returns the decoded sizes of its segments"""
    try: import zbic
    except ImportError: raise SystemExit(f'[RED] {path}: ZBIC-compressed NSO (system 22.0.0 format); the zbic Python package decodes it: pip install zbic')
    d = open(path, 'rb').read()
    flags = struct.unpack_from('<I', d, 0xc)[0]
    segs = [struct.unpack_from('<III', d, 0x10 + 0x10 * i) for i in range(3)]   # file offset, memory offset, size
    csz = struct.unpack_from('<3I', d, 0x60)
    out_segs = []
    for i, (fo, mo, sz) in enumerate(segs):
        raw = d[fo:fo + csz[i]]
        if flags >> i & 1:
            raw = zbic.decompress(raw)
            if len(raw) != sz: raise SystemExit(f'[RED] {path}: segment {i} decodes to {len(raw):#x} bytes, the header says {sz:#x}')
        if hashlib.sha256(raw).digest() != d[0xa0 + 0x20 * i:0xc0 + 0x20 * i]: raise SystemExit(f'[RED] {path}: segment {i} does not match its SHA-256 after decoding')
        out_segs.append(raw)
    h = bytearray(d[:0x100])
    struct.pack_into('<I', h, 0xc, flags & ~(ZBIC_FLAG | 7))
    off, body = 0x100, b''
    for i, raw in enumerate(out_segs):
        struct.pack_into('<I', h, 0x10 + 0x10 * i, off); struct.pack_into('<I', h, 0x60 + 4 * i, len(raw))
        body += raw; off += len(raw)
    tmp = path + '.unzbic'
    with open(tmp, 'wb') as f: f.write(bytes(h) + body)
    os.replace(tmp, path)
    return [len(r) for r in out_segs]

def unzbic_dir(d):
    """every ZBIC NSO in an ExeFS folder → stored; returns [(name, segment sizes)]"""
    done = []
    for n in sorted(os.listdir(d)):
        p = os.path.join(d, n)
        if os.path.isfile(p) and is_zbic(p): done.append((n, unzbic(p)))
    return done

if __name__ == '__main__':
    for a in sys.argv[1:]:
        for n, s in (unzbic_dir(a) if os.path.isdir(a) else [(a, unzbic(a))] if is_zbic(a) else []):
            print(f'{n}: ZBIC segments stored uncompressed ({", ".join(f"{x / 2**20:.1f} MB" for x in s)})')
