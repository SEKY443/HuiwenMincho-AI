"""Round 6 (user on U+20A0: "the part of the C that overlaps the E: just cut it off directly"):
round-5 layout (C full size, E at 73% lower right, foot -158) unchanged; every part of the C inside the E's footprint
dilated by GAP units is removed (the cut follows the E's silhouette with a constant thin gap), C fragments narrower than
40 units are deleted, the E stays complete and is drawn whole. Raster ops at 4 px/unit, re-trace, light wobble.
(The user explicitly asked for this cut; it is the one exception to the no-cut rule.)
Run:  PYTHONDONTWRITEBYTECODE=1 python3 -I build_round6.py
Writes HuiwenMincho-AI-v2.1.round6.ttf = current main font with ONLY U+20A0 replaced (asserted), round6_result.json.
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
OUT = os.path.join(HERE, 'HuiwenMincho-AI-v2.1.round6.ttf')
TARGETS = [0x20A0]
L['_seed'][0] = 9300
GAP = 12.0

def euro_currency():
    C = G('C'); E = G('E'); cx0, cy0, cx1, cy1 = bb(C)
    s = 0.73; e = S(E, s)                                                  # round-3 size and placement
    e = union_trace(e, max(0.0, (stroke_w(E) - stroke_w(e)) * 0.40))
    e = put(e, x0=(cx0 + cx1) / 2 - 8, y0=-158)
    x0, y0, x1, y1 = bb(C + e); b = Box(x0, y0, x1, y1, 50)
    mc, me = b.mask(C), b.mask(e)
    keep_out = nd.distance_transform_edt(~me) <= GAP * R               # E footprint + constant gap
    mc2 = mc & ~keep_out
    lab, n = nd.label(mc2)                                             # drop C fragments narrower than 40 units
    for i in range(1, n + 1):
        comp = lab == i; dt = nd.distance_transform_edt(comp)
        if dt.max() * 2 / R < 40 or comp.sum() / R ** 2 < 1600: mc2[comp] = False
    m2 = mc2 | me
    out = jitter(b.trace(m2), 0.9)
    adv = 930
    return out, adv, 'C + our E at 73% (round-5 layout); the C is cut away under the E with a 12-unit gap (user request), E intact'

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
    json.dump({'rebuilt': ['U+20A0'], 'notes': {'U+20A0': note}}, open(os.path.join(HERE, 'round6_result.json'), 'w'), indent=1)
    print('rebuilt U+20A0 (round 6); all other glyphs, metrics and cmap verified unchanged ->', OUT)
