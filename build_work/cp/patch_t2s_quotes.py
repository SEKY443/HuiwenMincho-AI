"""T2S fonts: make the quotes shown for 「」『』 full-width (1 em cell) instead of the half-width “ ” ‘ ’ glyphs.
New glyphs cn_<name> reuse the outline of the half-width glyph, placed in the right (opening) or left (closing) half of the cell.
Western U+201C/D and U+2018/9 keep the half-width glyphs; vertical forms (vert/vrt2) are copied from the old target."""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
p=sys.argv[1]; f=TTFont(p); gs=f.getGlyphSet(); cmap=f.getBestCmap()
order=f.getGlyphOrder(); new=[]
vsubs=[]
for fr in f['GSUB'].table.FeatureList.FeatureRecord:
    if fr.FeatureTag in('vert','vrt2'):
        for i in fr.Feature.LookupListIndex:
            for st in f['GSUB'].table.LookupList.Lookup[i].SubTable:
                st=getattr(st,'ExtSubTable',st)
                if hasattr(st,'mapping') and st not in vsubs: vsubs.append(st)
for cp,dx in [(0x300C,512),(0x300D,0),(0x300E,512),(0x300F,0)]:
    src=cmap[cp]
    if f['hmtx'][src][0]==1024: print('already full width',hex(cp)); continue
    nn='cn_'+src
    rec=DecomposingRecordingPen(gs); gs[src].draw(rec)
    pen=TTGlyphPen(gs); rec.replay(TransformPen(pen,(1,0,0,1,dx,0)))
    g=pen.glyph(); f['glyf'].glyphs[nn]=g; new.append(nn); g.recalcBounds(f['glyf'])
    f['hmtx'].metrics[nn]=(1024,g.xMin)
    f['vmtx'].metrics[nn]=(f['vmtx'][src][0],864-g.yMax)
    for st in vsubs:
        if src in st.mapping: st.mapping[nn]=st.mapping[src]
    for t in f['cmap'].tables:
        if cp in t.cmap: t.cmap[cp]=nn
f.setGlyphOrder(order+new); f['glyf'].glyphOrder=order+new
print(p,'new glyphs',new)
f.save(p)
