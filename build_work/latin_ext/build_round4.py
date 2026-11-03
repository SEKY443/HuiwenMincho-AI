"""Round 4 (user review of round 3): ONLY U+20A0 and U+20B8 are replaced (tugrik/austral functions kept from round 3).
  U+20B8 TENGE          the extra bar goes ABOVE the T's top bar (user: "one more bar on top / above"), clear gap ~40,
                        length of the top bar, weight of the top bar; everything under y=915.
  U+20A0 EURO-CURRENCY  C full size upper left; E at 75% of the C height, lower right: top near the C's middle, foot at -158,
                        left stem laid over the C's lower terminal, so its three arms stand clear to the right of the C; advance = C + ~65% of the E.
Run:  PYTHONDONTWRITEBYTECODE=1 python3 -I build_round4.py
Writes HuiwenMincho-AI-v2.1.round4.ttf = current main font with ONLY these 2 glyphs replaced (asserted), round4_result.json.
Parts/techniques of build_round2.py (imported): complete outlines (minus sign, letters), weight by raster re-trace,
union by raster union + re-trace, letterpress wobble; nothing cut, nothing drawn.
"""
import os, json, runpy
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
L = runpy.run_path(os.path.join(HERE, 'build_round2.py'), run_name='round2_lib')
f, GL, CM = L['f'], L['GL'], L['CM']
G, ADV, bb, T, S, put, norm = L['G'], L['ADV'], L['bb'], L['T'], L['S'], L['put'], L['norm']
bar, union_trace, stroke_w, jitter = L['bar'], L['union_trace'], L['stroke_w'], L['jitter']
ink_runs_x, ink_runs_y, area, to_glyph = L['ink_runs_x'], L['ink_runs_y'], L['area'], L['to_glyph']
OUT = os.path.join(HERE, 'HuiwenMincho-AI-v2.1.round4.ttf')
MAIN = L['MAIN']
TARGETS = [0x20A0, 0x20B8]
L['_seed'][0] = 9100

def rotate(cs, deg):
    a = np.radians(deg); R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return [p @ R.T for p in cs]
def angle_of(cs):
    """direction of the long axis (degrees from horizontal) by PCA of the outline points"""
    a = np.vstack(cs); a = a - a.mean(0); w, v = np.linalg.eigh(a.T @ a); d = v[:, -1]
    return np.degrees(np.arctan2(d[1], d[0])) % 180

def t_stem(cs):
    return [r for r in ink_runs_y(cs, 300) if r[1] - r[0] > 40][0]

def euro_currency():
    C = G('C'); E = G('E'); cx0, cy0, cx1, cy1 = bb(C)
    s = 0.75 * (cy1 - cy0) / (bb(E)[3] - bb(E)[1]); e = S(E, s)
    e = union_trace(e, max(0.0, (stroke_w(E) - stroke_w(e)) * 0.45))       # weight back toward the full E
    # the E's stem is laid over the C's lower terminal (x of the terminal at y=150), so the terminal disappears into the
    # stem and all three arms of the E stand to the right of the C, clear of it
    term = [r for r in ink_runs_y(C, 150) if r[0] > (cx0 + cx1) / 2][0]
    e = put(e, x0=term[0] - 14, y0=-158)
    out = union_trace(C + e); ew = bb(e)[2] - bb(e)[0]
    adv = int(round(min(1000, max(bb(out)[2] + 24, ADV('C') + 0.65 * ew))))
    return out, adv, 'C + our E at 75%% of the C height (re-thickened), lower right: top at %d, foot -158, stem over the C lower terminal' % round(bb(e)[3])

def tugrik():
    cs = G('T'); adv = ADV('T'); st = t_stem(cs); scx = (st[0] + st[1]) / 2; sw = st[1] - st[0]
    sl = norm(G('/')); sl = rotate(sl, 30 - angle_of(sl))                  # our slash, turned to 30 deg (as Arial / Times / Sarasa)
    target_w = 56.0; strokes = []
    for k, yc in enumerate((400, 265)):
        a = norm(S(sl, 1.0)); L0 = bb(a)[2] - bb(a)[0]                      # horizontal extent
        a = S(a, (sw + 2 * 100) / L0); w = stroke_w(a)
        a = union_trace(a, (target_w - w) / 2); a = jitter(a, 1.2)
        strokes.append(put(a, cx=scx, cy=yc))
    out = union_trace(cs + [p for s_ in strokes for p in s_])
    return out, adv, 'T + two parallel diagonal strokes (our / turned to 30 deg, weight 56) across the lower middle of the stem'

def austral():
    cs = G('A'); adv = ADV('A'); x0, y0, x1, y1 = bb(cs); H = y1 - y0; bars = []
    # the A's own crossbar sits at ~1/3 of the height: the upper bar runs along it (the crossbar becomes one of the two
    # bars, extended past the legs), the lower bar 92 units under it (gap 40)
    hole = [p for p in cs if area(p) > 0 and bb([p])[3] - bb([p])[1] > 60][0]; cx = (bb([hole])[0] + bb([hole])[2]) / 2
    xb = [r for r in ink_runs_x(cs, cx) if r[1] < bb([hole])[3] - 20][0]          # the run under the counter = crossbar
    ycb = (xb[0] + xb[1]) / 2
    for y in (ycb, ycb - 108):
        runs = ink_runs_y(cs, y); a, c = runs[0][0], runs[-1][1]
        xa, xc = max(4.0, a - 60), min(adv - 4.0, c + 60)
        bars.append(put(bar(xc - xa, 52), x0=xa, cy=y))
    out = union_trace(cs + [p for b_ in bars for p in b_])
    return out, adv, 'A + two horizontal bars (the crossbar extended + one 108 lower, clear gap) across both legs'

def tenge():
    cs = G('T'); adv = ADV('T'); x0, y0, x1, y1 = bb(cs)
    xs = (x0 + 150, x1 - 150)                                              # top bar weight between serif and stem
    runs = [max(ink_runs_x(cs, x), key=lambda r: r[1]) for x in xs]          # the topmost run = the top bar
    tw = float(np.clip(np.mean([c - a for a, c in runs]), 54, 90))
    b = put(bar(x1 - x0 - 6, tw), cx=(x0 + x1) / 2, y0=y1 + 40)            # floating ABOVE the top bar, gap 40
    if bb(b)[3] > 912:                                                     # (not needed for our T: top ~ 696+40+bar)
        k = (912 - 40 - tw) / y1; cs = S(cs, k); b = put(b, y0=bb(cs)[3] + 40)
    out = cs + jitter(b, 0.6)
    return out, adv, 'T + extra bar ABOVE the top bar (gap 40, top-bar length, weight %d = top bar)' % round(tw)

BUILD = {0x20A0: euro_currency, 0x20AE: tugrik, 0x20B3: austral, 0x20B8: tenge}

if __name__ == '__main__':
    from fontTools.ttLib import TTFont
    notes = {}
    for cp in TARGETS:
        out, adv, note = BUILD[cp]()
        out = [np.asarray(p, float) for p in out if len(p) >= 3 and abs(area(np.asarray(p, float))) > 1.0]
        x0, y0, x1, y1 = bb(out); assert y1 <= 915.5 and y0 >= -160.5, ('U+%04X' % cp, y0, y1)
        name = CM[cp]; g = to_glyph(out); GL[name] = g; g.recalcBounds(GL)
        f['hmtx'][name] = (int(adv), g.xMin); f['vmtx'][name] = (1024, 864 - g.yMax)
        notes['U+%04X' % cp] = note
    f.save(OUT)
    a, b = TTFont(MAIN), TTFont(OUT); mine = {CM[c] for c in TARGETS}
    assert a.getGlyphOrder() == b.getGlyphOrder()
    for n in a.getGlyphOrder():
        if n in mine: continue
        assert a['glyf'][n].compile(a['glyf']) == b['glyf'][n].compile(b['glyf']), n
        assert a['hmtx'][n] == b['hmtx'][n] and a['vmtx'][n] == b['vmtx'][n], n
    for ta, tb in zip(a['cmap'].tables, b['cmap'].tables): assert ta.cmap == tb.cmap
    json.dump({'rebuilt': ['U+%04X' % c for c in TARGETS], 'notes': notes}, open(os.path.join(HERE, 'round4_result.json'), 'w'), indent=1)
    print('rebuilt 2; all other glyphs, metrics and cmap verified unchanged ->', OUT)
