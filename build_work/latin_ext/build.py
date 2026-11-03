"""latin_ext: add the 154 missing letters of Latin Extended Additional U+1E00..U+1E9B to HuiwenMincho-AI-v2.1.

Run (from anywhere):  PYTHONDONTWRITEBYTECODE=1 python3 -I build.py
Reads   ../../HuiwenMincho-AI-v2.1.ttf  (never written)
Writes  HuiwenMincho-AI-v2.1.latin_ext.ttf  (= main font + ONLY the new glyphs uniXXXX), latin_ext_result.json
Checks  every original glyph (glyf bytes), hmtx, vmtx and every original cmap entry is unchanged; only the new code points are added.

Recipe (same conventions as the accepted Vietnamese letters U+1EA0..U+1EF9):
 * bases  = the font's own rough letters (ASCII letters, dotless i for i with marks above, long s for U+1E9B), copied unchanged.
 * marks  = WHOLE contours of the font's own marks, never sliced (no cut edges):
            grave À/à, acute Ó/é, circumflex Ô/ô, tilde õ (capitals: enlarged, as in Vietnamese), dot Ö/ä, diaeresis Ö/ä,
            macron Ū/ō, caron Č/č, breve = the breve of ĕ (THE breve), ring = the degree sign °, cedilla = the separate
            cedilla contours of Ȩ/ȩ (attached exactly like the font's Ȩ ȩ Ş Ţ), small right half ring = our ’.
            Below-marks are the same marks placed under the letter (line below = macron, at full weight, never a hairline).
 * reduced marks are re-thickened to the stroke weight by raster union + re-trace (allowed by the user), then given back a
   letterpress wobble; every placed mark has its own jitter seed, so no two copies are identical.
 * stacking follows the NFD order outward from the letter; capitals: lower mark reduced/flattened (<= 15%), the upper one as big
   as the room under y=910 allows (Windows clip line usWinAscent=915); small letters stay under 862 where possible.
 * dot above on b d h: beside the ascender over the x-height part; on f, long s, k, l, t: above the top, over the stem.
"""
import os, json, unicodedata as U
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image, ImageDraw
from scipy import ndimage as nd
import contourpy

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.abspath(os.path.join(HERE, '..', '..', 'HuiwenMincho-AI-v2.1.ttf'))
OUT = os.path.join(HERE, 'HuiwenMincho-AI-v2.1.latin_ext.ttf')
RESULT = os.path.join(HERE, 'latin_ext_result.json')

f = TTFont(MAIN, recalcTimestamp=False)      # byte-deterministic output (head.modified kept)
gs = f.getGlyphSet(); CM = dict(f.getBestCmap()); GL = f['glyf']
ORIG_ORDER = list(f.getGlyphOrder())
TARGETS = [c for c in range(0x1E00, 0x1E9C) if c not in CM and U.name(chr(c), '')]
assert len(TARGETS) == 154, len(TARGETS)

# ---------------------------------------------------------------- geometry
class Flat(BasePen):
    def __init__(s): super().__init__(gs); s.cs = []; s.cur = None
    def _moveTo(s, p): s.cur = [p]
    def _lineTo(s, p): s.cur.append(p)
    def _qCurveToOne(s, a, c):
        p0 = s.cur[-1]
        for t in np.linspace(0, 1, 9)[1:]:
            u = 1 - t; s.cur.append((u*u*p0[0] + 2*u*t*a[0] + t*t*c[0], u*u*p0[1] + 2*u*t*a[1] + t*t*c[1]))
    def _curveToOne(s, a, b, c):
        p0 = s.cur[-1]
        for t in np.linspace(0, 1, 11)[1:]:
            u = 1 - t
            s.cur.append((u**3*p0[0] + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*c[0], u**3*p0[1] + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*c[1]))
    def _closePath(s):
        if s.cur and len(s.cur) > 2: s.cs.append(np.array(s.cur, float))
        s.cur = None
    _endPath = _closePath

def G(ch):
    """all contours of the glyph of character ch (polylines, original orientation)"""
    p = Flat(); gs[CM[ord(ch)]].draw(p); return p.cs
def ADV(ch): return f['hmtx'][CM[ord(ch)]][0]
def area(p): return 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
def bb(cs):
    a = np.vstack(cs); return a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max()
def T(cs, dx=0.0, dy=0.0): return [p + np.array([dx, dy]) for p in cs]
def A(cs, sx, sy): return [p * np.array([sx, sy]) for p in cs]
def S(cs, s): return A(cs, s, s)
def norm(cs):
    x0, y0, x1, y1 = bb(cs); return T(cs, -(x0 + x1) / 2, -y0)
def W_(cs): x0, y0, x1, y1 = bb(cs); return x1 - x0
def H_(cs): x0, y0, x1, y1 = bb(cs); return y1 - y0
def put(cs, cx=None, y0=None, y1=None, x0=None, x1=None):
    a, b, c, d = bb(cs); dx = dy = 0.0
    if cx is not None: dx = cx - (a + c) / 2
    if x0 is not None: dx = x0 - a
    if x1 is not None: dx = x1 - c
    if y0 is not None: dy = y0 - b
    if y1 is not None: dy = y1 - d
    return T(cs, dx, dy)

def resample(p, step=5.0):
    q = np.vstack([p, p[:1]]); seg = np.hypot(*np.diff(q, axis=0).T); L = seg.sum()
    n = max(12, int(L / step)); cum = np.r_[0, np.cumsum(seg)]; t = np.linspace(0, L, n, endpoint=False)
    return np.stack([np.interp(t, cum, q[:, 0]), np.interp(t, cum, q[:, 1])], 1)

def jitter(cs, seed, amp=1.1):
    """letterpress wobble: smooth random displacement along the normal (keeps orientation)"""
    rng = np.random.default_rng(seed); out = []
    for p in cs:
        q = resample(p, 5.0); n = len(q)
        d = np.roll(q, -1, 0) - np.roll(q, 1, 0); d /= np.maximum(1e-9, np.hypot(d[:, 0], d[:, 1]))[:, None]
        nrm = np.stack([d[:, 1], -d[:, 0]], 1)
        w = rng.normal(size=n + 6); k = np.array([1, 2, 3, 2, 1.]) / 9
        low = np.convolve(w, k, 'same')[3:3 + n]; low = (low - low.mean()) / (low.std() + 1e-9)
        out.append(q + nrm * (amp * (0.8 * low + 0.3 * rng.normal(size=n)))[:, None])
    return out

# ---------------- raster union + re-trace (used to re-thicken reduced marks; allowed by the user)
R = 4.0          # pixels per font unit
def retrace(cs, grow=0.0):
    x0, y0, x1, y1 = bb(cs); pad = grow + 8; ox, oy = x0 - pad, y1 + pad
    Wd = int((x1 - x0 + 2 * pad) * R) + 2; Ht = int((y1 - y0 + 2 * pad) * R) + 2
    acc = np.zeros((Ht, Wd), np.int32)
    for p in cs:            # nonzero winding fill
        im = Image.new('L', (Wd, Ht), 0)
        ImageDraw.Draw(im).polygon([((x - ox) * R, (oy - y) * R) for x, y in p], fill=1)
        acc += np.asarray(im, np.int32) * (1 if area(p) < 0 else -1)
    m = acc != 0
    if grow > 0: m = nd.distance_transform_edt(~m) <= grow * R
    sm = nd.gaussian_filter(m.astype(float), 1.2)
    lines = contourpy.contour_generator(z=sm).lines(0.5)
    polys = []
    for ln in lines:
        if len(ln) < 8: continue
        q = np.stack([ln[:, 0] / R + ox, oy - ln[:, 1] / R], 1)
        if np.hypot(*(q[0] - q[-1])) < 1e-6: q = q[:-1]
        if abs(area(q)) < 30: continue
        polys.append(resample(q, 3.0))
    # orientation: even nesting depth = outer (clockwise, TrueType), odd = hole (counter-clockwise)
    from matplotlib.path import Path
    out = []
    for i, p in enumerate(polys):
        depth = sum(Path(o).contains_point(p[0]) for j, o in enumerate(polys) if j != i)
        cw = area(p) < 0
        out.append(p if (cw == (depth % 2 == 0)) else p[::-1])
    return out

def stroke_w(cs):
    """mean stroke width estimate = 2 * area / perimeter"""
    a = sum(abs(area(p)) * (1 if area(p) < 0 else -1) for p in cs)
    per = sum(np.hypot(*np.diff(np.vstack([p, p[:1]]), axis=0).T).sum() for p in cs)
    return 2 * abs(a) / max(per, 1e-9)

def scaled(cs, s, minw=None):
    """uniform scale; if reduced, thickened back toward the original stroke weight (letterpress weight)"""
    w0 = stroke_w(cs); out = S(cs, s)
    target = minw if minw is not None else min(w0, max(w0 * s, w0 * s + (1 - s) * 30))
    w1 = stroke_w(out)
    if s < 0.93 and target > w1 + 1.5:
        out = jitter(retrace(out, (target - w1) / 2), sd(), 0.8)   # give the re-traced edge its letterpress wobble back
    return norm(out)

_seed = [5100]
def sd():
    _seed[0] += 1; return _seed[0]
def J(cs, amp=1.0): return norm(jitter(cs, sd(), amp))

# ---------------------------------------------------------------- mark library (whole contours only)
def pick(ch, sel):
    cs = G(ch); return norm([cs[i] for i in sel])
def pick_top(ch, ymin):
    return norm([p for p in G(ch) if bb([p])[1] > ymin])
def pick_bottom(ch, ymax):
    return [p for p in G(ch) if bb([p])[3] < ymax]
MK = {
 'cap': {'grave': pick('À', [1]), 'acute': S(pick('Ó', [1]), 1.15), 'circ': pick('Ô', [1]), 'tilde': S(pick('õ', [1]), 1.25),
         'dot': S(pick('Ö', [1]), 1.15), 'dia': pick('Ö', [1, 2]), 'macron': pick('Ū', [1]), 'caron': pick('Č', [1]),
         'breve': S(pick_top('ĕ', 470), 1.12), 'ring': S(norm(G('°')), 0.62)},
 'lc':  {'grave': pick('à', [0]), 'acute': pick('é', [0]), 'circ': pick('ô', [1]), 'tilde': pick('õ', [1]),
         'dot': pick('ä', [2]), 'dia': pick('ä', [2, 3]), 'macron': pick('ō', [1]), 'caron': pick('č', [1]),
         'breve': pick_top('ĕ', 470), 'ring': S(norm(G('°')), 0.58)},
}
CED = {'cap': pick_bottom('Ȩ', 10), 'lc': pick_bottom('ȩ', 10)}      # cedilla contours, kept at their own position (top y=8)
QUOTE = norm(G('’'))
NAME = {0x300: 'grave', 0x301: 'acute', 0x302: 'circ', 0x303: 'tilde', 0x304: 'macron', 0x306: 'breve', 0x307: 'dot',
        0x308: 'dia', 0x30A: 'ring', 0x30C: 'caron',
        0x323: 'dot', 0x324: 'dia', 0x325: 'ring', 0x327: 'cedilla', 0x32D: 'circ', 0x32E: 'breve', 0x330: 'tilde', 0x331: 'macron'}
BELOW = {0x323, 0x324, 0x325, 0x327, 0x32D, 0x32E, 0x330, 0x331}
GAP1 = {'cap': dict(grave=30, acute=30, circ=28, tilde=26, breve=28, dot=26, dia=26, macron=30, caron=28, ring=22),
        'lc': dict(grave=14, acute=14, circ=28, tilde=28, breve=40, dot=55, dia=55, macron=50, caron=40, ring=30)}
CAP_LIM, LC_LIM, ASC_LIM = 910.0, 862.0, 910.0

def jdia(cs):
    """diaeresis: each dot jittered on its own (never two identical dots)"""
    return norm([q for p in cs for q in jitter([p], sd(), 1.0)])

def mark(kind, case):
    m = MK[case][kind]
    return jdia(m) if kind == 'dia' else J(m, 0.8 if kind in ('breve', 'macron') else 1.0)

# ---------------------------------------------------------------- base analysis
def ink_band_cx(cs, ylo, yhi):
    """x-centre of the ink of the glyph between heights ylo..yhi (raster, 2 units/px)"""
    x0, y0, x1, y1 = bb(cs); Wd = int((x1 - x0) / 2) + 4; Ht = int((y1 - y0) / 2) + 4
    acc = np.zeros((Ht, Wd), np.int32)
    for p in cs:
        im = Image.new('L', (Wd, Ht), 0); ImageDraw.Draw(im).polygon([((x - x0) / 2 + 1, (y1 - y) / 2 + 1) for x, y in p], fill=1)
        acc += np.asarray(im, np.int32) * (1 if area(p) < 0 else -1)
    m = acc != 0; rows = slice(max(0, int((y1 - yhi) / 2)), max(1, int((y1 - ylo) / 2)))
    ys, xs = np.nonzero(m[rows]); return x0 + (xs.mean() - 1) * 2

def mask_of(cs, ox, oy, Wd, Ht, r=2.0):
    im = Image.new('L', (Wd, Ht), 0); d = ImageDraw.Draw(im)
    acc = np.zeros((Ht, Wd), np.int32)
    for p in cs:
        im = Image.new('L', (Wd, Ht), 0); ImageDraw.Draw(im).polygon([((x - ox) / r, (oy - y) / r) for x, y in p], fill=1)
        acc += np.asarray(im, np.int32) * (1 if area(p) < 0 else -1)
    return acc != 0
def gap_between(a, b):
    """smallest distance (units) between ink of a and ink of b"""
    x0, y0, x1, y1 = bb(a + b); ox, oy = x0 - 10, y1 + 10; Wd = int((x1 - x0 + 20) / 2) + 2; Ht = int((y1 - y0 + 20) / 2) + 2
    ma, mb = mask_of(a, ox, oy, Wd, Ht), mask_of(b, ox, oy, Wd, Ht)
    if (ma & mb).any(): return 0.0
    return nd.distance_transform_edt(~ma)[mb].min() * 2.0

XH = 450.0
ASC_DOT_BESIDE = set('bdh')
ASC_TOP = set('fklt') | {'ſ'}

def build(cp):
    nfd = U.normalize('NFD', chr(cp)); base = nfd[0]; marks = [ord(m) for m in nfd[1:]]
    if cp == 0x1E9B: base, marks = 'ſ', [0x307]
    case = 'cap' if base.isupper() else 'lc'
    above = [m for m in marks if m not in BELOW]; below = [m for m in marks if m in BELOW]
    bch = 'ı' if (base == 'i' and above) else base
    cs = G(bch); adv = ADV(bch)
    x0, y0, x1, y1 = bb(cs); cx = (x0 + x1) / 2; top = y1
    out = list(cs); parts = []; maxw = adv - 24
    # ------------- marks above
    if above:
        kinds = [NAME[m] for m in above]
        ax = cx; beside = False
        if base in ASC_DOT_BESIDE and kinds == ['dot']:
            beside = True
        elif base in ASC_TOP:
            if base in 'fſ': ax = ink_band_cx(cs, XH + 40, XH + 160)
            elif base == 't': ax = ink_band_cx(cs, top - 70, top)
            elif base == 'l': ax = ink_band_cx(cs, top - 160, top - 60)
            elif base == 'k': ax = cx
        if base == 'a' and case == 'lc': ax = x0 + 0.52 * (x1 - x0)
        if base in 'y' and case == 'lc': ax = x0 + 0.55 * (x1 - x0)
        if beside:
            m = mark('dot', 'lc'); stem_side = 'left' if base in 'bh' else 'right'
            # dot over the x-height part, clear of the ascender (search outward from the bowl centre)
            body_cx = ink_band_cx(cs, 60, XH - 60) if base != 'h' else x0 + 0.68 * (x1 - x0)
            if base == 'b': body_cx = x0 + 0.62 * (x1 - x0)
            if base == 'd': body_cx = x0 + 0.38 * (x1 - x0)
            m = put(m, cx=body_cx, y0=XH + GAP1['lc']['dot'])
            step = 4 if stem_side == 'left' else -4
            for _ in range(40):
                if gap_between(cs, m) >= 34: break
                m = T(m, step, 0)
            out += m; parts.append('dot above beside the ascender')
        elif base in 'fſ' and kinds == ['dot']:
            # f / long s: full-size dot over the stem, as low as a clear gap (>= 40) under the hooked top allows
            m = scaled(mark('dot', 'lc'), 0.82); mm = put(m, cx=ax - 16, y1=ASC_LIM)
            for _ in range(15):                       # step left, off the hooked top, until the dot is clear (>= 40)
                if gap_between(cs, mm) >= 40: break
                mm = T(mm, -4, 0)
            for _ in range(80):                       # then as low as the clearance allows
                m2 = T(mm, 0, -4)
                if gap_between(cs, m2) < 40: break
                mm = m2
            out += mm; parts.append('dot above')
        else:
            lim = CAP_LIM if case == 'cap' else (ASC_LIM if top > 600 else LC_LIM)
            ms = [mark(k, case) for k in kinds]
            g1 = GAP1[case][kinds[0]] if top < 600 or case == 'cap' else 30
            if case == 'cap' and len(ms) == 2:
                lo_k, hi_k = kinds
                lo = ms[0]
                spec = {'macron': ('w', 290), 'tilde': ('w', 210), 'dia': ('s', 0.85), 'acute': ('h', 112),
                        'caron': ('h', 96), 'circ': ('w', 160), 'breve': ('w', 210), 'grave': ('h', 112), 'dot': ('s', 1.0)}[lo_k]
                s = spec[1] / W_(lo) if spec[0] == 'w' else (spec[1] / H_(lo) if spec[0] == 'h' else spec[1])
                lo = scaled(lo, min(1.0, s))
                if lo_k in ('tilde', 'circ', 'breve', 'dia'): lo = norm(A(lo, 1.0, 0.86))
                lo = put(lo, cx=ax, y0=top + min(g1, 22)); y = bb(lo)[3] + 16
                hi = ms[1]; room = lim - y
                s = min(1.0, room / H_(hi))
                for _ in range(30):
                    hi2 = scaled(hi, s) if s < 0.999 else hi
                    if H_(hi2) <= room: break
                    s *= 0.96
                hi2 = put(hi2, cx=ax, y0=y); assert bb(hi2)[3] <= lim + 1
                out += lo + hi2
            else:
                gaps = [g1] + [22 if case == 'lc' else 18] * (len(ms) - 1)
                hs = sum(H_(m) for m in ms); s = min(1.0, (lim - top - sum(gaps)) / hs)
                for _ in range(30):
                    y = top; placed = []
                    for m, g in zip(ms, gaps):
                        m2 = scaled(m, s) if s < 0.999 else m
                        if W_(m2) > maxw: m2 = scaled(m2, maxw / W_(m2))
                        m2 = put(m2, cx=ax, y0=y + g); placed += m2; y = bb(m2)[3]
                    if y <= lim + 0.5: break
                    s *= 0.97
                out += placed
            parts += ['%s above' % k for k in kinds]
    # ------------- marks below (outward from the letter)
    ybot = min(0.0, y0) if y0 > -80 else 0.0      # letters whose foot dips under the baseline (t: -20): start from it
    for m in below:
        k = NAME[m]
        if k == 'cedilla':
            c = [p.copy() for p in CED[case]]
            ccx = cx
            if base in 'Hh': ccx = x0 + (0.13 if base == 'H' else 0.17) * (x1 - x0)   # under the left stem (no ink mid-bottom)
            c = jitter(T(c, ccx - (bb(c)[0] + bb(c)[2]) / 2, 0), sd(), 0.8)
            out += c; ybot = bb(c)[1]; parts.append('cedilla'); continue
        if k == 'dot':
            mm = mark('dot', case)
            mm = norm(S(mm, 1.35 / 1.15)) if case == 'cap' else scaled(mm, 0.86)   # as the Vietnamese dot below
        elif k == 'macron':
            mm = mark('macron', case)
            if case == 'lc': mm = norm(S(mm, 300 / W_(mm)))
        elif k == 'circ':
            mm = norm(A(scaled(mark('circ', case), 0.85 if case == 'cap' else 0.75), 1.0, 0.86))   # wide, flattened 14% to fit the descent
        elif k == 'tilde':
            mm = scaled(mark('tilde', 'lc'), (250 if case == 'cap' else 230) / W_(MK['lc']['tilde']))
        elif k == 'dia':
            mm = scaled(mark('dia', case), 0.95 if case == 'cap' else 0.82)
        elif k == 'ring':
            mm = mark('ring', case)
        elif k == 'breve':
            mm = mark('breve', case)
        if W_(mm) > maxw: mm = scaled(mm, maxw / W_(mm))
        g = 30 if not parts or not parts[-1].endswith('below') else 18
        mm = put(mm, cx=cx, y1=ybot - g)
        if bb(mm)[1] < -160:              # keep inside the em box: reduce
            s = (160 - g + ybot) / H_(mm); mm = put(scaled(mm, s), cx=cx, y1=ybot - g)
        out += mm; ybot = bb(mm)[1]; parts.append('%s below' % k)
    return out, adv, '%s + %s' % (bch, ' + '.join(parts))

def build_1E9A():
    cs = G('a'); x0, y0, x1, y1 = bb(cs)
    q = jitter(scaled(QUOTE, 0.62), sd(), 0.9)
    q = put(q, x0=x1 - 34, y0=y1 - 36)
    out = cs + q; adv = max(ADV('a'), int(round(bb(q)[2] + 14)))
    return out, adv, 'a + our right quotation mark (0.62) at the upper right; advance widened to hold it'

# ---------------------------------------------------------------- glyph assembly
def to_glyph(cs):
    pen = TTGlyphPen(None)
    for p in cs:
        q = np.round(p).astype(int); keep = [0]
        for i in range(1, len(q)):
            if (q[i] != q[keep[-1]]).any(): keep.append(i)
        q = q[keep]
        if len(q) > 1 and (q[0] == q[-1]).all(): q = q[:-1]
        if len(q) < 3: continue
        pen.moveTo(tuple(q[0]))
        for r in q[1:]: pen.lineTo(tuple(r))
        pen.closePath()
    return pen.glyph()

def verify(path):
    a, b = TTFont(MAIN), TTFont(path)
    oa, ob = a.getGlyphOrder(), b.getGlyphOrder()
    assert ob[:len(oa)] == oa and len(ob) == len(oa) + len(TARGETS)
    ga, gb = a['glyf'], b['glyf']
    for n in oa:
        assert ga[n].compile(ga) == gb[n].compile(gb), n
        assert a['hmtx'][n] == b['hmtx'][n], n
        assert a['vmtx'][n] == b['vmtx'][n], n
    for ta, tb in zip(a['cmap'].tables, b['cmap'].tables):
        assert (ta.platformID, ta.platEncID, ta.format) == (tb.platformID, tb.platEncID, tb.format)
        extra = {k: v for k, v in tb.cmap.items() if k not in ta.cmap}
        assert all(tb.cmap[k] == v for k, v in ta.cmap.items())
        if ta.isUnicode(): assert sorted(extra) == TARGETS, (ta.format, len(extra))
        else: assert not extra
    return len(oa)

if __name__ == '__main__':
    notes, new = {}, {}
    for cp in TARGETS:
        out, adv, note = build_1E9A() if cp == 0x1E9A else build(cp)
        out = [np.asarray(p, float) for p in out if len(p) >= 3 and abs(area(np.asarray(p, float))) > 1.0]
        x0, y0, x1, y1 = bb(out)
        assert y1 <= 915.5 and y0 >= -250.5, ('U+%04X' % cp, y0, y1)   # g descends to -248 itself
        new[cp] = (out, adv); notes[cp] = note + ('  [top %d]' % round(y1) if y1 > 864.5 else '')
    order = list(ORIG_ORDER)
    for cp in TARGETS:
        name = 'uni%04X' % cp; assert name not in GL.keys() and name not in order
        out, adv = new[cp]; g = to_glyph(out); GL[name] = g; g.recalcBounds(GL); order.append(name)
        f['hmtx'][name] = (adv, g.xMin)
        f['vmtx'][name] = (1024, 864 - g.yMax)
    f.setGlyphOrder(order)
    for t in f['cmap'].tables:
        if t.isUnicode():
            for cp in TARGETS: t.cmap[cp] = 'uni%04X' % cp
    f['maxp'].numGlyphs = len(order)
    f.save(OUT)
    n = verify(OUT)
    json.dump({'built': TARGETS, 'unsure': {}, 'not_built': {}, 'notes': {'U+%04X' % k: v for k, v in notes.items()}},
              open(RESULT, 'w'), indent=1, ensure_ascii=False)
    print('built %d; %d original glyphs, metrics and cmap entries verified unchanged -> %s' % (len(TARGETS), n, OUT))
