#!/usr/bin/env python3
"""Build NetraMesh Labs brand assets from the uploaded logo (pure stdlib, no deps):
  - assets/img/logo-icon.png        (eye+mesh icon, transparent) for navbar/footer
  - assets/img/favicon.png          (64x64)
  - assets/img/apple-touch-icon.png (180x180, navy bg)
  - assets/img/og-image.png         (1200x630 share card)

The OG card uses a hand-built ANTI-ALIASED monoline vector font (not a bitmap),
so its typography reads clean/modern and stays consistent with the site.
"""
import zlib, struct, math, os

IMGDIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "img"))
SRC = os.path.join(IMGDIR, "NetraMeshLabs.png")

# ===================== PNG decode (8-bit RGBA) =====================
def decode_png(path):
    d = open(path, "rb").read(); pos = 8; W = Hh = 0; idat = b''
    while pos < len(d):
        ln = struct.unpack(">I", d[pos:pos+4])[0]; typ = d[pos+4:pos+8]
        data = d[pos+8:pos+8+ln]; pos += 12+ln
        if typ == b'IHDR': W, Hh = struct.unpack(">II", data[:8])
        elif typ == b'IDAT': idat += data
        elif typ == b'IEND': break
    raw = zlib.decompress(idat); bpp = 4; stride = W*bpp
    out = bytearray(); prev = bytearray(stride); i = 0
    def paeth(a, b, c):
        p = a+b-c; pa = abs(p-a); pb = abs(p-b); pc = abs(p-c)
        return a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
    for y in range(Hh):
        f = raw[i]; i += 1; line = bytearray(raw[i:i+stride]); i += stride
        if f == 1:
            for x in range(bpp, stride): line[x] = (line[x]+line[x-bpp]) & 255
        elif f == 2:
            for x in range(stride): line[x] = (line[x]+prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x-bpp] if x >= bpp else 0
                line[x] = (line[x]+((a+prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x-bpp] if x >= bpp else 0
                c = prev[x-bpp] if x >= bpp else 0
                line[x] = (line[x]+paeth(a, prev[x], c)) & 255
        out += line; prev = line
    return W, Hh, out

def write_png(path, w, h, rgba, rgb_only=False):
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data +
                struct.pack(">I", zlib.crc32(typ+data) & 0xffffffff))
    ct = 2 if rgb_only else 6
    ihdr = struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, 0)
    bpp = 3 if rgb_only else 4
    stride = w*bpp; raw = bytearray()
    for y in range(h):
        raw.append(0); raw += rgba[y*stride:(y+1)*stride]
    idat = zlib.compress(bytes(raw), 9)
    with open(path, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b''))

def downscale(src, sw, sh, x0, y0, x1, y1, tw, th):
    out = bytearray(tw*th*4); bw = (x1-x0)/tw; bh = (y1-y0)/th
    for ty in range(th):
        iy0 = int(y0+ty*bh); iy1 = max(int(math.ceil(y0+(ty+1)*bh)), iy0+1)
        for tx in range(tw):
            ix0 = int(x0+tx*bw); ix1 = max(int(math.ceil(x0+(tx+1)*bw)), ix0+1)
            ar = ag = ab = aa = 0.0; n = 0
            for yy in range(iy0, min(iy1, sh)):
                base = yy*sw
                for xx in range(ix0, min(ix1, sw)):
                    o = (base+xx)*4; a = src[o+3]/255.0
                    ar += src[o]*a; ag += src[o+1]*a; ab += src[o+2]*a; aa += a; n += 1
            oo = (ty*tw+tx)*4
            if aa > 0:
                out[oo] = min(255, int(ar/aa)); out[oo+1] = min(255, int(ag/aa))
                out[oo+2] = min(255, int(ab/aa)); out[oo+3] = int(aa/max(n, 1)*255)
            else:
                out[oo+3] = 0
    return out

def content_bbox(src, sw, sh, xmin, xmax):
    x0 = sw; y0 = sh; x1 = 0; y1 = 0
    for y in range(sh):
        base = y*sw
        for x in range(xmin, min(xmax, sw)):
            if src[(base+x)*4+3] > 30:
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
    return x0, y0, x1+1, y1+1

# ===================== icon / favicon / apple =====================
SW, SH, SRCPX = decode_png(SRC)
ix0, iy0, ix1, iy1 = content_bbox(SRCPX, SW, SH, 0, 448)
icw, ich = ix1-ix0, iy1-iy0
print(f"icon bbox: {icw}x{ich}")

LH = 160; LW = round(icw*LH/ich)
write_png(IMGDIR + "/logo-icon.png", LW, LH, downscale(SRCPX, SW, SH, ix0, iy0, ix1, iy1, LW, LH))
print("logo-icon.png", LW, "x", LH)

FS = 64; pad = 4; fw = FS-2*pad; fh = round(ich*fw/icw)
if fh > FS-2*pad: fh = FS-2*pad; fw = round(icw*fh/ich)
fav_icon = downscale(SRCPX, SW, SH, ix0, iy0, ix1, iy1, fw, fh)
fav = bytearray(FS*FS*4); ox = (FS-fw)//2; oy = (FS-fh)//2
for y in range(fh):
    for x in range(fw):
        s = (y*fw+x)*4; fav[((oy+y)*FS+(ox+x))*4:((oy+y)*FS+(ox+x))*4+4] = fav_icon[s:s+4]
write_png(IMGDIR + "/favicon.png", FS, FS, fav); print("favicon.png 64x64")

AS = 180; NAVY = (15, 23, 42)
atouch = bytearray(AS*AS*4)
for i in range(AS*AS):
    o = i*4; atouch[o] = NAVY[0]; atouch[o+1] = NAVY[1]; atouch[o+2] = NAVY[2]; atouch[o+3] = 255
aw = 150; ah = round(ich*aw/icw); ai = downscale(SRCPX, SW, SH, ix0, iy0, ix1, iy1, aw, ah)
axo = (AS-aw)//2; ayo = (AS-ah)//2
for y in range(ah):
    for x in range(aw):
        s = (y*aw+x)*4; a = ai[s+3]/255.0
        if a > 0:
            dp = ((ayo+y)*AS+(axo+x))*4
            atouch[dp] = int(NAVY[0]*(1-a)+ai[s]*a); atouch[dp+1] = int(NAVY[1]*(1-a)+ai[s+1]*a)
            atouch[dp+2] = int(NAVY[2]*(1-a)+ai[s+2]*a); atouch[dp+3] = 255
write_png(IMGDIR + "/apple-touch-icon.png", AS, AS, atouch); print("apple-touch-icon.png 180x180")

def make_icon(size, bg=None, padfrac=0.08):
    pad = int(size*padfrac); iw = size-2*pad; ih = round(ich*iw/icw)
    if ih > size-2*pad: ih = size-2*pad; iw = round(icw*ih/ich)
    ic = downscale(SRCPX, SW, SH, ix0, iy0, ix1, iy1, iw, ih)
    out = bytearray(size*size*4)
    if bg:
        for i in range(size*size):
            o = i*4; out[o] = bg[0]; out[o+1] = bg[1]; out[o+2] = bg[2]; out[o+3] = 255
    ox = (size-iw)//2; oy = (size-ih)//2
    for y in range(ih):
        for x in range(iw):
            s = (y*iw+x)*4; a = ic[s+3]/255.0
            if a <= 0: continue
            dp = ((oy+y)*size+(ox+x))*4
            if bg:
                out[dp] = int(bg[0]*(1-a)+ic[s]*a); out[dp+1] = int(bg[1]*(1-a)+ic[s+1]*a)
                out[dp+2] = int(bg[2]*(1-a)+ic[s+2]*a); out[dp+3] = 255
            else:
                out[dp:dp+4] = ic[s:s+4]
    return out
# transparent tab favicons + opaque PWA icons (navy)
write_png(IMGDIR + "/favicon-16.png", 16, 16, make_icon(16)); print("favicon-16.png")
write_png(IMGDIR + "/favicon-32.png", 32, 32, make_icon(32)); print("favicon-32.png")
write_png(IMGDIR + "/icon-192.png", 192, 192, make_icon(192, NAVY, 0.14)); print("icon-192.png")
write_png(IMGDIR + "/icon-512.png", 512, 512, make_icon(512, NAVY, 0.14)); print("icon-512.png")

# ===================== OG image 1200x630 =====================
W, H = 1200, 630
buf = bytearray(W*H*3)
NAVY_TOP = (8, 13, 26); NAVY_BOT = (15, 23, 42); EBLUE = (30, 136, 229)
LBLUE = (103, 192, 255); WHITE = (248, 250, 252); SLATE = (128, 147, 176); DIMBLUE = (26, 54, 96)

def setpx(x, y, c, a=1.0):
    xi = int(x); yi = int(y)
    if 0 <= xi < W and 0 <= yi < H and a > 0:
        i = (yi*W+xi)*3
        if a >= 1: buf[i], buf[i+1], buf[i+2] = c
        else:
            buf[i] = int(buf[i]*(1-a)+c[0]*a); buf[i+1] = int(buf[i+1]*(1-a)+c[1]*a); buf[i+2] = int(buf[i+2]*(1-a)+c[2]*a)

# background gradient + radial glow
gx, gy, gr = 930, 150, 560
for y in range(H):
    t = y/(H-1)
    br = int(NAVY_TOP[0]+(NAVY_BOT[0]-NAVY_TOP[0])*t); bg = int(NAVY_TOP[1]+(NAVY_BOT[1]-NAVY_TOP[1])*t); bb = int(NAVY_TOP[2]+(NAVY_BOT[2]-NAVY_TOP[2])*t)
    row = y*W*3
    for x in range(W):
        r, g, b = br, bg, bb; d = math.hypot(x-gx, y-gy)
        if d < gr:
            f = (1-d/gr)**2*0.42; r = min(255, int(r+EBLUE[0]*f)); g = min(255, int(g+EBLUE[1]*f)); b = min(255, int(b+EBLUE[2]*f))
        i = row+x*3; buf[i], buf[i+1], buf[i+2] = r, g, b

def line_seg(x0, y0, x1, y1, c, w, a=1.0):
    """Anti-aliased thick segment (rounded) via distance field."""
    minx = int(min(x0, x1)-w-1); maxx = int(max(x0, x1)+w+1)
    miny = int(min(y0, y1)-w-1); maxy = int(max(y0, y1)+w+1)
    dx = x1-x0; dy = y1-y0; L2 = dx*dx+dy*dy
    hw = w/2.0
    for py in range(miny, maxy+1):
        for px in range(minx, maxx+1):
            if L2 == 0: dist = math.hypot(px-x0, py-y0)
            else:
                tt = ((px-x0)*dx+(py-y0)*dy)/L2
                tt = 0 if tt < 0 else (1 if tt > 1 else tt)
                dist = math.hypot(px-(x0+tt*dx), py-(y0+tt*dy))
            cov = hw - dist + 0.5
            if cov > 0: setpx(px, py, c, min(1.0, cov)*a)

def disc(cx, cy, r, c, a=1.0):
    for py in range(int(cy-r-1), int(cy+r+2)):
        for px in range(int(cx-r-1), int(cx+r+2)):
            cov = r - math.hypot(px-cx, py-cy) + 0.5
            if cov > 0: setpx(px, py, c, min(1.0, cov)*a)

def polyline(pts, sx, sy, s, c, w):
    for k in range(len(pts)-1):
        line_seg(sx+pts[k][0]*s, sy+pts[k][1]*s, sx+pts[k+1][0]*s, sy+pts[k+1][1]*s, c, w)

def arc(cx, cy, rx, ry, a0, a1, n=14):
    return [[cx+rx*math.cos(math.radians(a)), cy+ry*math.sin(math.radians(a))]
            for a in [a0+(a1-a0)*i/n for i in range(n+1)]]

# ---- monoline vector font (glyph = list of polylines in a 6x10 unit box, y down) ----
def _bowl(cx, cy, rx, ry): return arc(cx, cy, rx, ry, -90, 90, 9)
G = {
 'A': [[[0.6,9.2],[3,0.8],[5.4,9.2]],[[1.7,6.2],[4.3,6.2]]],
 'B': [[[1,0.8],[1,9.2]]] + [_bowl(1,2.85,3.3,2.05)] + [_bowl(1,7.05,3.8,2.15)],
 'C': [arc(3,5,2.4,4.2,52,308,16)],
 'D': [[[1,0.8],[1,9.2]], arc(1,5,4.2,4.2,-90,90,12)],
 'E': [[[1,0.8],[1,9.2]],[[1,0.8],[5,0.8]],[[1,5],[4.3,5]],[[1,9.2],[5,9.2]]],
 'F': [[[1,0.8],[1,9.2]],[[1,0.8],[5,0.8]],[[1,5],[4.3,5]]],
 'G': [arc(3,5,2.4,4.2,52,310,16),[[5.0,5.3],[3.3,5.3]],[[5.0,5.3],[5.0,7.6]]],
 'H': [[[1,0.8],[1,9.2]],[[5,0.8],[5,9.2]],[[1,5],[5,5]]],
 'I': [[[3,0.8],[3,9.2]],[[1.8,0.8],[4.2,0.8]],[[1.8,9.2],[4.2,9.2]]],
 'K': [[[1,0.8],[1,9.2]],[[1,5.3],[5,0.8]],[[1.9,4.3],[5,9.2]]],
 'L': [[[1,0.8],[1,9.2],[5,9.2]]],
 'M': [[[1,9.2],[1,0.8],[3,4.8],[5,0.8],[5,9.2]]],
 'N': [[[1,9.2],[1,0.8],[5,9.2],[5,0.8]]],
 'O': [arc(3,5,2.3,4.15,0,360,20)],
 'P': [[[1,0.8],[1,9.2]]] + [_bowl(1,2.8,3.6,2.0)],
 'R': [[[1,0.8],[1,9.2]]] + [_bowl(1,2.8,3.6,2.0)] + [[[2.6,4.8],[5.2,9.2]]],
 'S': [[[5,2.3],[3.4,0.9],[1.6,1.7],[1.5,3.5],[3,4.9],[4.5,6.1],[4.5,7.9],[2.8,9.1],[1,7.9]]],
 'T': [[[0.8,0.8],[5.2,0.8]],[[3,0.8],[3,9.2]]],
 'U': [[[1,0.8],[1,6.4]]] + [arc(3,6.4,2,2.7,0,180,10)] + [[[5,6.4],[5,0.8]]],
 'V': [[[0.8,0.8],[3,9.2],[5.2,0.8]]],
 'W': [[[0.6,0.8],[1.9,9.2],[3,4.4],[4.1,9.2],[5.4,0.8]]],
 'Y': [[[0.9,0.8],[3,5],[5.1,0.8]],[[3,5],[3,9.2]]],
 '-': [[[1.4,5],[4.6,5]]],
 '/': [[[1,9.2],[5,0.8]]],
}
def text_w(s, txt): return len(txt)*7*s
def text(x, ytop, txt, s, c):
    w = max(1.5, s*0.78)
    for ch in txt.upper():
        if ch == ' ': x += 7*s; continue
        if ch == '.': disc(x+3*s, ytop+8.7*s, max(1.3, s*0.85), c)
        elif ch == ',':
            disc(x+3*s, ytop+8.7*s, max(1.3, s*0.85), c); line_seg(x+3*s, ytop+8.7*s, x+2.3*s, ytop+10.2*s, c, w*0.8)
        elif ch == '·': disc(x+3*s, ytop+5*s, max(1.4, s*0.95), c)
        elif ch in G:
            for pl in G[ch]: polyline(pl, x, ytop, s, c, w)
        x += 7*s

# decorative mesh (upper-right)
nodes = [(770,70),(880,130),(1010,90),(1110,180),(960,210),(820,235),(1060,295),(905,315),(1140,95),(745,175)]
for i,(ax,ay) in enumerate(nodes):
    for (bx,by) in nodes[i+1:]:
        if math.hypot(ax-bx, ay-by) < 170: line_seg(ax, ay, bx, by, DIMBLUE, 1.2, 0.5)
for (ax,ay) in nodes: disc(ax, ay, 3, LBLUE, 0.75)

# real logo (composited)
OGIH = 96; ogiw = round(icw*OGIH/ich)
ogicon = downscale(SRCPX, SW, SH, ix0, iy0, ix1, iy1, ogiw, OGIH)
lx, ly = 88, 66
for y in range(OGIH):
    for x in range(ogiw):
        s = (y*ogiw+x)*4; a = ogicon[s+3]/255.0
        if a > 0: setpx(lx+x, ly+y, (ogicon[s], ogicon[s+1], ogicon[s+2]), a)

# wordmark beside logo
wx = lx + ogiw + 26
text(wx, 92, "NETRA", 4.0, WHITE);  wx += text_w(4.0, "NETRA")
text(wx, 92, "MESH", 4.0, LBLUE);   wx += text_w(4.0, "MESH")
text(wx, 92, " LABS", 4.0, SLATE)

# accent bar + headline
line_seg(94, 214, 162, 214, EBLUE, 7)
text(90, 238, "CYBER DEFENSE,", 6.2, WHITE)
text(90, 312, "WOVEN INTO ONE MESH.", 6.2, LBLUE)

# rallying cry
text(92, 398, "SECURITY WITHOUT GATEKEEPERS", 2.7, SLATE)

# divider + chips + footer line
line_seg(92, 452, 1108, 452, DIMBLUE, 1.4, 0.85)
text(92, 478, "SIEM · SOAR · UEBA · CMDB · SOC · NIDS", 3.0, LBLUE)
text(92, 544, "OPEN SECOPS INITIATIVE", 2.5, SLATE)
dom = "NETRAMESH.COM"
text(1108-text_w(3.4, dom), 540, dom, 3.4, WHITE)

write_png(IMGDIR + "/og-image.png", W, H, buf, rgb_only=True)
print("og-image.png 1200x630")
