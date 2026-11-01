# The Weapon Mastery frame page (#416) is chrome.html (Vesna's Trade, #361) with the skill-tree labels: one kit, three screens.
#   python make_skill_html.py  ->  skilltree.html
import os
HERE = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(HERE, 'chrome.html'), encoding='utf-8').read()
REPL = [
    ('<script src="layout.js"></script>', '<script src="layout_sk.js"></script>'),
    ("<!-- Vesna's Trade frame (#361).", "<!-- The Weapon Mastery frame (#416), generated from chrome.html by make_skill_html.py."),
    ("'VESNA’S TRADE'", "'WEAPON MASTERY'"),
    ("'ARMOUR  •  WEAPONS  •  SUPPLIES'", "'CROSSBOW  •  SWORD  •  AURAS'"),
    ("el('div','rule',`left:600px;top:93px;width:56px`); el('div','rule',`left:1016px;top:93px;width:56px`);",
     "el('div','rule',`left:580px;top:93px;width:56px`); el('div','rule',`left:1036px;top:93px;width:56px`);"),
    ("  crest:", "  xbow:`<path ${GS} d=\"M3 10c5-4 17-4 22 0 M4 11l10 4 10-4 M14 5v20 M12 23h4\"/>`,\n"
              "  sword:`<path ${GS} d=\"M14 2l2 3v15h-4V5z M8 20h12 M14 21v5\"/>`,\n"
              "  aura:`<path ${GS} d=\"M14 4l7 3v6c0 6-3 9-7 11-4-2-7-5-7-11V7z M14 1v2 M3 12H1 M27 12h-2\"/>`,\n"
              "  spt:`<path d=\"M14 2l3.4 9.2L27 14l-9.6 3.6L14 27l-3.4-9.4L1 14l9.6-2.8z\" fill=\"#f0c66e\" stroke=\"#fff0c0\"/>`,\n"
              "  lvl:`<path ${GS} d=\"M14 3l10 6v10l-10 6-10-6V9z M9 15l5-5 5 5 M9 20l5-5 5 5\"/>`,\n  crest:"),
    # purse: free skill points / hero level / points spent
    ("ico('coin',pu.gold[0],pu.cy,26); ico('ingot',pu.iron[0],pu.cy,30); ico('ore',pu.silver[0],pu.cy,30);",
     "ico('spt',pu.gold[0],pu.cy,28); ico('lvl',pu.iron[0]+40,pu.cy,28);"),
    ("ico(['', 'helm','knight','flask'][i]", "ico(['xbow','sword','aura'][i]"),
    ("svg(lh.laurel,lh.cy,40,40,ICON.laurel);", "svg(lh.laurel,lh.cy,40,40,ICON.laurel);"),
    ("text(lh.text,lh.cy,'SOVEREIGN SET',", "text(lh.text,lh.cy,'THE TREE',"),
    ("ico('shield',c.shield[0],c.shield[1],34);", "ico('spt',c.shield[0],c.shield[1],32);"),
    ("text(616,609,'Defence',", "text(616,609,'Next rank costs',"),
    ("text(826,604,'Compare',", "text(826,604,'Rank',"),
    ("text(826,637,'Current','font-size:17px;font-weight:600;color:var(--cream)');\n", ""),
    ("text(975,637,'After','font-size:17px;font-weight:600;color:var(--cream)');\n", ""),
    ("svg(c.arr,637,10,12,`<path d=\"M1 1l8 5-8 5z\" fill=\"#ece2cf\"/>`);\n", ""),
    ("'Set Bonus — Sovereign Set'", "'What it does'"),
    ("'EQUIPMENT'", "'MASTERY'"), ("'SET PROGRESS'", "'RULES'"),
    ("hint(45,['ESC'],'Close',118); hint(280,['A','D'],'Navigate',370); hint(528,['E'],'Buy / Equip',577); hint(770,['F'],'Compare',823);",
     "hint(45,['ESC'],'Close',118); hint(260,['W','S'],'Navigate',350); hint(508,['E'],'Learn rank',557); hint(740,['LB','RB'],'Tabs',866);"),
    ("hint(996,['R'],'Rotate Preview',1053); hint(1266,['mouseW'],'Zoom',1303); hint(1490,['mouseL'],'Rotate',1535);",
     "hint(1000,['Q'],'Mastery / Rules',1042); hint(1290,['mouseL'],'Select',1327); hint(1440,['mouseL','mouseL'],'Learn',1520);"),
    ("s.src='live.js'", "s.src='live_sk.js'"),
    ("rgba(70,82,104,.42),rgba(40,46,60,.18) 45%", "rgba(150,58,30,.40),rgba(90,30,20,.16) 45%"),
    ("if(M==='overlay')", "if(false)"),
]
for a, b in REPL:
    if a not in t: raise SystemExit('not found: ' + a[:70])
    t = t.replace(a, b)
# the paper doll and the hero stats box go (the mastery list and the key list are drawn live)
i = t.index('const hr=L.hero;'); j = t.index('// ---------------------------------------------------------------- bottom hints')
t = t[:i] + t[j:]
# no turntable arrows / dots for skills
t = t.replace("svg(L.arrows.l,L.arrows.cy,22,30,ICON.arrowL); svg(L.arrows.r,L.arrows.cy,22,30,ICON.arrowR);", "")
open(os.path.join(HERE, 'skilltree.html'), 'w', encoding='utf-8').write(t)
print('skilltree.html written')
