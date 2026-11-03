"""Per-language specimen PNGs and a font-version comparison PNG, rendered with the final fonts via headless Chrome."""
import subprocess, os
from fontTools.ttLib import TTFont
R='/Users/seky/Developer/Git/Huiwen-mincho/'; OUT=R+'example/'; W=R+'build_work/specimen/'
cm=set(TTFont(R+'HuiwenMincho-AI-v2.1.ttf').getBestCmap())
CHROME='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
L=[('english','English','en','The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.\nHow vexingly quick daft zebras jump! “Quotes”, ‘single’ — dashes, (brackets) & 1234567890.'),
('french','Français','fr','Portez ce vieux whisky au juge blond qui fume. Où est l’été ? Cœur, œuvre, naïve, façade,\nnoël, être, hôtel, garçon, à bientôt — « bonjour ».'),
('german','Deutsch','de','Zwölf Boxkämpfer jagen Viktor quer über den großen Sylter Deich. Äpfel, Öl, Übung.\nFranz jagt im komplett verwahrlosten Taxi quer durch Bayern.'),
('spanish','Español','es','El veloz murciélago hindú comía feliz cardillo y kiwi. La cigüeña tocaba el saxofón.\n¿Dónde está la niña? ¡Qué sorpresa! Año nuevo, vida nueva.'),
('portuguese','Português','pt','À noite, vovô Kowalsky vê o ímã cair no pé do pinguim queixoso e vovó põe açúcar.\nCoração, informação, avô, atenção, você, já é.'),
('polish','Polski','pl','Zażółć gęślą jaźń. Pchnąć w tę łódź jeża lub ośm skrzyń fig.\nŁódź, święto, źdźbło, żółw, ąę, ćńóśźż.'),
('czech','Čeština','cs','Příliš žluťoučký kůň úpěl ďábelské ódy. Nechť již hříšné saxofony ďáblů rozezvučí síň úděsnou.'),
('hungarian','Magyar','hu','Árvíztűrő tükörfúrógép. Egy hűtlen vejét fia dühöngött; öt ősz hölgy űzött kő.'),
('turkish','Türkçe','tr','Pijamalı hasta yağız şoföre çabucak güvendi. İstanbul, Işık, ığdır, Ağrı, çöl, şiir.'),
('romanian','Română','ro','Muzicologă în bej vând whisky și tequila, preț fix. Ăâîșț ĂÂÎȘȚ, ținut, șoaptă, țară.'),
('icelandic','Íslenska','is','Kæmi ný öxi hér ykist þjófum nú bæði víl og ádrepa. Þórður, Æðey, ðþæö.'),
('vietnamese','Tiếng Việt','vi','Tiếng Việt: Ăn quả nhớ kẻ trồng cây. Đây là chữ ế, ề, ể, ễ, ệ, ơ, ờ, ở, ỡ, ợ, ư, ừ, ử, ữ, ự, ỳ, ỷ, ỹ, ỵ.'),
('greek','Ελληνικά','el','Ξεσκεπάζω την ψυχοφθόρα βδελυγμία. Καλημέρα, ήλιος, ώρα, ΐ ΰ ϊ ϋ.'),
('greek_polytonic','Ἑλληνικά (πολυτονικά)','grc','Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος. ᾄ ῷ ῳ ἄλφα.'),
('russian','Русский','ru','Съешь же ещё этих мягких французских булок, да выпей чаю. Щ ж ё ъ ы э ю я.'),
('ukrainian','Українська','uk','Чуєш їх, доцю, га? Кумедна ж ви пта! Їжак, є, ґанок, Київ, дуже добре.'),
('serbian','Српски','sr','Љубазни фењерџија чађавог лица хоће да ми покаже штос. Ђ ј љ њ ћ џ.'),
('bulgarian','Български','bg','Жълтата дюля беше щастлива, че пухът, който цъфна, замръзна като гьон. Ъ ь ю я.'),
('kazakh','Қазақша','kk','Қазақ тілі: Ә ә Ғ ғ Қ қ Ң ң Ө ө Ұ ұ Ү ү Һ һ І і. Менің атым Айгерім.'),
('chinese_traditional','正體中文','zh-Hant','天地玄黃，宇宙洪荒。日月盈昃，辰宿列張。\n學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？人不知而不慍，不亦君子乎？'),
('chinese_simplified','简体中文','zh-Hans','天地玄黄，宇宙洪荒。日月盈昃，辰宿列张。\n学而时习之，不亦说乎？有朋自远方来，不亦乐乎？人不知而不愠，不亦君子乎？'),
('japanese','日本語','ja','いろはにほへと ちりぬるを わかよたれそ つねならむ。吾輩は猫である。名前はまだ無い。\nアイウエオ カキクケコ、ガギグゲゴ。「日本語」の表示。'),
('bopomofo','注音符號','zh-Hant','ㄅㄆㄇㄈ ㄉㄊㄋㄌ ㄍㄎㄏ ㄐㄑㄒ ㄓㄔㄕㄖ ㄗㄘㄙ ㄧㄨㄩ ㄚㄛㄜㄝ ㄞㄟㄠㄡ ㄢㄣㄤㄥㄦ。\n你好嗎？我很好，謝謝。 臺灣話、客家話的擴充注音：ㆠㆡㆢㆣ ㆤㆥㆦㆧㆨㆩㆪㆫㆬㆭㆮㆯㆰㆱㆲㆳ'),
]
def shot(html,png,w,h):
    open(html,'w').write(html_s[0]); subprocess.run([CHROME,'--headless=new','--disable-gpu','--allow-file-access-from-files',f'--screenshot={png}',f'--window-size={w},{h}','--hide-scrollbars','file://'+html],capture_output=True)
html_s=['']
def ff(n,f): return f'@font-face{{font-family:{n};src:url("file://{R}{f}")}}'
css=ff('M','HuiwenMincho-AI-v2.1.ttf')+'body{margin:0;background:#fff;color:#111}.p{padding:26px 34px 28px}h1{font:15px/1 -apple-system,sans-serif;color:#777;margin:0 0 12px}pre{font-family:M;font-size:34px;line-height:1.55;margin:0;white-space:pre-wrap}'
for old in os.listdir(OUT): os.remove(OUT+old)
for key,name,lang,txt in L:
    miss=sorted({c for c in txt if c not in '\n ' and ord(c) not in cm})
    if miss: print(key,'MISSING',miss)
    html_s[0]=f'<!doctype html><meta charset=utf-8><style>{css}</style><div class=p><h1>{name}</h1><pre lang="{lang}">{txt}</pre></div>'
    h=130+55*(txt.count('\n')+1+len(txt)//52)
    shot(W+'lang.html',OUT+f'lang_{key}.png',1500,h)
# version comparison
rows=[('Main — traditional input','M','頭髮、皇后、發財、後來、裡面、乾淨、幹部、台灣「你好」，。'),
('Main — simplified input','M','头发、皇后、发财、后来、里面、干净、干部、台湾「你好」，。'),
('S2T — simplified input, traditional shown','S','头发、皇后、发财、后来、里面、干净、干部、台湾「你好」，。'),
('T2S — traditional input, simplified shown','T','頭髮、皇后、發財、後來、裡面、乾淨、幹部、台灣「你好」，。'),
('CP — punctuation and symbols centred','C','頭髮、皇后、發財、後來、裡面、乾淨、幹部、台灣「你好」，。（★）')]
fonts=ff('S','HuiwenMincho-AI-v2.1-S2T.ttf')+ff('T','HuiwenMincho-AI-v2.1-T2S.ttf')+ff('C','HuiwenMincho-AI-v2.1-CP.ttf')
body=''.join(f'<h1>{l}</h1><pre style="font-family:{f}" lang="zh-Hant">{t}</pre><br>' for l,f,t in rows)
html_s[0]=f'<!doctype html><meta charset=utf-8><style>{css}{fonts}</style><div class=p>{body}</div>'
shot(W+'versions.html',OUT+'versions_comparison.png',1500,760)
