# The Muster (#359): the barracks screen in the same kit as Vesna's Trade (#361). Same panel geometry (layout.py),
# different content.   python layout_mu.py -> layout_mu.js (muster.html / atlas_mu.html) + layout_mu.json (gen_muster.py)
import json, os
from layout import L as LT, TW, TH, S, pack
HERE = os.path.dirname(os.path.abspath(__file__))

TABS = ['RECRUIT', 'ARTILLERY', 'FORTIFY', 'SUPPLIES']
# items: key, tab, row name, title, tag, glyph, description (2 lines), kind
#   kind: rec0/rec1/rec2 = BP_BarracksHUD Enqueue(Kind) after paying (sword / crossbow / commander), medic = BPC_Medics.HudBuy,
#         mech = locked (#50 spec only), cannon = BP_CannonOrder.HudOrder, walls / towers = BPC_CastleUpgrades.HudBuyWalls/Towers,
#         gate = info (the Forge, #208), flares = BPC_Flares.HudBuy
ITEMS = [
    ('sword',  0, 'Swordsman',      'SWORDSMAN',          'FRONTLINE',      'sword',   ('Short sword and shield. Holds the gate', 'and cuts down anything that comes close.'), 'rec0'),
    ('xbow',   0, 'Crossbowman',    'CROSSBOWMAN',        'RANGED',         'xbow',    ('Mans the walls and shoots far into the', 'field before the horde reaches the gate.'), 'rec1'),
    ('cmdr',   0, 'Commander',      'COMMANDER',          'LEADER  (ONE)',  'banner',  ('Leads a squad into battle and heals every', 'soldier fighting near him.'), 'rec2'),
    ('medic',  0, 'Medic',          'MEDIC',              'SUPPORT  (FOUR)', 'medic',  ('Heals your soldiers and you, 8 HP a second.', 'Never fights: runs to you when zombies come.'), 'medic'),
    ('mech',   0, 'Mechanic',       'MECHANIC',           'WORKSHOP',       'gear',    ('Repairs the gate and the cannons.', 'Training starts when the workshop is built.'), 'mech'),
    ('cannon', 1, 'Cannon',         'FIELD CANNON',       'WALL PAD',       'cannon',  ('A cart convoy brings it to a free wall pad.', 'Zombies will hunt the cart on the way.'), 'cannon'),
    ('walls',  2, 'Walls',          'CASTLE WALLS',       'TWO LEVELS',     'wall',    ('A colossus needs x1.75 the smashes to breach', 'a wall (level 2: x2.5).'), 'walls'),
    ('towers', 2, 'Towers',         'BALLISTA TOWERS',    'TWO LEVELS',     'tower',   ('Tower ballistas shoot the nearest zombie,', 'a colossus first (level 2: fire ballistas).'), 'towers'),
    ('gate',   2, 'Gate',           'GATE BANDS',         'AT THE FORGE',   'gate',    ('Iron bands for the gate are forged by the', 'smith: up to +150% gate life.'), 'gate'),
    ('flares', 3, 'Crossbow flares', 'CROSSBOW FLARES',   'ONE-TIME',       'flare',   ('At night your crossbowmen light up the', 'threats they spot. 26 s magnesium flares.'), 'flares'),
]
# walls / towers costs per level (handoffs/castle-upgrades-224): (gold, {ore index: amount}); Ore[0] iron, [1] copper, [2] silver, [3] gold ore
WALLS = [(300, {0: 6}), (700, {0: 8, 2: 3})]
TOWERS = [(400, {0: 6, 1: 2}), (900, {0: 6, 3: 2})]
ORES = ['Iron', 'Copper', 'Silver', 'Gold ore']

L = dict(LT)
L.update(dict(
    TW=TW, TH=TH, S=S, tabnames=TABS, walls=WALLS, towers=TOWERS, ores=ORES,
    tabs=[dict(cx=459, lx=470, x0=380, x1=560, icon=None), dict(cx=665, lx=693, x0=565, x1=775, icon=603),
          dict(cx=870, lx=893, x0=780, x1=962, icon=826), dict(cx=1060, lx=1085, x0=966, x1=1158, icon=1004)],
    # centre: the preview box holds the item's big glyph; cost / you-have box; what-it-does box
    cost=dict(x=540, y=590, w=545, h=72, div=793),
    # right panel: GARRISON (army) / CASTLE (works) tabs
    rtabs=dict(y=200, h=38, eq=(1198, 1400), sp=(1400, 1640)),
    garrison=dict(x=1160, y0=262, step=44, label=1214, val=1600, icon=1186),
    queue=dict(y=560, x0=1214, step=128, w=112, h=70),
    treasury=dict(rows=[691, 728, 764, 800]),
))

def cells():
    c = []
    for k, tab, name, title, tag, glyph, desc, kind in ITEMS:
        c += [('name_' + k, 220, 30, 'name', name), ('title_' + k, 470, 40, 'title', title), ('tag_' + k, 200, 24, 'tag', tag),
              ('d1_' + k, 500, 24, 'desc', desc[0]), ('d2_' + k, 500, 24, 'desc', desc[1])]
    for k, n in enumerate(TABS): c.append(('tab%d' % k, 202, 50, 'tab', n))
    c += [('rtab0', 202, 38, 'rtab', 'GARRISON'), ('rtab1', 240, 38, 'rtab', 'CASTLE'),
          ('rsel', 447, 74, 'rsel', ''), ('setpiece', 108, 24, 'setpiece', 'BARRACKS'),
          ('owned', 100, 26, 'state', 'OWNED'), ('maxed', 120, 26, 'state', 'AT BEST'), ('locked', 110, 26, 'state', 'LOCKED'),
          ('btn_on', 530, 44, 'btn', 'on'), ('btn_off', 530, 44, 'btn', 'off'), ('key_e', 36, 26, 'key', 'E'),
          ('pip_on', 16, 16, 'pip', 'on'), ('pip_off', 16, 16, 'pip', 'off'), ('coin', 22, 22, 'coin', ''),
          ('qslot', 112, 70, 'qslot', ''), ('nogold', 360, 26, 'msg', 'Not enough, captain.')]
    for g in sorted({i[5] for i in ITEMS}): c.append(('glyph_' + g, 128, 128, 'glyph', g))
    return c

def write():
    L['atlas'] = pack(cells())
    L['items'] = [dict(key=k, tab=t, name=n, title=ti, tag=tg, glyph=g, desc=list(d), kind=kd) for k, t, n, ti, tg, g, d, kd in ITEMS]
    open(os.path.join(HERE, 'layout_mu.json'), 'w').write(json.dumps(L, indent=1))
    open(os.path.join(HERE, 'layout_mu.js'), 'w').write('window.L = ' + json.dumps(L) + ';\n')
    return L

if __name__ == '__main__':
    write(); print('muster layout: %d items, %d atlas cells' % (len(ITEMS), len(L['atlas'])))
