"""Review sheets: [previous (main font) | NEW | reference fonts (env LE_REFS, default Times New Roman:Arial Unicode)], glyph box 400 px.
usage: python3 -I sheets_round2.py OUTPREFIX NEWFONT HEX [HEX ...]
Guides: grey = baseline / x-height 450 / 864 / -160, red = 915."""
import os, sys, unicodedata as U
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.abspath(os.path.join(HERE, '..', '..', 'HuiwenMincho-AI-v2.1.ttf'))
REFS = os.environ.get('LE_REFS', '/System/Library/Fonts/Supplemental/Times New Roman.ttf:/System/Library/Fonts/Supplemental/Arial Unicode.ttf').split(':')
prefix, newfont = sys.argv[1], sys.argv[2]
cps = [int(x, 16) for x in sys.argv[3:]]
TOPY, BOTY = 960.0, -270.0
P = 400

class Flat(BasePen):
    def __init__(s, gs): super().__init__(gs); s.cs = []; s.cur = None
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
        if s.cur and len(s.cur) > 2: s.cs.append(s.cur)
        s.cur = None
    _endPath = _closePath

def render(font, cp, size=P):
    gs = font.getGlyphSet(); cm = font.getBestCmap()
    if cp not in cm: return None, 0, 0
    p = Flat(gs); gs[cm[cp]].draw(p); adv = font['hmtx'][cm[cp]][0]
    k = size / (TOPY - BOTY); W = size; ox = (W - adv * k) / 2
    acc = np.zeros((size * 2, W * 2), np.int32)
    for c in p.cs:
        a = 0.5 * sum(c[j][0] * c[(j + 1) % len(c)][1] - c[(j + 1) % len(c)][0] * c[j][1] for j in range(len(c)))
        im = Image.new('L', (W * 2, size * 2), 0)
        ImageDraw.Draw(im).polygon([((ox + x * k) * 2, (TOPY - y) * k * 2) for x, y in c], fill=1)
        acc += np.asarray(im, np.int32) * (1 if a < 0 else -1)
    return Image.fromarray(((acc != 0) * 255).astype(np.uint8)).resize((W, size), Image.LANCZOS), ox, adv * k

OURS = [TTFont(x) for x in os.environ['LE_OURS'].split(':')] if os.environ.get('LE_OURS') else [TTFont(PREV), TTFont(newfont)]
refcm = [TTFont(r).getBestCmap() for r in REFS]
RW = 230; NO = len(OURS); CW = NO * (P + 10) + len(REFS) * RW + 30; CH = P + 50; cols = 2
LB = ImageFont.load_default(size=18); HD = ImageFont.load_default(size=26)
per = 6; pages = (len(cps) + per - 1) // per
for pg in range(pages):
    chunk = cps[pg * per:(pg + 1) * per]
    im = Image.new('RGB', (cols * CW + 20, 54 + ((len(chunk) + cols - 1) // cols) * CH), 'white'); d = ImageDraw.Draw(im)
    d.text((10, 12), os.environ.get('LE_TITLE', 'Round 2') + '  page %d/%d   ' % (pg + 1, pages) + os.environ.get('LE_HEAD', '[previous | NEW (blue) | ') + ' | '.join(os.path.basename(r)[:-4] for r in REFS) + ']   grey: 0, 450, 864, -160; red: 915', font=HD, fill='#111')
    for i, cp in enumerate(chunk):
        x = 10 + (i % cols) * CW; y = 54 + (i // cols) * CH
        for k, font in enumerate(OURS):
            px = x + k * (P + 10)
            new = k == NO - 1
            d.rectangle((px, y, px + P, y + P), outline='#2b6cb0' if new else '#bbbbbb', width=3 if new else 1)
            for yy, col in ((0, '#bbbbbb'), (450, '#e2e2e2'), (864, '#bbbbbb'), (-160, '#bbbbbb'), (915, '#f08080')):
                yp = y + (TOPY - yy) * P / (TOPY - BOTY); d.line((px, yp, px + P, yp), fill=col)
            m, ox, aw = render(font, cp)
            if m is None: continue
            d.line((px + ox, y + P - 10, px + ox, y + P), fill='#66a'); d.line((px + ox + aw, y + P - 10, px + ox + aw, y + P), fill='#66a')
            im.paste((0, 0, 0), (px, y), m)
            if new and os.environ.get('LE_GUIDE'):          # optional thin red guide line (font units) on the NEW cell
                for gv in os.environ['LE_GUIDE'].split(','):
                    gy = y + (TOPY - float(gv)) * P / (TOPY - BOTY); d.line((px, gy, px + P, gy), fill='#e02020', width=1)
        for k, r in enumerate(REFS):
            if cp in refcm[k]:
                F = ImageFont.truetype(r, int(P * 0.42))
                d.text((x + NO * (P + 10) + 10 + k * RW + RW / 2, y + P * 0.52), chr(cp), font=F, fill='#333', anchor='mm')
        d.text((x, y + P + 6), 'U+%04X %s' % (cp, U.name(chr(cp), '?').title()), font=LB, fill='#333')
    out = os.path.abspath(os.path.join(HERE, '..', '..', 'example', '%s_%02d.png' % (prefix, pg + 1))); im.save(out); print(out)
