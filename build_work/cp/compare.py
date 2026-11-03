"""Side-by-side main vs CP comparison PNG (horizontal + vertical) via headless Chrome."""
import subprocess
R='/Users/seky/Developer/Git/Huiwen-mincho/'
t="「你好」『書名』（補足）〔註〕【標題】《卷》，。、；：！？・…—～★☆○●◎□■"
def col(font,vert,label):
    wm='vertical-rl' if vert else 'horizontal-tb'
    return f'<div class=c><b>{label}</b><div style="font-family:{font};writing-mode:{wm}">{t}</div></div>'
html=f'''<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:M;src:url("file://{R}HuiwenMincho-AI-v2.1.ttf")}}
@font-face{{font-family:C;src:url("file://{R}HuiwenMincho-AI-v2.1-CP.ttf")}}
body{{margin:20px;background:#fff;font-size:44px;line-height:1.4}}
b{{font:16px sans-serif;display:block;margin-bottom:4px}}
.c div{{background-image:linear-gradient(#0000,#0000)}}
.h .c{{margin-bottom:14px}}
.v{{display:flex;gap:30px;margin-top:20px}}
.v .c div{{height:1000px}}
</style><div class=h>{col('M',0,'Main')}{col('C',0,'CP (centred)')}</div>
<div class=v>{col('M',1,'Main')}{col('C',1,'CP (centred)')}</div>'''
open(R+'build_work/cp/compare.html','w').write(html)
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless=new','--disable-gpu','--allow-file-access-from-files',f'--screenshot={R}example/cp_comparison.png','--window-size=1700,1250','--hide-scrollbars','file://'+R+'build_work/cp/compare.html'],capture_output=True)
