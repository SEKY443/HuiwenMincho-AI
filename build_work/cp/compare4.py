"""Four-way centring comparison PNG: horizontal and vertical, using the main-font family files."""
import subprocess,sys
R='/Users/seky/Developer/Git/Huiwen-mincho/'
sfx=sys.argv[1] if len(sys.argv)>1 else ''   # '' | -S2T | -T2S
vs=[('Main (HC): horizontal centred','HuiwenMincho-AI-v2.1'),('VC: vertical centred','build_work/variants/VC'),('AC: all centred','HuiwenMincho-AI-v2.1-CP'),('NC: none centred','build_work/variants/NC')]
t="「你好」『書名』（補足）〔註〕《卷》，。、；：！？・…—～★○"
ff=''.join(f'@font-face{{font-family:F{i};src:url("file://{R}{p}.ttf")}}' for i,(l,p) in enumerate(vs))
h=''.join(f'<div class=c><b>{l}</b><div style="font-family:F{i}">{t}</div></div>' for i,(l,p) in enumerate(vs))
v=''.join(f'<div class=c><b>{l.split(":")[0]}</b><div class=v style="font-family:F{i}">{t}</div></div>' for i,(l,p) in enumerate(vs))
html=f'<!doctype html><meta charset=utf-8><style>{ff}body{{margin:20px;background:#fff;font-size:44px;line-height:1.4}}b{{font:15px sans-serif;display:block;color:#666}}.v{{writing-mode:vertical-rl;height:900px}}.row{{display:flex;gap:26px;margin-top:16px}}</style>{h}<div class=row>{v}</div>'
open(R+'build_work/cp/compare4.html','w').write(html)
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless=new','--disable-gpu','--allow-file-access-from-files',f'--screenshot={R}example/centring_comparison.png','--window-size=1300,1300','--hide-scrollbars','file://'+R+'build_work/cp/compare4.html'],capture_output=True)
