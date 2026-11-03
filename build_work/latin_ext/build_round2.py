"""Round 2 (user review of the 154 Latin Extended Additional glyphs + the currency signs):
REDO A  U+1E00 U+1E01 (ring below), U+1E98 U+1E99 (ring above), U+1E9A (right half ring), U+1E9B (long s + dot above)
REDO B  U+20AB U+20AE U+20B8 U+20BD U+20B1 U+20B3 U+20BF U+20A0 (currency signs: complete bars with natural ends)

Run:  PYTHONDONTWRITEBYTECODE=1 python3 -I build_round2.py
Reads   ../../HuiwenMincho-AI-v2.1.ttf (current main font, never written)
Writes  HuiwenMincho-AI-v2.1.round2.ttf = main font with ONLY these 14 glyphs replaced (same names, same cmap),
        round2_result.json. Asserts every other glyph (glyf bytes), hmtx, vmtx and the whole cmap are unchanged.

Parts (existing outlines only, nothing drawn):
 * ring      = our rough capital O (complete outline with its counter), scaled and thickened back by raster re-trace;
               the counter is checked to stay open (a hole of at least 34% x 55% of the ring size).
 * half ring = the right half of that ring, re-traced with ROUND ends (morphological opening: the ends become half discs).
 * long s    = our long s is drawn identical to f (crossbar on both sides); for U+1E9B the crossbar band is replaced by a
               copy of the stem just below it (natural stem edges, joins hidden in the overlap) -> clearly f without crossbar.
 * bars      = our minus sign (one complete stroke with natural round ends), scaled uniformly to the bar length, then
               thickened/thinned by re-trace to the stroke weight of the letter (54 units), turned 90 deg for the Bitcoin strokes.
 * union of overlapping parts by raster union + re-trace (allowed by the user), then letterpress wobble (jitter) on new edges.
"""
import os, json, unicodedata as U
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image, ImageDraw
from scipy import ndimage as nd
import contourpy
from matplotlib.path import Path

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.abspath(os.path.join(HERE, '..', '..', 'HuiwenMincho-AI-v2.1.ttf'))
OUT = os.path.join(HERE, 'HuiwenMincho-AI-v2.1.round2.ttf')
RESULT = os.path.join(HERE, 'round2_result.json')
TARGETS = [0x1E00, 0x1E01, 0x1E98, 0x1E99, 0x1E9A, 0x1E9B, 0x20AB, 0x20AE, 0x20B8, 0x20BD, 0x20B1, 0x20B3, 0x20BF, 0x20A0]

f = TTFont(MAIN, recalcTimestamp=False)
gs = f.getGlyphSet(); CM = dict(f.getBestCmap()); GL = f['glyf']
for c in TARGETS: assert c in CM, hex(c)

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
    p = Flat(); gs[CM[ord(ch)]].draw(p); return p.cs
def ADV(ch): return f['hmtx'][CM[ord(ch)]][0]
def area(p): return 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
def bb(cs):
    a = np.vstack(cs); return a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max()
def T(cs, dx=0.0, dy=0.0): return [p + np.array([dx, dy]) for p in cs]
def S(cs, s, cx=0.0, cy=0.0): return [(p - [cx, cy]) * s + [cx, cy] for p in cs]
def rot90(cs):
    """+90 deg (counter-clockwise) about the origin; a rotation keeps the winding"""
    return [np.stack([-p[:, 1], p[:, 0]], 1) for p in cs]
def norm(cs):
    x0, y0, x1, y1 = bb(cs); return T(cs, -(x0 + x1) / 2, -(y0 + y1) / 2)        # centred on (0,0)
def put(cs, cx=None, cy=None, x0=None, x1=None, y0=None, y1=None):
    a, b, c, d = bb(cs); dx = dy = 0.0
    if cx is not None: dx = cx - (a + c) / 2
    if cy is not None: dy = cy - (b + d) / 2
    if x0 is not None: dx = x0 - a
    if x1 is not None: dx = x1 - c
    if y0 is not None: dy = y0 - b
    if y1 is not None: dy = y1 - d
    return T(cs, dx, dy)

def resample(p, step=5.0):
    q = np.vstack([p, p[:1]]); seg = np.hypot(*np.diff(q, axis=0).T); L = seg.sum()
    n = max(12, int(L / step)); cum = np.r_[0, np.cumsum(seg)]; t = np.linspace(0, L, n, endpoint=False)
    return np.stack([np.interp(t, cum, q[:, 0]), np.interp(t, cum, q[:, 1])], 1)

_seed = [7700]
def sd():
    _seed[0] += 1; return _seed[0]
def jitter(cs, amp=1.2, seed=None):
    rng = np.random.default_rng(sd() if seed is None else seed); out = []
    for p in cs:
        q = resample(p, 5.0); n = len(q)
        d = np.roll(q, -1, 0) - np.roll(q, 1, 0); d /= np.maximum(1e-9, np.hypot(d[:, 0], d[:, 1]))[:, None]
        nrm = np.stack([d[:, 1], -d[:, 0]], 1)
        w = rng.normal(size=n + 6); k = np.array([1, 2, 3, 2, 1.]) / 9
        low = np.convolve(w, k, 'same')[3:3 + n]; low = (low - low.mean()) / (low.std() + 1e-9)
        out.append(q + nrm * (amp * (0.8 * low + 0.3 * rng.normal(size=n)))[:, None])
    return out

# ---------------- raster space (R px per unit): union, grow/shrink, opening, re-trace
R = 4.0
class Box:
    def __init__(s, x0, y0, x1, y1, pad=30):
        s.ox, s.oy = x0 - pad, y1 + pad
        s.W = int((x1 - x0 + 2 * pad) * R) + 2; s.H = int((y1 - y0 + 2 * pad) * R) + 2
    def mask(s, cs):
        acc = np.zeros((s.H, s.W), np.int32)
        for p in cs:
            im = Image.new('L', (s.W, s.H), 0)
            ImageDraw.Draw(im).polygon([((x - s.ox) * R, (s.oy - y) * R) for x, y in p], fill=1)
            acc += np.asarray(im, np.int32) * (1 if area(p) < 0 else -1)
        return acc != 0
    def xpix(s, x): return int(round((x - s.ox) * R))
    def ypix(s, y): return int(round((s.oy - y) * R))
    def trace(s, m, step=3.0, minarea=30):
        sm = nd.gaussian_filter(m.astype(float), 1.0)
        polys = []
        for ln in contourpy.contour_generator(z=sm).lines(0.5):
            if len(ln) < 8: continue
            q = np.stack([ln[:, 0] / R + s.ox, s.oy - ln[:, 1] / R], 1)
            if np.hypot(*(q[0] - q[-1])) < 1e-6: q = q[:-1]
            if abs(area(q)) < minarea: continue
            polys.append(resample(q, step))
        out = []
        for i, p in enumerate(polys):      # even nesting depth = outer (clockwise, TrueType), odd = hole
            depth = sum(Path(o).contains_point(p[0]) for j, o in enumerate(polys) if j != i)
            cw = area(p) < 0
            out.append(p if (cw == (depth % 2 == 0)) else p[::-1])
        return out
def disk(r):
    r = max(1, int(round(r))); y, x = np.ogrid[-r:r + 1, -r:r + 1]; return x * x + y * y <= r * r
def grow(m, d):                     # d in units (negative = shrink)
    if abs(d) < 0.3: return m
    if d > 0: return nd.distance_transform_edt(~m) <= d * R
    return nd.distance_transform_edt(m) > -d * R
def union_trace(cs, grow_by=0.0):
    x0, y0, x1, y1 = bb(cs); b = Box(x0, y0, x1, y1, 30 + max(0, grow_by)); return b.trace(grow(b.mask(cs), grow_by))

def stroke_w(cs):
    a = sum(-area(p) for p in cs); per = sum(np.hypot(*np.diff(np.vstack([p, p[:1]]), axis=0).T).sum() for p in cs)
    return 2 * abs(a) / max(per, 1e-9)

def ink_runs_y(cs, y):
    """x-intervals of ink on the horizontal line y"""
    x0, y0, x1, y1 = bb(cs); b = Box(x0, y0, x1, y1, 10); m = b.mask(cs); row = m[b.ypix(y)]
    xs = np.flatnonzero(np.diff(np.r_[0, row.astype(int), 0])); return [((a / R) + b.ox, (c / R) + b.ox) for a, c in zip(xs[::2], xs[1::2])]
def ink_runs_x(cs, x):
    x0, y0, x1, y1 = bb(cs); b = Box(x0, y0, x1, y1, 10); m = b.mask(cs); col = m[:, b.xpix(x)]
    ys = np.flatnonzero(np.diff(np.r_[0, col.astype(int), 0])); return [(b.oy - c / R, b.oy - a / R) for a, c in zip(ys[::2], ys[1::2])]
def min_gap(a, b_):
    x0, y0, x1, y1 = bb(a + b_); b = Box(x0, y0, x1, y1, 10); ma, mb = b.mask(a), b.mask(b_)
    if (ma & mb).any(): return 0.0
    return nd.distance_transform_edt(~ma)[mb].min() / R

# ---------------------------------------------------------------- parts
BARW = 54.0
MINUS = norm(G('−'))
def bar(length, weight=BARW, vertical=False):
    """one complete stroke with natural round ends: our minus sign, uniform scale, weight set by re-trace, wobble"""
    w0 = stroke_w(MINUS); L0 = bb(MINUS)[2] - bb(MINUS)[0]
    s = (length - (weight - w0 * (length / L0))) / L0           # the re-trace grows the length by (weight - scaled weight)
    for _ in range(3):
        s = max(0.1, s); ws = w0 * s; L = L0 * s + (weight - ws)
        s *= length / L
    b = S(MINUS, s); ws = stroke_w(b)
    b = norm(jitter(union_trace(b, (weight - ws) / 2), 1.3))
    return norm(rot90(b)) if vertical else b

def ring(outer, weight):
    """complete ring from our rough capital O (outline + counter), outer size 'outer', stroke weight set by re-trace"""
    o = norm(G('O')); D0 = max(bb(o)[2] - bb(o)[0], bb(o)[3] - bb(o)[1]); w0 = stroke_w(o)
    s = (outer - weight) / (D0 - w0)                  # the re-trace adds (weight - w0*s) to the outer size
    r = S(o, s); w = stroke_w(r)
    r = norm(jitter(union_trace(r, (weight - w) / 2), 1.0))
    holes = [p for p in r if area(p) > 0]
    assert len(holes) == 1, 'ring must keep exactly one counter'
    hx0, hy0, hx1, hy1 = bb(holes)
    assert hx1 - hx0 >= 0.34 * outer and hy1 - hy0 >= 0.55 * outer, ('counter too small', hx1 - hx0, hy1 - hy0)
    return r

def half_ring(outer, weight):
    """right half of the ring, ends rounded by opening with a disc of half the stroke weight (no flat cut ends)"""
    r = ring(outer, weight); x0, y0, x1, y1 = bb(r); b = Box(x0, y0, x1, y1, 20)
    m = b.mask(r); cx = (x0 + x1) / 2
    m[:, :b.xpix(cx - 0.08 * (x1 - x0))] = False               # keep a bit more than the right half
    m = nd.binary_opening(m, structure=disk(weight * R * 0.48))  # flat cut ends -> half-disc ends
    return norm(jitter(b.trace(m), 1.0))

DOT = norm([G('ä')[2]])                                          # the dot used for every small-letter dot above
def assert_inside(cs, cp):
    x0, y0, x1, y1 = bb(cs); assert y1 <= 915.5 and y0 >= -200.5, ('U+%04X' % cp, y0, y1)

# ---------------------------------------------------------------- REDO A
def ring_letter(cp):
    nfd = U.normalize('NFD', chr(cp)); base = nfd[0]; below = nfd[1] == '̥'
    cs = G(base); adv = ADV(base); x0, y0, x1, y1 = bb(cs); cx = (x0 + x1) / 2
    if base == 'a': cx = x0 + 0.52 * (x1 - x0)
    if base == 'y': cx = x0 + 0.55 * (x1 - x0)
    if below:
        rg = ring(124 if base == 'A' else 120, 27)
        rg = put(rg, cx=cx, y1=-34); assert bb(rg)[1] >= -160
    else:
        rg = ring(156, 31)
        rg = put(rg, cx=cx, y0=y1 + 44)
    assert min_gap(cs, rg) >= 28, ('ring touches the letter', hex(cp))
    out = cs + rg; assert_inside(out, cp)
    return out, adv, '%s + ring %s (our rough O, complete with its counter, thickened back)' % (base, 'below' if below else 'above')

def a_half_ring():
    cs = G('a'); adv = ADV('a'); x0, y0, x1, y1 = bb(cs)
    h = half_ring(190, 34)
    h = put(h, x0=x1 - 10, y0=y1 - 20)
    for _ in range(30):
        if min_gap(cs, h) >= 26: break
        h = T(h, 4, 2)
    out = cs + h; assert_inside(out, 0x1E9A); adv = max(adv, int(round(bb(h)[2] + 12)))
    return out, adv, 'a + right half ring (right half of our ring, round ends) at the upper right; advance widened to hold it'

def long_s_dot():
    cs = G('ſ'); adv = ADV('ſ'); x0, y0, x1, y1 = bb(cs)
    # crossbar band: rows where the ink is much wider than the stem
    stem = [r for r in ink_runs_y(cs, 250) if r[1] - r[0] > 40][0]; sw = stem[1] - stem[0]
    band = [y for y in range(300, 600, 2) if sum(c - a for a, c in ink_runs_y(cs, y)) > 1.15 * sw]
    by0, by1 = min(band) - 16, max(band) + 16
    b = Box(x0, y0, x1, y1, 40); m = b.mask(cs)
    m[b.ypix(by1):b.ypix(by0) + 1, :] = False                   # remove the whole crossbar band ...
    src = Box(x0, y0, x1, y1, 40)
    piece = m[b.ypix(by0) + 4:b.ypix(by0) + 4 + (b.ypix(by0) - b.ypix(by1)) + 60, :].copy()   # ... stem just below it
    # keep only the stem column in the copied piece (it is below the bar: nothing else there), paste it overlapping
    h = piece.shape[0]; top = b.ypix(by1) - 30
    m[top:top + h, :] |= piece
    body = jitter(b.trace(m), 0.9)
    # dot: same size as the other dots above, as close above the hook as the 915 clip line allows, clear gap >= 30
    d = jitter(DOT, 1.0); best = None
    for dx in range(0, 200, 4):
        for cxd in (None,):
            dd = put(d, cx=(x0 + x1) / 2 + 30 - dx, y1=912)
            if min_gap(body, dd) < 30: continue
            for _ in range(60):
                d2 = T(dd, 0, -3)
                if min_gap(body, d2) < 30: break
                dd = d2
            score = bb(dd)[1] + 0.6 * dx
            if best is None or score < best[0]: best = (score, dd)
    out = body + best[1]; assert_inside(out, 0x1E9B)
    return out, adv, 'long s with its crossbar band replaced by the stem below it (clearly f without crossbar) + dot above (full size)'

# ---------------------------------------------------------------- REDO B (currency)
def with_bars(base_cs, bars, adv, note):
    out = union_trace(base_cs + [p for b_ in bars for p in b_])
    return out, adv, note

def dong():
    cs = G('d'); adv = ADV('d'); x0, y0, x1, y1 = bb(cs)
    st = [r for r in ink_runs_y(cs, 600) if r[1] - r[0] > 30][-1]; scx = (st[0] + st[1]) / 2
    xr = min(adv - 6, st[1] + 62); xl = st[0] - 150               # clearly through the ascender, longer on the left
    cb = put(bar(xr - xl), x0=xl, cy=548)
    ul = put(bar(x1 - x0 - 10), cx=(x0 + x1) / 2, y1=y0 - 30)
    return with_bars(cs, [cb, ul], adv, 'd + bar through the ascender + underline (bars = our minus sign, 54 units)')

def tugrik():
    cs = G('T'); adv = ADV('T'); x0, y0, x1, y1 = bb(cs)
    st = [r for r in ink_runs_y(cs, 300) if r[1] - r[0] > 40][0]; scx = (st[0] + st[1]) / 2
    top_bar_bottom = min(a for a, c in ink_runs_x(cs, x0 + 60))
    y = top_bar_bottom - 0.40 * top_bar_bottom
    return with_bars(cs, [put(bar(380), cx=scx, cy=y)], adv, 'T + bar across the stem 40% below the top bar')

def tenge():
    cs = G('T'); adv = ADV('T'); x0, y0, x1, y1 = bb(cs)
    tb = ink_runs_x(cs, x0 + 80)[-1]; st = [r for r in ink_runs_y(cs, 300) if r[1] - r[0] > 40][0]
    b = put(bar(x1 - x0 - 60), cx=(st[0] + st[1]) / 2, y1=tb[0] - 32)
    return with_bars(cs, [b], adv, 'T + second bar just under the top bar')

def p_stem(cs):
    st = [r for r in ink_runs_y(cs, 150) if r[1] - r[0] > 40][0]; return st
def ruble():
    cs = G('P'); adv = ADV('P'); x0, y0, x1, y1 = bb(cs)
    st = p_stem(cs)
    runs = ink_runs_x(cs, st[1] + 120); bowl_lo = min(a for a, c in runs if a > 150)   # lower edge of the bowl
    y = bowl_lo - 105
    b = put(bar(st[1] - st[0] + 260), x0=st[0] - 85, cy=y)
    return with_bars(cs, [b], adv, 'P + one bar across the stem under the bowl')

def peso():
    cs = G('P'); adv = ADV('P'); x0, y0, x1, y1 = bb(cs)
    st = p_stem(cs)
    hole = [p for p in cs if area(p) > 0][0]; hy0, hy1 = bb([hole])[1], bb([hole])[3]      # the counter of the bowl
    ys = [hy0 + 0.80 * (hy1 - hy0), hy0 + 0.28 * (hy1 - hy0)]                            # clear of the bowl strokes
    bars = [put(bar(x1 - st[0] + 66, 48), x0=st[0] - 80, cy=y) for y in ys]   # ends inside the bowl's right stroke
    return with_bars(cs, bars, adv, 'P + two bars across stem and bowl')

def austral():
    cs = G('A'); adv = ADV('A'); x0, y0, x1, y1 = bb(cs)
    y = 205; runs = ink_runs_y(cs, y); a, c = runs[0][0], runs[-1][1]
    b = put(bar(c - a + 90), cx=(a + c) / 2, cy=y)
    b = T(b, max(0.0, 2 - bb(b)[0]) + min(0.0, adv - 2 - bb(b)[2]), 0)
    return with_bars(cs, [b], adv, 'A + bar across both legs, low')

def bitcoin():
    cs = G('B'); adv = ADV('B'); x0, y0, x1, y1 = bb(cs)
    st = [r for r in ink_runs_y(cs, 350) if r[1] - r[0] > 40][0]; sw = st[1] - st[0]
    w = max(36.0, 0.6 * sw); xs = [st[0] + 0.62 * sw, st[0] + 0.62 * sw + 150]
    strokes = []
    for k, x in enumerate(xs):
        top = max(c for a, c in ink_runs_x(cs, x)); bot = min(a for a, c in ink_runs_x(cs, x))
        strokes.append(put(bar(150, w, vertical=True), cx=x, y0=top - 40))
        strokes.append(put(bar(150, w, vertical=True), cx=x, y1=bot + 40))
    out, adv, _ = with_bars(cs, strokes, adv, '')
    return out, adv, 'B + two short vertical strokes above and below (minus sign turned 90 deg, weight 0.6 x stem)'

def euro_currency():
    C = G('C'); E = G('E')
    cx0, cy0, cx1, cy1 = bb(C)
    e = S(E, 0.66); ex0, ey0, ex1, ey1 = bb(e)
    # E sits low on the right, its stem crossing only the lower arm of the C (one clean crossing)
    e = put(e, x0=cx0 + 0.62 * (cx1 - cx0), y0=0)
    ew = stroke_w(E) * 0.66; e = union_trace(e, max(0.0, (stroke_w(E) - ew) * 0.35))
    out = union_trace(C + e); adv = int(round(bb(out)[2] + 30))
    return out, adv, 'C + our E at 66% (re-thickened) overlapping the lower arm of the C; advance = C + E - overlap'

BUILD = {0x1E00: lambda: ring_letter(0x1E00), 0x1E01: lambda: ring_letter(0x1E01), 0x1E98: lambda: ring_letter(0x1E98),
         0x1E99: lambda: ring_letter(0x1E99), 0x1E9A: a_half_ring, 0x1E9B: long_s_dot,
         0x20AB: dong, 0x20AE: tugrik, 0x20B8: tenge, 0x20BD: ruble, 0x20B1: peso, 0x20B3: austral, 0x20BF: bitcoin,
         0x20A0: euro_currency}

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
    assert a.getGlyphOrder() == b.getGlyphOrder()
    mine = {CM[c] for c in TARGETS}
    ga, gb = a['glyf'], b['glyf']
    for n in a.getGlyphOrder():
        if n in mine: continue
        assert ga[n].compile(ga) == gb[n].compile(gb), n
        assert a['hmtx'][n] == b['hmtx'][n], n
        assert a['vmtx'][n] == b['vmtx'][n], n
    for ta, tb in zip(a['cmap'].tables, b['cmap'].tables): assert ta.cmap == tb.cmap
    return len(a.getGlyphOrder()) - len(mine)

if __name__ == '__main__':
    notes = {}
    for cp in TARGETS:
        out, adv, note = BUILD[cp]()
        out = [np.asarray(p, float) for p in out if len(p) >= 3 and abs(area(np.asarray(p, float))) > 1.0]
        x0, y0, x1, y1 = bb(out); assert y1 <= 915.5 and y0 >= -200.5, ('U+%04X' % cp, y0, y1)
        name = CM[cp]; g = to_glyph(out); GL[name] = g; g.recalcBounds(GL)
        f['hmtx'][name] = (int(adv), g.xMin); f['vmtx'][name] = (1024, 864 - g.yMax)
        notes['U+%04X' % cp] = note
    f.save(OUT)
    n = verify(OUT)
    json.dump({'rebuilt': ['U+%04X' % c for c in TARGETS], 'notes': notes}, open(RESULT, 'w'), indent=1, ensure_ascii=False)
    print('rebuilt %d; %d other glyphs, metrics and cmap verified unchanged -> %s' % (len(TARGETS), n, OUT))
