#!/usr/bin/env python3
# EA's archives and file wrappers, as FIFA 18 (EA's FIFA engine, "fifarna" renderer, SDK 3.4.0) keeps them in its RomFS:
#   · BIG4 / BIGF archives (*.big, an index *.bh beside each that the game reads first; the reader here needs only the .big): 'BIG4', u32 archive size (little-endian), then big-endian
#     u32 entry count, u32 header length, and per entry big-endian u32 offset, u32 size and a NUL-terminated path. Members may be archives of their own (data/fifarna/shader.big inside datax.big).
#   · EASF ("EA secure file"): 'EASF', big-endian u32 plain size, an 8-byte key name ("datax   "), the SHA-256 of the first 32 plain bytes, then from +0x30 the data, AES-128-CBC with the key
#     as its IV and no padding (the last block is cut to the plain size). AssetStream::Loader::LoadingUpdate (main+0x2af5f0 on 1.0.0) asks Fifa::AssetStreamCryptoKeyProvider::GetKey for the key
#     by name, decrypts the first 32 bytes, checks them against the hash and goes on with the rest in the same CBC chain. GetKey returns a key built into main for "datax   " (a table of
#     {8-byte name, 16-byte key} in its read-only data) and looks any other name up in a database (GetKeyFromDB). find_key takes the 16 bytes after each copy of the name in main and keeps the
#     one the header's hash confirms; no key is stored anywhere else, and none is printed.
#   · chunkzip: 'chunkzip', big-endian u32 version (2), plain size, chunk size (0x28000), chunk count, alignment (16); each chunk's data starts at the next aligned offset with
#     {u32 stored size, u32 method} (big-endian) in the 8 bytes before it; method 1 is raw deflate, 0 stored.
# FIFA 18's shaders: datax.big → data/fifarna/shader.big (EASF → chunkzip → BIG4, 174 .fxo) and shaderboot.big (15 .fxo); each .fxo is an 'NXSHADER' file holding one GLSLC output
# of a vertex and a pixel shader (or one compute shader), which shader_split.py's glslc_shaders reads: 368 shaders.
# Usage: eabig.py list <archive.big>   |   eabig.py extract <archive.big> <member path> <main NSO> <output file>   (EASF and chunkzip layers removed)
import hashlib, os, struct, sys, zlib

BIG, EASF, CHUNKZIP = (b'BIG4', b'BIGF'), b'EASF', b'chunkzip'

def entries(d):
    """[(path, offset, size)] of a BIG archive's index; d = the archive's bytes, or at least its header"""
    if d[:4] not in BIG: raise ValueError(f'not a BIG archive (magic {d[:4]!r})')
    n, hs = struct.unpack_from('>II', d, 8)
    out, p = [], 16
    for _ in range(n):
        off, size = struct.unpack_from('>II', d, p); p += 8
        e = d.index(b'\0', p); out.append((d[p:e].decode('latin1'), off, size)); p = e + 1
    return out

def file_entries(path):
    """entries() of a BIG archive on disk, reading only its index"""
    with open(path, 'rb') as f:
        h = f.read(16)
        if h[:4] not in BIG: raise ValueError(f'not a BIG archive (magic {h[:4]!r})')
        return entries(h + f.read(struct.unpack_from('>I', h, 12)[0] - 16))

def read(path, e):
    with open(path, 'rb') as f: f.seek(e[1]); return f.read(e[2])

def cbc_decrypt(key, iv, data):
    """AES-CBC decryption through AES-ECB (CommonCrypto, uepak.aes_decrypt): P[i] = D(C[i]) ^ C[i-1], C[-1] = iv"""
    import uepak
    n = len(data) // 16 * 16
    if not n: return b''
    p = uepak.aes_decrypt(key, data[:n])
    prev = iv + data[:n - 16]
    return (int.from_bytes(p, 'little') ^ int.from_bytes(prev, 'little')).to_bytes(n, 'little')

def easf_name(head): return head[8:16]

def find_key(img, name, head):
    """The 16-byte key for EASF files with this key name: the bytes after a copy of the name in main's image that decrypt head's first block pair to the hash in head; None when none does"""
    if len(head) < 0x50: return None
    i = img.find(name)
    while i >= 0:
        k = bytes(img[i + 8:i + 24])
        if len(k) == 16 and hashlib.sha256(cbc_decrypt(k, k, head[0x30:0x50])).digest() == head[0x10:0x30]: return k
        i = img.find(name, i + 1)
    return None

def easf(d, key):
    """The plain bytes of an EASF file"""
    if d[:4] != EASF: raise ValueError('not an EASF file')
    n = struct.unpack_from('>I', d, 4)[0]
    out = cbc_decrypt(key, key, d[0x30:])
    if hashlib.sha256(out[:32]).digest() != d[0x10:0x30]: raise ValueError('EASF: the key does not match the header hash')
    if len(out) < n: raise ValueError(f'EASF: {len(out)} bytes for a plain size of {n}')
    return out[:n]

def chunkzip(d):
    """The inflated bytes of a chunkzip file"""
    if d[:8] != CHUNKZIP: raise ValueError('not a chunkzip file')
    ver, total, _, n, align = struct.unpack_from('>5I', d, 8)
    if not align: raise ValueError('chunkzip: alignment 0')
    out, p = bytearray(), 0x1c
    for _ in range(n):
        ds = (p + 8 + align - 1) // align * align
        size, method = struct.unpack_from('>II', d, ds - 8)
        blob = d[ds:ds + size]; p = ds + size
        if method == 1: out += zlib.decompress(blob, -15)
        elif method == 0: out += blob
        else: raise ValueError(f'chunkzip: chunk method {method} at {ds:#x}')
    if len(out) != total: raise ValueError(f'chunkzip: {len(out)} bytes for a plain size of {total}')
    return bytes(out)

def unwrap(d, keys):
    """d with its EASF and chunkzip layers removed; keys = {key name: key}. Raises KeyError for an EASF key name not in keys"""
    while True:
        if d[:4] == EASF: d = easf(d, keys[easf_name(d)])
        elif d[:8] == CHUNKZIP: d = chunkzip(d)
        else: return d

def _nso(path):
    import lz4.block
    d = open(path, 'rb').read()
    flags = struct.unpack_from('<I', d, 0xc)[0]; segs = [struct.unpack_from('<III', d, 0x10 + i * 0x10) for i in range(3)]; csz = struct.unpack_from('<III', d, 0x60)
    img = bytearray(segs[2][1] + segs[2][2])
    for i, (fo, mo, sz) in enumerate(segs):
        raw = d[fo:fo + csz[i]]
        img[mo:mo + sz] = lz4.block.decompress(raw, uncompressed_size=sz) if flags >> i & 1 else raw
    return bytes(img)

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'list':
        for nm, off, size in file_entries(sys.argv[2]): print(f'{nm}\t{off:#x}\t{size}')
    elif len(sys.argv) == 6 and sys.argv[1] == 'extract':
        e = next((e for e in file_entries(sys.argv[2]) if e[0] == sys.argv[3]), None)
        if e is None: sys.exit(f'{sys.argv[3]} is not in {sys.argv[2]}')
        d = read(sys.argv[2], e); keys = {}
        if d[:4] == EASF:
            k = find_key(_nso(sys.argv[4]), easf_name(d), d[:0x50])
            if k is None: sys.exit(f'no key for the EASF key name {easf_name(d)!r} in {sys.argv[4]}')
            keys[easf_name(d)] = k
        with open(sys.argv[5], 'wb') as f: f.write(unwrap(d, keys))
    else: sys.exit('usage: eabig.py list <archive.big> | eabig.py extract <archive.big> <member path> <main NSO> <output file>')
