"""Build HuiwenMincho-AI-v2.1-CP.ttf: the main font with every full-width symbol / punctuation glyph centred in the em box."""
import unicodedata as U, copy, sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib.tables._n_a_m_e import NameRecord
R='/Users/seky/Developer/Git/Huiwen-mincho/'
SRC=R+'HuiwenMincho-AI-v2.1.ttf'; OUT=R+'build_work/cp/HuiwenMincho-AI-v2.1-CP.ttf'
CX,CY=512,352          # centre of the em box: x=1024/2, y=(864-160)/2
f=TTFont(SRC); cmap=f.getBestCmap(); gs=f.getGlyphSet(); hm=f['hmtx']
def is_symbol(cp):
    c=U.category(chr(cp)); return c[0] in 'PS'
cands=[]
for cp,g in cmap.items():
    if cp<0x2000 and not (0xB0<=cp<=0xB7): 
        continue            # plain Latin/Greek/Cyrillic punctuation keeps its baseline design
    if 0x2500<=cp<=0x259F: continue          # box drawing and blocks must keep joining
    if not is_symbol(cp) and not (0x3000<=cp<=0x303F and U.category(chr(cp)) in ('Zs','Cf')): continue
    if hm[g][0]!=1024: continue                # only full-width glyphs
    cands.append(cp)
# vertical alternates of those glyphs
gsub=f['GSUB'].table; vert={}
for fr in gsub.FeatureList.FeatureRecord:
    if fr.FeatureTag in ('vert','vrt2'):
        for i in fr.Feature.LookupListIndex:
            for st in gsub.LookupList.Lookup[i].SubTable:
                st=getattr(st,'ExtSubTable',st)
                if hasattr(st,'mapping'): vert.update(st.mapping)
names={cmap[c] for c in cands}
names|={vert[n] for n in list(names) if n in vert}
names|={n for n in vert.values() if any(n==vert.get(cmap[c]) for c in cands)}
moved=0; skipped=[]
for n in sorted(names):
    bp=BoundsPen(gs); gs[n].draw(bp)
    if not bp.bounds: continue
    x0,y0,x1,y1=bp.bounds
    if x1-x0>900 or y1-y0>900: skipped.append(n); continue       # cell-filling shapes keep their place
    dx=round(CX-(x0+x1)/2); dy=round(CY-(y0+y1)/2)
    if dx==0 and dy==0: continue
    rec=DecomposingRecordingPen(gs); gs[n].draw(rec)
    pen=TTGlyphPen(gs); tp=TransformPen(pen,(1,0,0,1,dx,dy)); rec.replay(tp)
    g=pen.glyph(); f['glyf'][n]=g; g.recalcBounds(f['glyf'])
    f['hmtx'][n]=(hm[n][0],g.xMin)
    if 'vmtx' in f: f['vmtx'][n]=(f['vmtx'][n][0],864-g.yMax)
    moved+=1
print('candidates',len(cands),'glyph names',len(names),'moved',moved,'skipped(cell-filling)',len(skipped))
# names
fam='HuiwenMincho-AI-v2.1-CP'
for r in f['name'].names:
    if r.nameID in (1,4,6,16): r.string=fam
    if r.nameID==3: r.string='2.1;'+fam
f.save(OUT); print('saved',OUT)
