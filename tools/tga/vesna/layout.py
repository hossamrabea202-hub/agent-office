# Vesna's Trade (#361, owner target 2026-10-31 22:14): one layout for everything.
#   python layout.py  ->  layout.js (read by chrome.html / atlas.html) + layout.json (read by gen_trade.py)
# Units are TARGET pixels (handoffs/vesna-trade-361/owner_target.png is 1672 x 941). In game every value is
# multiplied by S = 1920/1672 and then by the screen scale (SizeY/1080, centred), so the frame texture
# (rendered at 1920 x 1080) and the live layer always line up.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
TW, TH = 1672, 941
S = 1920.0 / TW

# ---- pieces: BPC_ObsidianSet ids (handoffs/obsidian-set-v2/pieces.csv). list order = the target's order (chest, arms, legs)
PIECES = [  # id, row name, title, slot tag, DEF, art folder (turntable) or None
    (10, 'Cuirass',    'SOVEREIGN CUIRASS',    'CHEST',             45, 'Chest'),
    (11, 'Pauldrons',  'SOVEREIGN PAULDRONS',  'SHOULDERS (PAIR)',  12, 'Shoulders'),
    (12, 'Gauntlets',  'SOVEREIGN GAUNTLETS',  'HANDS (PAIR)',       8, 'Gauntlets'),
    (17, 'Vambraces',  'SOVEREIGN VAMBRACES',  'FOREARMS (PAIR)',    8, 'Forearms'),
    (16, 'Rerebraces', 'SOVEREIGN REREBRACES', 'UPPER ARMS (PAIR)',  8, 'UpperArms'),
    (18, 'Fauld',      'SOVEREIGN FAULD',      'WAIST',             10, 'Waist'),
    (19, 'Cuisses',    'SOVEREIGN CUISSES',    'THIGHS (PAIR)',     12, 'Thighs'),
    (14, 'Greaves',    'SOVEREIGN GREAVES',    'SHINS (PAIR)',      10, 'Shins'),
    (13, 'Sabatons',   'SOVEREIGN SABATONS',   'FEET (PAIR)',        8, 'Boots'),
    (15, 'Helmet',     'SOVEREIGN HELM',       'HEAD',              15, None),
    (20, 'Cape',       'SOVEREIGN CAPE',       'BACK',               4, None),
    # #418 shields (BPC_ShieldKit index = id - 27; ids 27-29 keep their bits clear of the set's 10-20)
    (27, 'Round Shield',  'ROUND SHIELD',           'OFF-HAND  ·  LINDEN',    0, 'RoundShield'),
    (28, 'Heater Shield', "KNIGHT'S HEATER SHIELD", 'OFF-HAND  ·  PAINTED',   0, 'HeaterShield'),
    (29, 'Gilded Shield', 'GILDED SHIELD',          'OFF-HAND  ·  GILT STEEL', 0, None),
]
# paper-doll slots round the hero: (piece id or -1 = shield), left column then right column, top to bottom
SLOTS_L = [15, 11, 16, 17, 12, -1]
SLOTS_R = [20, 10, 18, 19, 14, 13]
TIERS = [  # (pieces, text) shown in the Set Bonus box (BPC_ObsidianSet v2 tiers 2/3/5)
    (4,  '+6% Damage Reduction'),
    (6,  'Ember Shockwave on hit (40 dmg, 4 m, 12 s)'),
    (11, "Sovereign's Ember: +15% Damage Reduction"),
]
TABS = ['WEAPONS', 'ARMOUR', 'SETS', 'SUPPLIES']

L = dict(
    TW=TW, TH=TH, S=S,
    # header
    title=dict(cx=836, y=56), sub=dict(cx=836, y=93),
    portrait=dict(x=0, y=0, w=345, h=152),                    # hole in the frame: the Vesna portrait draws under it
    purse=dict(x=1288, y=38, w=367, h=44, gold=(1328, 1355), iron=(1473, 1500), silver=(1588, 1612), cy=60),
    tabbar=dict(x=240, y=124, w=1182, h=50, cy=148, lb=(316, 148), rb=(1356, 148)),
    tabs=[dict(cx=459, lx=459, x0=380, x1=540, icon=None), dict(cx=655, lx=681, x0=553, x1=755, icon=597),
          dict(cx=855, lx=877, x0=775, x1=935, icon=821), dict(cx=1060, lx=1079, x0=962, x1=1158, icon=1003)],
    # left: the set list
    left=dict(x=25, y=200, w=472, h=645),
    lhead=dict(x=40, y=212, w=440, h=46, cy=234, laurel=78, text=120, chev=448),
    rows=dict(x=45, y0=275, step=80, h=68, w=427, n=6, icon=(47, 122), name=(137, 293), deff=(137, 322), state=(457, 308)),
    rsel=dict(dx=-10, dy=-3, w=447, h=74),
    scroll=dict(x=484, y=275, w=5, h=470),
    # centre: the item
    mid=dict(x=520, y=200, w=585, h=655),
    ititle=dict(cx=813, y=230), tags=dict(y=267, slot_cx=743, piece_cx=911, h=22),
    turn=dict(cx=815, cy=430, w=420, h=280), arrows=dict(l=543, r=1080, cy=445), dots=dict(cx=819, y=563, step=19),
    cmp=dict(x=540, y=590, w=545, h=72, div=793, shield=(581, 625), plus=(616, 637), cur=(917, 637), arr=953, after=(1037, 637)),
    bonus=dict(x=540, y=668, w=545, h=122, head_y=687, count_r=1066, lines=[723, 748, 771], diamond=570, text=589),
    buy=dict(x=547, y=802, w=530, h=44, key=(655, 824), text=697, cy=824),
    # right: the hero
    right=dict(x=1128, y=200, w=520, h=648),
    rtabs=dict(y=200, h=38, eq=(1198, 1400), sp=(1400, 1640)),
    hero=dict(x=1250, y=242, w=280, h=423),
    slot=dict(lx=1207, rx=1585, cy0=274, step=72, size=58),
    stats=dict(x=1150, y=668, w=485, h=157, rows=[691, 728, 764, 800], icon=1186, label=1213, val=1376, arr=1422, after=1440),
    # bottom key hints
    foot=dict(y=870, h=71, cy=898),
)

# ---- atlas T_VT_Atlas (2048 x 2048 at 1080p scale): text cells are WHITE (tinted at draw time), sprites are in colour.
# cell = (key, w, h, kind, payload). Shelf-packed below; rects are in target px (texture px = rect * S).
GLYPHS = {15: 'helm', 16: 'rerebrace', 17: 'vambrace', 18: 'fauld', 19: 'cuisses', 20: 'cape', -1: 'shield', 29: 'shield'}
SHIELD_BLOCK = {27: 12, 28: 15, 29: 20}     # % block chance, the same numbers as BPC_ShieldKit (gen_shieldkit.py)
def cells():
    c = []
    for p in PIECES:
        i = p[0]
        c += [('name%d' % i, 200, 30, 'name', p[1]), ('def%d' % i, 110, 24, 'def', ('%d%% BLOCK' % SHIELD_BLOCK[i]) if i in SHIELD_BLOCK else '+%d DEF' % p[4]),
              ('title%d' % i, 470, 40, 'title', p[2]), ('tag%d' % i, 200, 24, 'tag', p[3])]
    for k, t in enumerate(TIERS): c.append(('tier%d' % k, 500, 24, 'tier', '(%d) %s' % t))
    for k, n in enumerate(TABS): c.append(('tab%d' % k, 202, 50, 'tab', n))
    c += [('rtab0', 202, 38, 'rtab', 'EQUIPMENT'), ('rtab1', 240, 38, 'rtab', 'SET PROGRESS'),
          ('rsel', 447, 74, 'rsel', ''), ('slotsel', 70, 70, 'slotsel', ''), ('setpiece', 108, 24, 'setpiece', 'SET PIECE'),
          ('owned', 100, 26, 'state', 'OWNED'), ('worn', 100, 26, 'state', 'WORN'), ('forging', 110, 26, 'state', 'FORGING'),
          ('btn_on', 530, 44, 'btn', 'on'), ('btn_off', 530, 44, 'btn', 'off'), ('key_e', 36, 26, 'key', 'E'),
          ('dot_on', 12, 12, 'dot', 'on'), ('dot_off', 12, 12, 'dot', 'off'), ('coin', 22, 22, 'coin', ''),
          ('nogold', 330, 26, 'msg', 'Not enough gold, hunter.'), ('forgemsg', 420, 30, 'msg2', 'IN VESNA’S FORGE — NOT YET FOR SALE'),
          ('tierrow', 470, 30, 'tierrow', '')]
    for i, g in GLYPHS.items(): c.append(('glyph%d' % i, 128, 128, 'glyph', g))
    return c

def pack(cs, W=1783, pad=18):
    out, x, y, rowh = {}, pad, pad, 0
    for k, w, h, kind, pl in cs:
        if x + w + pad > W: x, y, rowh = pad, y + rowh + pad, 0
        out[k] = dict(x=x, y=y, w=w, h=h, kind=kind, p=pl); x += w + pad; rowh = max(rowh, h)
    assert y + rowh < W, 'atlas overflow'
    return out

def write():
    L['atlas'] = pack(cells())
    L['pieces'] = [dict(id=i, name=n, title=t, tag=g, deff=d, art=a) for i, n, t, g, d, a in PIECES]
    L['slotsL'], L['slotsR'], L['tiers'], L['tabnames'] = SLOTS_L, SLOTS_R, [dict(n=n, t=t) for n, t in TIERS], TABS
    open(os.path.join(HERE, 'layout.json'), 'w').write(json.dumps(L, indent=1))
    open(os.path.join(HERE, 'layout.js'), 'w').write('window.L = ' + json.dumps(L) + ';\n')
    return L

if __name__ == '__main__':
    write(); print('layout: %d pieces, %d slots' % (len(PIECES), len(SLOTS_L) + len(SLOTS_R)))
