# The Muster frame page (#359) is chrome.html (Vesna's Trade, #361) with the barracks labels: one kit, two screens.
#   python make_muster_html.py  ->  muster.html
import os
HERE = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(HERE, 'chrome.html'), encoding='utf-8').read()
REPL = [
    ('<script src="layout.js"></script>', '<script src="layout_mu.js"></script>'),
    ("<!-- Vesna's Trade frame (#361).", "<!-- The Muster frame (#359), generated from chrome.html by make_muster_html.py."),
    ("'VESNA’S TRADE'", "'THE MUSTER'"),
    ("'ARMOUR  \u2022  WEAPONS  \u2022  SUPPLIES'", "'RECRUIT  \u2022  ARTILLERY  \u2022  FORTIFY  \u2022  SUPPLIES'"),
    ("el('div','rule',`left:600px;top:93px;width:56px`); el('div','rule',`left:1016px;top:93px;width:56px`);",
     "el('div','rule',`left:520px;top:93px;width:56px`); el('div','rule',`left:1096px;top:93px;width:56px`);"),
    ("  crest:", "  cannon:`<path ${GS} d=\"M3 17l17-7 2 5-17 7z M20 11l4-2 2 5-4 2 M7 22a3 3 0 1 0 .1 0z M13 22a3 3 0 1 0 .1 0z\"/>`,\n"
              "  tower:`<path ${GS} d=\"M8 26V11h12v15z M6 11V6h4v3h3V6h3v3h3V6h3v5z\"/>`,\n"
              "  copper:`<path d=\"M4 20l5-9h14l-5 9z\" fill=\"#b8733a\" stroke=\"#f0b27a\"/><path d=\"M4 20h14v4H4z\" fill=\"#8c5426\"/>`,\n"
              "  goldore:`<path d=\"M5 22l3-9 6-4 7 3 3 8-5 4H9z\" fill=\"#c9a13a\" stroke=\"#ffe08a\"/>`,\n  crest:"),
    ("ico(['', 'helm','knight','flask'][i]", "ico(['', 'cannon','tower','flask'][i]"),
    ("svg(lh.laurel,lh.cy,40,40,ICON.laurel);", "ico('swords',lh.laurel,lh.cy,30);"),
    ("text(lh.text,lh.cy,'SOVEREIGN SET',", "text(lh.text,lh.cy,'THE BARRACKS',"),
    ("ico('shield',c.shield[0],c.shield[1],34);", "ico('coin',c.shield[0],c.shield[1],30);"),
    ("text(616,609,'Defence',", "text(616,609,'Cost',"),
    ("text(826,604,'Compare',", "text(826,604,'Treasury',"),
    ("text(826,637,'Current','font-size:17px;font-weight:600;color:var(--cream)');\n", ""),
    ("text(975,637,'After','font-size:17px;font-weight:600;color:var(--cream)');\n", ""),
    ("svg(c.arr,637,10,12,`<path d=\"M1 1l8 5-8 5z\" fill=\"#ece2cf\"/>`);\n", ""),
    ("'Set Bonus \u2014 Sovereign Set'", "'What it does'"),
    ("'EQUIPMENT'", "'GARRISON'"), ("'SET PROGRESS'", "'CASTLE'"),
    ("[['shield','Defence'],['swords','Damage'],['foot','Move Speed'],['heart','Health']]", "[['ingot','Iron'],['copper','Copper'],['ore','Silver'],['goldore','Gold ore']]"),
    ("svg(st.arr,st.rows[0],10,12,`<path d=\"M1 1l8 5-8 5z\" fill=\"#ece2cf\"/>`);\n", ""),
    ("hint(45,['ESC'],'Close',118); hint(280,['A','D'],'Navigate',370); hint(528,['E'],'Buy / Equip',577); hint(770,['F'],'Compare',823);",
     "hint(45,['ESC'],'Close',118); hint(280,['A','D'],'Navigate',370); hint(528,['E'],'Recruit / Buy',577); hint(790,['LB','RB'],'Tabs',916);"),
    ("hint(996,['R'],'Rotate Preview',1053); hint(1266,['mouseW'],'Zoom',1303); hint(1490,['mouseL'],'Rotate',1535);",
     "hint(1040,['Q'],'Garrison / Castle',1082); hint(1320,['mouseW'],'Scroll',1357); hint(1490,['mouseL'],'Select',1535);"),
    ("s.src='live.js'", "s.src='live_mu.js'"),
    ("if(M==='overlay')", "if(false)"),
]
for a, b in REPL:
    if a not in t: raise SystemExit('not found: ' + a[:70])
    t = t.replace(a, b)
# the paper-doll slots go (the garrison / castle lists are drawn live)
i = t.index('const sl=L.slot;'); j = t.index('const st=L.stats;')
t = t[:i] + t[j:]
open(os.path.join(HERE, 'muster.html'), 'w', encoding='utf-8').write(t)
print('muster.html written')
