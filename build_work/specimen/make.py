"""Render horizontal and vertical specimen PNGs (box drawing + diverse characters) with the final font via headless Chrome."""
import subprocess, sys
from fontTools.ttLib import TTFont
R='/Users/seky/Developer/Git/Huiwen-mincho/'
cm=set(TTFont(R+'HuiwenMincho-AI-v2.1.ttf').getBestCmap())
def ok(s):
    miss=[c for c in s if c not in '\n ' and ord(c) not in cm]; return miss
rows=["┌─┬─┐　╔═╦═╗　┏━┳━┓","│　│　│　║　║　║　┃　┃　┃","├─┼─┤　╠═╬═╣　┣━╋━┫","│　│　│　║　║　║　┃　┃　┃","└─┴─┘　╚═╩═╝　┗━┻━┛"]
box="\n".join(rows)+"\n"+"▀▄█▌▐░▒▓　■□▲△●○◆◇★☆"
latin="Pack my box with five dozen liquor jugs. Ǆžuhľ Œuvre Ǣ ǂ ĳ ŉ Ƿ Ṳ ỳ Ằ ế ǭ ɐ ʃ ʒ ə ŋ ɔ ˈ ˌ ː Ά έ ή ί ϊ ΐ ό ύ ώ ᾳ ᾴ ἀ ἄ ᾄ ῷ Щ Ж Ђ Ѣ ѣ Ӂ ӂ"
cjk="天地玄黃，宇宙洪荒。日月盈昃，辰宿列張。\n學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？\nあいうえお かきくけこ アイウエオ ｶﾞｷﾞｸﾞ ㄅㄆㄇㄈ ㈠㈡㈢ ㊀㊁ ①②③ ⑴⑵ ⒈⒉\n「引用」『書名』（補足）〔註〕【標題】《卷》〈篇〉……——～、。；：！？"
sym="€ £ ¥ ₩ ₽ ₠ ₡ ₣ ₤ ₦ ₧ ₨ ₫ ₭ ₮ ₱ ₲ ₵ ₸ ₿  ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ ₀₁₂₃₄₅₆₇₈₉₊₋  ± × ÷ ≠ ≤ ≥ ≈ ∞ ∑ √ ∫ ← → ↑ ↓ ↔ ⇒ ™ © ® ℃ ℉ № ℓ"
for nm,s in [('box',box),('latin',latin),('cjk',cjk),('sym',sym)]: print(nm,'missing',ok(s))
def html(fam,vert,txt,cls=''):
    return txt
def page(file,font,vertical):
    wm='vertical-rl' if vertical else 'horizontal-tb'
    blocks=[box,latin,cjk,sym]
    body=''.join(f'<pre>{b}</pre>' for b in blocks)
    return f'''<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:H;src:url("file://{R}{font}")}}
body{{margin:0;background:#fff;color:#111;font-family:H;font-size:34px;line-height:1.5;padding:30px;
 {"height:900px;width:1250px;writing-mode:vertical-rl;" if vertical else "width:1500px;"}}}
pre{{font-family:H;margin:0 0 {"0 1.5em" if vertical else "1em 0"};white-space:pre-wrap;{"display:inline-block;" if vertical else ""}}}
</style><body lang=zh-Hant>{body}'''
for nm,font,v,w,h in [('horizontal','HuiwenMincho-AI-v2.1.ttf',False,1560,880),('vertical','HuiwenMincho-AI-v2.1.ttf',True,1310,960)]:
    p=R+f'build_work/specimen/{nm}.html'; open(p,'w').write(page(p,font,v))
    subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless=new','--disable-gpu','--allow-file-access-from-files',f'--screenshot={R}example/specimen_{nm}.png',f'--window-size={w},{h}','--hide-scrollbars',f'file://{p}'],capture_output=True)
