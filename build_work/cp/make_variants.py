"""Build centring variants of a HuiwenMincho-AI font.

usage: make_variants.py SRC OUT MODE FAMILY   (MODE: VC | AC | NC)
 horizontal punctuation (，。、．；：！？): centred (as in the main font) or placed lower-left / left (mainland style)
 vertical forms of symbols: as in the main font (top-right) or centred in the em box
 AC additionally centres every full-width symbol, also in horizontal form (the earlier "CP" build)
"""
import sys, unicodedata as U
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.boundsPen import BoundsPen
SRC,OUT,MODE,FAM=sys.argv[1:5]
CX,CY=512,352
f=TTFont(SRC); cmap=f.getBestCmap(); gs=f.getGlyphSet(); hm=f['hmtx']
gsub=f['GSUB'].table; vert={}
for fr in gsub.FeatureList.FeatureRecord:
    if fr.FeatureTag in ('vert','vrt2'):
        for i in fr.Feature.LookupListIndex:
            for st in gsub.LookupList.Lookup[i].SubTable:
                st=getattr(st,'ExtSubTable',st)
                if hasattr(st,'mapping'): vert.update(st.mapping)
def bounds(n):
    bp=BoundsPen(gs); gs[n].draw(bp); return bp.bounds
def move(n,dx,dy):
    if dx==0 and dy==0: return False
    rec=DecomposingRecordingPen(gs); gs[n].draw(rec)
    pen=TTGlyphPen(gs); rec.replay(TransformPen(pen,(1,0,0,1,dx,dy)))
    g=pen.glyph(); f['glyf'][n]=g; g.recalcBounds(f['glyf'])
    f['hmtx'][n]=(hm[n][0],g.xMin)
    if 'vmtx' in f: f['vmtx'][n]=(f['vmtx'][n][0],864-g.yMax)
    return True
def centre(n):
    b=bounds(n)
    if not b: return False
    x0,y0,x1,y1=b
    if x1-x0>900 or y1-y0>900: return False
    return move(n,round(CX-(x0+x1)/2),round(CY-(y0+y1)/2))
def fullwidth_symbol(cp):
    c=U.category(chr(cp))
    if cp<0x2000 and not (0xB0<=cp<=0xB7): return False
    if 0x2500<=cp<=0x259F: return False
    if c[0] not in 'PS': return False
    return hm[cmap[cp]][0]==1024
PUNCT_LOW=[0xFF0C,0x3002,0x3001,0xFF0E]; PUNCT_LEFT=[0xFF1B,0xFF1A,0xFF01,0xFF1F]
hnames={cmap[c] for c in cmap if fullwidth_symbol(c)}
hv={vert[n] for n in hnames if n in vert}
fw=[c for c in cmap if fullwidth_symbol(c)]
vpres={cmap[c] for c in fw if 0xFE10<=c<=0xFE4F}             # vertical presentation forms have their own code points
horiz={cmap[c] for c in fw if not 0xFE10<=c<=0xFE4F}
vnames=(hv|vpres)-horiz
moved=0
if MODE in('VC','AC'):
    for n in sorted(vnames): moved+=centre(n)
if MODE=='AC':
    for n in sorted(hnames): moved+=centre(n)
if MODE in('VC','NC'):
    for cp in PUNCT_LOW:                 # lower-left corner of the cell
        if cp in cmap:
            x0,y0,x1,y1=bounds(cmap[cp]); moved+=move(cmap[cp],70-x0,-40-y0)
    for cp in PUNCT_LEFT:                # left side of the cell, height unchanged
        if cp in cmap:
            x0,y0,x1,y1=bounds(cmap[cp]); moved+=move(cmap[cp],150-x0,0)
if MODE in('VC','NC'):               # mainland quotation marks: 「」 -> “”, 『』 -> ‘’ (horizontal glyphs only; vertical forms keep corner brackets)
    for tgt,src,dx in [(0x300C,0x201C,512),(0x300D,0x201D,0),(0x300E,0x2018,512),(0x300F,0x2019,0)]:
        tn,sn=cmap[tgt],cmap[src]
        if sum(1 for c in cmap if cmap[c]==tn)!=1:   # S2T/T2S: the converter already shares the glyph with “ ” ‘ ’, leave as is
            print('quotes shared, kept',hex(tgt)); continue
        rec=DecomposingRecordingPen(gs); gs[sn].draw(rec)
        pen=TTGlyphPen(gs); rec.replay(TransformPen(pen,(1,0,0,1,dx,0)))
        g=pen.glyph(); f['glyf'][tn]=g; g.recalcBounds(f['glyf'])
        f['hmtx'][tn]=(1024,g.xMin)
        if 'vmtx' in f: f['vmtx'][tn]=(f['vmtx'][tn][0],864-g.yMax)
        moved+=1
print(MODE,'moved',moved)
for r in f['name'].names:
    if r.nameID in (1,4,6,16): r.string=FAM
    if r.nameID==3: r.string='2.1;'+FAM
f.save(OUT)
