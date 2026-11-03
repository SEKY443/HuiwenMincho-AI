"""Round 5 (user: "the previous version was good, but the junction of C and E is unnatural"):
U+20A0 EURO-CURRENCY back to the ROUND-3 layout (E at 73%, lower right, stem from the C centre line, foot -158), and the
contact of the two letters is fused like a deliberate ligature:
  * raster union of C and E (4 px/unit),
  * a fillet only in the contact zone: morphological closing with a disc of r=24 units, applied where the two letters come
    within ~30 units of each other (so the rest of both outlines is untouched),
  * no slivers: tiny holes (< 900 sq units) and specks inside the zone are filled / removed,
  * re-trace, then the letterpress wobble on the outline.
Run:  PYTHONDONTWRITEBYTECODE=1 python3 -I build_round5.py
Writes HuiwenMincho-AI-v2.1.round5.ttf = current main font with ONLY U+20A0 replaced (asserted), round5_result.json.
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
OUT = os.path.join(HERE, 'HuiwenMincho-AI-v2.1.round5.ttf')
TARGETS = [0x20A0]
L['_seed'][0] = 9300
FILLET, ZONE = 24.0, 30.0

def euro_currency():
    C = G('C'); E = G('E'); cx0, cy0, cx1, cy1 = bb(C)
    s = 0.73; e = S(E, s)                                                  # round-3 size and placement
    e = union_trace(e, max(0.0, (stroke_w(E) - stroke_w(e)) * 0.40))
    e = put(e, x0=(cx0 + cx1) / 2 - 8, y0=-158)
    x0, y0, x1, y1 = bb(C + e); b = Box(x0, y0, x1, y1, 50)
    mc, me = b.mask(C), b.mask(e); m = mc | me
    dc = nd.distance_transform_edt(~mc) / R; de = nd.distance_transform_edt(~me) / R
    zone = (dc <= ZONE) & (de <= ZONE)                                     # where the two letters meet or nearly meet
    zone = nd.distance_transform_edt(~zone) <= FILLET * R              # (distance transforms: fast exact disc dilation)
    grown = nd.distance_transform_edt(~m) <= FILLET * R
    closed = nd.distance_transform_edt(grown) > FILLET * R - 0.5       # closing = dilation then erosion by the same disc
    m2 = m | (closed & zone)
    # clean slivers in the zone: fill small holes, drop small specks
    holes = nd.binary_fill_holes(m2) & ~m2; lab, n = nd.label(holes)
    for i in range(1, n + 1):
        h = lab == i
        if h.sum() / R ** 2 < 900 and (h & zone).any(): m2 |= h
    lab, n = nd.label(m2); sizes = nd.sum(m2, lab, range(1, n + 1))
    for i, sz in enumerate(sizes, 1):
        if sz / R ** 2 < 200: m2[lab == i] = False
    out = jitter(b.trace(m2), 0.9)
    adv = 930
    return out, adv, 'C + our E at 73% (round-3 layout), joined by a fillet (closing r=24) in the contact zone only'

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
    json.dump({'rebuilt': ['U+20A0'], 'notes': {'U+20A0': note}}, open(os.path.join(HERE, 'round5_result.json'), 'w'), indent=1)
    print('rebuilt U+20A0; all other glyphs, metrics and cmap verified unchanged ->', OUT)
