# Weapon Mastery (#416): the skill tree in the same kit as Vesna's Trade (#361) and the Muster (#359). Same panel geometry
# (layout.py), skill content.   python layout_sk.py -> layout_sk.js (skilltree.html / atlas.html?L=sk) + layout_sk.json (gen_skill.py)
# Game rules are the live BP_SkillTreeHUD ones (10-30 export, CX_4791..4843), unchanged:
#   ranks live in MPC_SkillTree (RkA.R, RkA.G, RkB.G, RkB.B, RkB.A), max rank 3, the next rank costs (rank + 1) points,
#   free points = hero Level - St.A (points spent). Sealed rows are the tree's unrevealed slots ("A forgotten technique").
import json, os
from layout import L as LT, TW, TH, S, pack
HERE = os.path.dirname(os.path.abspath(__file__))

TABS = ['CROSSBOW', 'SWORD', 'AURAS']
# items: key, tab, row name, title, tag, glyph, description (2 lines), rank source (MPC param, channel) or aura id, key hint
ITEMS = [
    ('blast',   0, 'Blast Bolt',    'BLAST BOLT',     'CROSSBOW  •  ACTIVE', 'blast',  ('Bolts explode on impact, hurting nearby foes.',), ('RkA', 'R'), ''),
    ('charge',  0, 'Charged Shot',  'CHARGED SHOT',   'CROSSBOW  •  ACTIVE', 'charge', ('Hold to charge one heavy, piercing bolt.',), ('RkA', 'G'), ''),
    ('whirl',   1, 'Whirlwind',     'WHIRLWIND',      'SWORD  •  ACTIVE', 'whirl',  ('Spin in a full circle, slashing all around you.',), ('RkB', 'G'), ''),
    ('quake',   1, 'Quake Slam',    'QUAKE SLAM',     'SWORD  •  ACTIVE', 'quake',  ('Leap and smash the ground: a quake hits all around.',), ('RkB', 'B'), ''),
    ('fissure', 1, 'Fissure',       'FISSURE',        'SWORD  •  ACTIVE', 'fissure', ('Slam a zig-zag crack that rips straight ahead.',), ('RkB', 'A'), ''),
    ('adef',    2, 'Defense Aura',  'DEFENSE AURA',   'PASSIVE  •  KEY 4', 'adef',  ('Key 4: 12 s, +2 s per rank, then it recharges.',), 'AuraDef', '4'),
    ('aheal',   2, 'Healer Aura',   'HEALER AURA',    'PASSIVE  •  KEY 5', 'aheal', ('Key 5: 12 s, +2 s per rank, then it recharges.',), 'AuraHeal', '5'),
    ('aburn',   2, 'Selfburn Aura', 'SELFBURN AURA',  'PASSIVE  •  KEY 6', 'aburn', ('Key 6: 12 s, +2 s per rank, then it recharges.',), 'AuraBurn', '6'),
]
SEALED = {0: 3, 1: 2, 2: 0}          # sealed slots under each tab (the tree's ??? rows), drawn after the real ones
ROWS_PER_TAB = 5

L = dict(LT)
L.update(dict(
    TW=TW, TH=TH, S=S, tabnames=TABS, sealed=SEALED, maxrank=3,
    tabs=[dict(cx=530, lx=560, x0=420, x1=640, icon=470), dict(cx=830, lx=850, x0=725, x1=935, icon=790),
          dict(cx=1130, lx=1150, x0=1020, x1=1240, icon=1090)],
    rows=dict(LT['rows'], n=5),
    # left: the tree (rows + a spine through the icon discs)
    spine=dict(x=84, w=3),
    # centre: rank pips under the glyph, cost box, what-it-does box
    rankpips=dict(cx=815, y=566, step=34),
    cost=dict(x=540, y=590, w=545, h=72, div=793),
    # right panel: MASTERY (all ranks) / KEYS
    rtabs=dict(y=200, h=38, eq=(1198, 1400), sp=(1400, 1640)),
    mastery=dict(head0=262, x=1160, label=1214, pip0=1490, pipstep=28, icon=1186, step=40),
    keys=dict(y0=690, step=36),
))

def cells():
    c = []
    for k, tab, name, title, tag, glyph, desc, src, key in ITEMS:
        c += [('name_' + k, 220, 30, 'name', name), ('title_' + k, 470, 40, 'title', title), ('tag_' + k, 220, 24, 'tag', tag),
              ('d1_' + k, 500, 24, 'desc', desc[0])]
    for k, n in enumerate(TABS): c.append(('tab%d' % k, 220, 50, 'tab', n))
    c += [('name_sealed', 220, 30, 'name', '???'), ('d_sealed', 500, 24, 'desc', 'A forgotten technique. Not yet revealed.'),
          ('rtab0', 202, 38, 'rtab', 'MASTERY'), ('rtab1', 240, 38, 'rtab', 'RULES'),
          ('learnhint', 500, 24, 'desc', 'Press E or double-click the skill to learn the next rank.'),
          ('rsel', 447, 74, 'rsel', ''), ('maxed', 130, 26, 'state', 'MASTERED'), ('sealed', 110, 26, 'state', 'SEALED'),
          ('btn_on', 530, 44, 'btn', 'on'), ('btn_off', 530, 44, 'btn', 'off'), ('key_e', 36, 26, 'key', 'E'),
          ('pip_on', 16, 16, 'pip', 'on'), ('pip_off', 16, 16, 'pip', 'off'), ('bigpip_on', 26, 26, 'bigpip', 'on'), ('bigpip_off', 26, 26, 'bigpip', 'off'),
          ('spt', 26, 26, 'spt', ''), ('nopts', 380, 26, 'msg', 'Not enough skill points, hunter.'),
          ('ring', 64, 64, 'ring', ''), ('ring_on', 64, 64, 'ring', 'on')]
    for g in sorted({i[5] for i in ITEMS} | {'lock'}): c.append(('glyph_' + g, 128, 128, 'glyph', g))
    return c

def write():
    L['atlas'] = pack(cells())
    L['items'] = [dict(key=k, tab=t, name=n, title=ti, tag=tg, glyph=g, desc=list(d), src=s, hotkey=hk) for k, t, n, ti, tg, g, d, s, hk in ITEMS]
    open(os.path.join(HERE, 'layout_sk.json'), 'w').write(json.dumps(L, indent=1))
    open(os.path.join(HERE, 'layout_sk.js'), 'w').write('window.L = ' + json.dumps(L) + ';\n')
    return L

if __name__ == '__main__':
    write(); print('skill layout: %d items, %d atlas cells' % (len(ITEMS), len(L['atlas'])))
