"""Round 8 (user on U+20A0: "C上移" = move the C up): round-7 treatment (C cut under the E with a 12-unit gap, island
removed, C's cut end joined to the E stem by a local closing r=14, nubs on the C's left edge removed by a local opening),
but the C is raised by CSHIFT units (E unchanged), so the C sits clearly higher than the E as in Arial / Sarasa and its
lower terminal now meets the upper part of the E's stem.
Run:  PYTHONDONTWRITEBYTECODE=1 python3 -I build_round8.py
Writes HuiwenMincho-AI-v2.1.round8.ttf = current main font with ONLY U+20A0 replaced (asserted), round8_result.json.
"""
import os, json, runpy
import numpy as np
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))
L = runpy.run_path(os.path.join(HERE, 'build_round2.py'), run_name='round2_lib')
f, GL, CM, MAIN = L['f'], L['GL'], L['CM'], L['MAIN']
G, ADV, bb, S, put = L['G'], L['ADV'], L['bb'], L['S'], L['put']
union_trace, stroke_w, jitter, area, to_glyph = L['union_trace'], L['stroke_w'], L['jitter'], L['area'], L['to_glyph']
Box, disk, R = L['Box'], L['disk'], L['R']
OUT = os.path.join(HERE, 'HuiwenMincho-AI-v2.1.round8.ttf')
TARGETS = [0x20A0]
L['_seed'][0] = 9300
GAP = 12.0
JOIN, NUB = 14.0, 15.0
CSHIFT = 140.0

def euro_currency():
    C = L['T'](G('C'), 0, CSHIFT); E = G('E'); cx0, cy0, cx1, cy1 = bb(C)
    cE0 = (bb(G('C'))[0] + bb(G('C'))[2]) / 2      # E placement keeps the round-3/7 reference (unshifted C centre)
    s = 0.73; e = S(E, s)                                                  # round-3 size and placement
    e = union_trace(e, max(0.0, (stroke_w(E) - stroke_w(e)) * 0.40))
    e = put(e, x0=cE0 - 8, y0=-158)
    x0, y0, x1, y1 = bb(C + e); b = Box(x0, y0, x1, y1, 50)
    mc, me = b.mask(C), b.mask(e)
    keep_out = nd.distance_transform_edt(~me) <= GAP * R               # E footprint + constant gap
    mc2 = mc & ~keep_out
    lab, n = nd.label(mc2)                                             # drop C fragments narrower than 40 units
    for i in range(1, n + 1):
        comp = lab == i; dt = nd.distance_transform_edt(comp)
        if dt.max() * 2 / R < 40 or comp.sum() / R ** 2 < 1600: mc2[comp] = False
    # (1) the stray island = a piece of the C's lower terminal left inside the E's upper counter by the cut: keep only
    #     the main body of the C, before anything is joined
    lab, n = nd.label(mc2); mc2 = lab == (1 + int(np.argmax(nd.sum(mc2, lab, range(1, n + 1)))))
    m2 = mc2 | me
    # (2) join the C's cut end to the E's stem (closing only where the two face each other across the cut gap)
    near = (nd.distance_transform_edt(~mc2) / R <= GAP + 6) & (nd.distance_transform_edt(~me) / R <= GAP + 6)
    near = nd.distance_transform_edt(~near) <= JOIN * R
    closed = nd.distance_transform_edt(nd.distance_transform_edt(~m2) <= JOIN * R) > JOIN * R - 0.5
    m2 |= closed & near
    # (3) remove the two tiny nubs on the C's left side (local opening of the left edge)
    xs = (np.arange(m2.shape[1]) / R) + b.ox; ys = b.oy - (np.arange(m2.shape[0]) / R)
    region = (xs[None, :] < cx0 + 45) & (ys[:, None] > 250 + CSHIFT) & (ys[:, None] < 550 + CSHIFT)
    opened = nd.distance_transform_edt(~(nd.distance_transform_edt(m2) > NUB * R)) <= NUB * R + 0.5
    m2 &= ~(region & ~opened)
    # (1) keep only the main shape: no islands inside the E's counters
    lab, n = nd.label(m2); sizes = nd.sum(m2, lab, range(1, n + 1)); m2 = lab == (1 + int(np.argmax(sizes)))
    out = jitter(b.trace(m2), 0.9)
    adv = 930
    return out, adv, 'round-7 treatment with the C raised by 140 units (E unchanged): C cut under the E (gap 12), joined to the E stem, no island, no nubs'

if __name__ == '__main__':
    from fontTools.ttLib import TTFont
    out, adv, note = euro_currency()
    out = [np.asarray(p, float) for p in out if len(p) >= 3 and abs(area(np.asarray(p, float))) > 1.0]
    x0, y0, x1, y1 = bb(out); assert y1 <= 915.5 and y0 >= -160.5 and x1 <= adv, (y0, y1, x1)
    name = CM[0x20A0]; g = to_glyph(out); GL[name] = g; g.recalcBounds(GL)
    f['hmtx'][name] = (adv, g.xMin); f['vmtx'][name] = (1024, 864 - g.yMax)
    f.save(OUT)
    a, b_ = TTFont(MAIN), TTFont(OUT)
    assert a.getGlyphOrder() == b_.getGlyphOrder()
    for n in a.getGlyphOrder():
        if n == name: continue
        assert a['glyf'][n].compile(a['glyf']) == b_['glyf'][n].compile(b_['glyf']), n
        assert a['hmtx'][n] == b_['hmtx'][n] and a['vmtx'][n] == b_['vmtx'][n], n
    for ta, tb in zip(a['cmap'].tables, b_['cmap'].tables): assert ta.cmap == tb.cmap
    json.dump({'rebuilt': ['U+20A0'], 'notes': {'U+20A0': note}}, open(os.path.join(HERE, 'round8_result.json'), 'w'), indent=1)
    print('rebuilt U+20A0 (round 8); all other glyphs, metrics and cmap verified unchanged ->', OUT)
