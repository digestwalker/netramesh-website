#!/usr/bin/env python3
"""Build NetraMesh brand assets from the uploaded logo (pure stdlib, no deps):
  - assets/img/logo-icon.png   (tight eye+mesh icon, transparent) for navbar/footer
  - assets/img/favicon.png     (64x64, eye icon centered)
  - assets/img/og-image.png    (1200x630 share card, real logo composited)
"""
import zlib, struct, math, os

# Paths are relative to this script (tools/), so the repo is portable.
IMGDIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "img"))
SRC = os.path.join(IMGDIR, "NetraMeshLabs.png")

# ===================== PNG decode (8-bit RGBA) =====================
def decode_png(path):
    d = open(path, "rb").read()
    pos = 8; W = Hh = 0; idat = b''
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

# ===================== area-average downscale (premultiplied) =====================
def downscale(src, sw, sh, x0, y0, x1, y1, tw, th):
    out = bytearray(tw*th*4)
    bw = (x1-x0)/tw; bh = (y1-y0)/th
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
                out[oo+2] = min(255, int(ab/aa)); out[oo+3] = int(aa/max(n,1)*255)
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

# ===================== build icon + favicon =====================
SW, SH, SRCPX = decode_png(SRC)
# icon lives left of the gap (~x448); text is to the right
ix0, iy0, ix1, iy1 = content_bbox(SRCPX, SW, SH, 0, 448)
icw, ich = ix1-ix0, iy1-iy0
print(f"icon bbox: x{ix0}-{ix1} y{iy0}-{iy1}  ({icw}x{ich})")

# logo-icon.png : preserve aspect, target height 160
LH = 160; LW = round(icw * LH / ich)
icon_full = downscale(SRCPX, SW, SH, ix0, iy0, ix1, iy1, LW, LH)
write_png(IMGDIR + "/logo-icon.png", LW, LH, icon_full)
print("logo-icon.png", LW, "x", LH)

# favicon.png : 64x64, icon centered (fit width)
FS = 64; pad = 4; fw = FS-2*pad; fh = round(ich * fw / icw)
if fh > FS-2*pad: fh = FS-2*pad; fw = round(icw*fh/ich)
fav_icon = downscale(SRCPX, SW, SH, ix0, iy0, ix1, iy1, fw, fh)
fav = bytearray(FS*FS*4)
ox = (FS-fw)//2; oy = (FS-fh)//2
for y in range(fh):
    for x in range(fw):
        s = (y*fw+x)*4; dpx = ((oy+y)*FS+(ox+x))*4
        fav[dpx:dpx+4] = fav_icon[s:s+4]
write_png(IMGDIR + "/favicon.png", FS, FS, fav)
print("favicon.png 64x64")

# apple-touch-icon.png : 180x180, solid navy background, eye centered
AS = 180; NAVY = (15, 23, 42)
atouch = bytearray(AS*AS*4)
for i in range(AS*AS):
    o = i*4; atouch[o]=NAVY[0]; atouch[o+1]=NAVY[1]; atouch[o+2]=NAVY[2]; atouch[o+3]=255
aw = 150; ah = round(ich*aw/icw)
ai = downscale(SRCPX, SW, SH, ix0, iy0, ix1, iy1, aw, ah)
axo = (AS-aw)//2; ayo = (AS-ah)//2
for y in range(ah):
    for x in range(aw):
        s = (y*aw+x)*4; a = ai[s+3]/255.0
        if a > 0:
            dp = ((ayo+y)*AS+(axo+x))*4
            atouch[dp]   = int(NAVY[0]*(1-a)+ai[s]*a)
            atouch[dp+1] = int(NAVY[1]*(1-a)+ai[s+1]*a)
            atouch[dp+2] = int(NAVY[2]*(1-a)+ai[s+2]*a)
            atouch[dp+3] = 255
write_png(IMGDIR + "/apple-touch-icon.png", AS, AS, atouch)
print("apple-touch-icon.png 180x180")

# ===================== OG image 1200x630 =====================
W, H = 1200, 630
buf = bytearray(W*H*3)
NAVY_TOP=(8,13,26); NAVY_BOT=(15,23,42); EBLUE=(30,136,229); LBLUE=(103,192,255)
WHITE=(248,250,252); SLATE=(120,139,168); DIMBLUE=(26,54,96)

def setpx(x, y, c, a=1.0):
    if 0 <= x < W and 0 <= y < H:
        i = (y*W+x)*3
        if a >= 1.0: buf[i], buf[i+1], buf[i+2] = c
        else:
            buf[i]=int(buf[i]*(1-a)+c[0]*a); buf[i+1]=int(buf[i+1]*(1-a)+c[1]*a); buf[i+2]=int(buf[i+2]*(1-a)+c[2]*a)

gx, gy, gr = 930, 150, 560
for y in range(H):
    t = y/(H-1)
    br=int(NAVY_TOP[0]+(NAVY_BOT[0]-NAVY_TOP[0])*t); bg=int(NAVY_TOP[1]+(NAVY_BOT[1]-NAVY_TOP[1])*t); bb=int(NAVY_TOP[2]+(NAVY_BOT[2]-NAVY_TOP[2])*t)
    row=(y*W)*3
    for x in range(W):
        r,g,b=br,bg,bb; d=math.hypot(x-gx,y-gy)
        if d<gr:
            f=(1-d/gr)**2*0.45; r=min(255,int(r+EBLUE[0]*f)); g=min(255,int(g+EBLUE[1]*f)); b=min(255,int(b+EBLUE[2]*f))
        i=row+x*3; buf[i],buf[i+1],buf[i+2]=r,g,b

def line(x0,y0,x1,y1,c,a=1.0):
    dx=abs(x1-x0);dy=abs(y1-y0);sx=1 if x0<x1 else -1;sy=1 if y0<y1 else -1;err=dx-dy
    while True:
        setpx(x0,y0,c,a)
        if x0==x1 and y0==y1:break
        e2=2*err
        if e2>-dy:err-=dy;x0+=sx
        if e2<dx:err+=dx;y0+=sy
def disc(cx,cy,r,c,a=1.0):
    for yy in range(cy-r,cy+r+1):
        for xx in range(cx-r,cx+r+1):
            if (xx-cx)**2+(yy-cy)**2<=r*r: setpx(xx,yy,c,a)
def rect(x,y,w,h,c):
    for yy in range(y,y+h):
        for xx in range(x,x+w): setpx(xx,yy,c)

# decorative mesh upper-right
nodes=[(770,70),(880,130),(1010,90),(1110,180),(960,210),(820,230),(1060,290),(900,310),(1140,90),(740,170)]
for i,(ax,ay) in enumerate(nodes):
    for (bx,by) in nodes[i+1:]:
        if math.hypot(ax-bx,ay-by)<170: line(ax,ay,bx,by,DIMBLUE,0.55)
for (ax,ay) in nodes: disc(ax,ay,3,LBLUE,0.7)

# composite REAL logo icon (downscaled) onto OG
OGIH = 116
ogiw = round(icw*OGIH/ich)
ogicon = downscale(SRCPX, SW, SH, ix0, iy0, ix1, iy1, ogiw, OGIH)
lx, ly = 92, 64
for y in range(OGIH):
    for x in range(ogiw):
        s=(y*ogiw+x)*4; a=ogicon[s+3]/255.0
        if a>0: setpx(lx+x, ly+y, (ogicon[s],ogicon[s+1],ogicon[s+2]), a)

# ---- 5x7 font ----
FONT={'A':["  #  "," # # "," # # ","#   #","#####","#   #","#   #"],'B':["#### ","#   #","#   #","#### ","#   #","#   #","#### "],'C':[" ####","#    ","#    ","#    ","#    ","#    "," ####"],'D':["#### ","#   #","#   #","#   #","#   #","#   #","#### "],'E':["#####","#    ","#    ","#### ","#    ","#    ","#####"],'F':["#####","#    ","#    ","#### ","#    ","#    ","#    "],'G':[" ####","#    ","#    ","#  ##","#   #","#   #"," ####"],'H':["#   #","#   #","#   #","#####","#   #","#   #","#   #"],'I':["#####","  #  ","  #  ","  #  ","  #  ","  #  ","#####"],'J':["#####","   # ","   # ","   # ","#  # ","#  # "," ##  "],'K':["#   #","#  # ","# #  ","##   ","# #  ","#  # ","#   #"],'L':["#    ","#    ","#    ","#    ","#    ","#    ","#####"],'M':["#   #","## ##","# # #","#   #","#   #","#   #","#   #"],'N':["#   #","##  #","# # #","#  ##","#   #","#   #","#   #"],'O':[" ### ","#   #","#   #","#   #","#   #","#   #"," ### "],'P':["#### ","#   #","#   #","#### ","#    ","#    ","#    "],'Q':[" ### ","#   #","#   #","#   #","# # #","#  # "," ## #"],'R':["#### ","#   #","#   #","#### ","# #  ","#  # ","#   #"],'S':[" ####","#    ","#    "," ### ","    #","    #","#### "],'T':["#####","  #  ","  #  ","  #  ","  #  ","  #  ","  #  "],'U':["#   #","#   #","#   #","#   #","#   #","#   #"," ### "],'V':["#   #","#   #","#   #","#   #","#   #"," # # ","  #  "],'W':["#   #","#   #","#   #","#   #","# # #","## ##","#   #"],'X':["#   #","#   #"," # # ","  #  "," # # ","#   #","#   #"],'Y':["#   #","#   #"," # # ","  #  ","  #  ","  #  ","  #  "],'Z':["#####","    #","   # ","  #  "," #   ","#    ","#####"],'0':[" ### ","#   #","#  ##","# # #","##  #","#   #"," ### "],'1':["  #  "," ##  ","  #  ","  #  ","  #  ","  #  ","#####"],'2':[" ### ","#   #","    #","   # ","  #  "," #   ","#####"],'3':["#####","   # ","  #  ","   # ","    #","#   #"," ### "],'4':["   # ","  ## "," # # ","#  # ","#####","   # ","   # "],'5':["#####","#    ","#### ","    #","    #","#   #"," ### "],'6':[" ### ","#    ","#    ","#### ","#   #","#   #"," ### "],'7':["#####","    #","   # ","  #  "," #   "," #   "," #   "],'8':[" ### ","#   #","#   #"," ### ","#   #","#   #"," ### "],'9':[" ### ","#   #","#   #"," ####","    #","    #"," ### "],' ':["     ","     ","     ","     ","     ","     ","     "],'.':["     ","     ","     ","     ","     ","  ## ","  ## "],',':["     ","     ","     ","     ","  ## ","  ## "," #   "],'/':["    #","    #","   # ","  #  "," #   ","#    ","#    "],'&':[" ##  ","#  # ","#  # "," ##  ","# # #","#  # "," ## #"],'-':["     ","     ","     ","#####","     ","     ","     "],':':["     ","  ## ","  ## ","     ","  ## ","  ## ","     "],'·':["     ","     ","  #  "," ### ","  #  ","     ","     "]}
def text_w(s,sc): return len(s)*6*sc-sc
def text(x,y,s,sc,c):
    for ch in s.upper():
        g=FONT.get(ch,FONT[' '])
        for r in range(7):
            rb=g[r]
            for col in range(5):
                if rb[col]=='#':
                    px=x+col*sc;py=y+r*sc
                    for dy in range(sc):
                        for dx in range(sc): setpx(px+dx,py+dy,c)
        x+=6*sc

# wordmark next to icon
wx = lx + ogiw + 26
for s,c in [("NETRA",WHITE),("MESH",LBLUE),(" LABS",SLATE)]:
    text(wx, 92, s, 6, c); wx += text_w(s,6)+6*6

rect(92,212,74,7,EBLUE)
text(90,240,"CYBER DEFENSE,",7,WHITE)
text(90,312,"WOVEN INTO ONE MESH.",7,LBLUE)
text(92,398,"INTEGRATED SECURITY OPERATIONS PLATFORM",3,SLATE)
line(92,446,1108,446,DIMBLUE,0.8)
text(92,474,"SIEM · SOAR · UEBA · CMDB · SOC · SANDBOX",4,LBLUE)
dom="NETRAMESH.COM"; text(1108-text_w(dom,4),540,dom,4,WHITE)
text(92,540,"CYBER TECHNOLOGY",4,SLATE)

write_png(IMGDIR + "/og-image.png", W, H, buf, rgb_only=True)
print("og-image.png 1200x630")
