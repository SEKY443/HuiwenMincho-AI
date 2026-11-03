"""Contact sheets for latin_ext: example/latin_ext_added_NN.png  [ours (large) | system font reference].
Guides: grey = baseline / x-height 450 / ascent 864 / descent -160, red = 915 (Windows clip line)."""
import os, sys, json, unicodedata as U
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, 'HuiwenMincho-AI-v2.1.latin_ext.ttf')
OUTDIR = os.path.abspath(os.path.join(HERE, '..', '..', 'example'))
REF = '/System/Library/Fonts/Supplemental/Times New Roman.ttf'
REF2 = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
res = json.load(open(os.path.join(HERE, 'latin_ext_result.json')))
cps = res['built'] if len(sys.argv) < 2 else [int(x, 16) for x in sys.argv[1:]]
f = TTFont(FONT); gs = f.getGlyphSet(); cm = f.getBestCmap()
rf, rf2 = TTFont(REF).getBestCmap(), TTFont(REF2).getBestCmap()

class Flat(BasePen):
    def __init__(s): super().__init__(gs); s.cs = []; s.cur = None
    def _moveTo(s, p): s.cur = [p]
    def _lineTo(s, p): s.cur.append(p)
    def _qCurveToOne(s, a, c):
        p0 = s.cur[-1]
        for t in np.linspace(0, 1, 9)[1:]:
            u = 1 - t; s.cur.append((u*u*p0[0] + 2*u*t*a[0] + t*t*c[0], u*u*p0[1] + 2*u*t*a[1] + t*t*c[1]))
    def _closePath(s):
        if s.cur and len(s.cur) > 2: s.cs.append(s.cur)
        s.cur = None
    _endPath = _closePath

TOPY, BOTY = 960.0, -270.0
P = 300; K = P / (TOPY - BOTY); RW = 150
def render(cp, size):
    p = Flat(); gs[cm[cp]].draw(p); adv = f['hmtx'][cm[cp]][0]
    k = size / (TOPY - BOTY); W = size; ox = (W - adv * k) / 2
    acc = np.zeros((size * 2, W * 2), np.int32)
    for c in p.cs:
        a = 0.5 * sum(c[j][0] * c[(j + 1) % len(c)][1] - c[(j + 1) % len(c)][0] * c[j][1] for j in range(len(c)))
        im = Image.new('L', (W * 2, size * 2), 0)
        ImageDraw.Draw(im).polygon([((ox + x * k) * 2, (TOPY - y) * k * 2) for x, y in c], fill=1)
        acc += np.asarray(im, np.int32) * (1 if a < 0 else -1)
    m = Image.fromarray(((acc != 0) * 255).astype(np.uint8)).resize((W, size), Image.LANCZOS)
    return m, ox, adv * k

cols, rows = 6, 4; CW = P + RW + 24; CH = P + 46; per = cols * rows
LB = ImageFont.load_default(size=15); HD = ImageFont.load_default(size=24)
os.makedirs(OUTDIR, exist_ok=True)
pages = (len(cps) + per - 1) // per
for pg in range(pages):
    chunk = cps[pg * per:(pg + 1) * per]
    im = Image.new('RGB', (cols * CW + 20, 50 + ((len(chunk) + cols - 1) // cols) * CH), 'white'); d = ImageDraw.Draw(im)
    d.text((10, 10), 'Latin Extended Additional - added glyphs  page %d/%d   [ours | reference]  grey: baseline, x-height, 864, -160;  red: 915' % (pg + 1, pages), font=HD, fill='#111')
    for i, cp in enumerate(chunk):
        x = 10 + (i % cols) * CW; y = 50 + (i // cols) * CH
        m, ox, aw = render(cp, P)
        d.rectangle((x, y, x + P, y + P), outline='#2b6cb0', width=2)
        for yy, col in ((0, '#bbbbbb'), (450, '#dddddd'), (864, '#bbbbbb'), (-160, '#bbbbbb'), (915, '#f08080')):
            d.line((x, y + (TOPY - yy) * K, x + P, y + (TOPY - yy) * K), fill=col)
        d.line((x + ox, y + P - 8, x + ox, y + P), fill='#99c'); d.line((x + ox + aw, y + P - 8, x + ox + aw, y + P), fill='#99c')
        im.paste((0, 0, 0), (x, y), m)
        rfont = REF if cp in rf else REF2 if cp in rf2 else None
        if rfont:
            F = ImageFont.truetype(rfont, int(RW * 0.62))
            d.text((x + P + 12 + RW / 2, y + P / 2), chr(cp), font=F, fill='#333', anchor='mm')
        d.text((x, y + P + 4), 'U+%04X %s' % (cp, U.name(chr(cp))[12:40].title()), font=LB, fill='#333')
        d.text((x, y + P + 22), res['notes']['U+%04X' % cp][:52], font=LB, fill='#b33')
    out = os.path.join(OUTDIR, 'latin_ext_added_%02d.png' % (pg + 1)); im.save(out); print(out)
