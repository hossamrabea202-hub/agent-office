# Vesna's Trade, #424 BUNDLES variant of layout.py (i9 helper, 2026-11-02).
#   python layout_bd.py  ->  layout_bd.js (chrome.html / atlas.html with ?L=bd) + layout_bd.json (gen_trade_bd.py)
# Same screen as layout.py. Only these change:
#   - the ARMOUR list is 4 Obsidian bundles (row ids 0..3 = BPC_ObsidianSet bundle index) + the 3 #418 shields (27..29)
#   - the EQUIPMENT doll has the inventory's 6 slots: left Head / Torso / Hands, right Weapon / Shield / Boots(Legs)
#   - set tiers count bundles worn (1/2/3/4), so the Set Bonus lines say (2) (3) (4)
#   - new atlas glyphs: helm/torso/hands/legs/sword/shield outlines for empty doll slots ('out0'..'out5')
import copy, json, os
import layout as base

HERE = os.path.dirname(os.path.abspath(__file__))
L = copy.deepcopy(base.L)

# id, row name, title, tag, DEF (sum of the parts' DEF in obsidian-set-v2/pieces.csv), art (bundle icon / turntable) or None
ROWS = [
    (0, 'Obsidian Helm',      'OBSIDIAN HELM',      'HEAD  ·  HELMET',                 15, None),
    (1, 'Obsidian Torso',     'OBSIDIAN TORSO',     'TORSO  ·  4 PIECES',              69, 'Torso'),
    (2, 'Obsidian Gauntlets', 'OBSIDIAN GAUNTLETS', 'HANDS  ·  2 PIECES',              16, 'Gauntlets'),
    (3, 'Obsidian Legs',      'OBSIDIAN LEGS',      'LEGS  ·  4 PIECES',               40, 'Legs'),
    (27, 'Round Shield',  'ROUND SHIELD',           'OFF-HAND  ·  LINDEN',    0, 'RoundShield'),
    (28, 'Heater Shield', "KNIGHT'S HEATER SHIELD", 'OFF-HAND  ·  PAINTED',   0, 'HeaterShield'),
    (29, 'Gilded Shield', 'GILDED SHIELD',          'OFF-HAND  ·  GILT STEEL', 0, None),
]
# what each bundle row contains (shown under the title as the piece list)
CONTENTS = {0: 'Helmet', 1: 'Cuirass · Pauldrons · Rerebraces · Cape', 2: 'Gauntlets · Vambraces',
            3: 'Fauld · Cuisses · Greaves · Sabatons'}
# doll slots, the inventory panel's order: bundle index 0..3, -1 = shield, -2 = weapon
SLOTS_L = [0, 1, 2]          # Head, Torso, Hands
SLOTS_R = [-2, -1, 3]        # Weapon, Shield, Boots (Obsidian Legs)
OUTLINE = {0: 'helm', 1: 'cuirass', 2: 'gauntlet', -2: 'sword', -1: 'shield', 3: 'legs'}
TIERS = [  # (bundles worn, text): BPC_ObsidianSet v3 tiers 2 / 3 / 4
    (2, '+6% Damage Reduction'),
    (3, 'Ember Shockwave on hit (40 dmg, 4 m, 12 s)'),
    (4, "Sovereign's Ember: +15% Damage Reduction"),
]
L['slot'] = dict(lx=1207, rx=1585, cy0=310, step=144, size=58)     # 3 per side, centred in the old 6-row column


def cells():
    c = []
    for i, n, t, g, d, a in ROWS:
        c += [('name%d' % i, 200, 30, 'name', n),
              ('def%d' % i, 110, 24, 'def', ('%d%% BLOCK' % base.SHIELD_BLOCK[i]) if i in base.SHIELD_BLOCK else '+%d DEF' % d),
              ('title%d' % i, 470, 40, 'title', t), ('tag%d' % i, 240, 24, 'tag', g)]
    for i, s in CONTENTS.items(): c.append(('desc%d' % i, 470, 24, 'desc', s))
    for k, (n, t) in enumerate(TIERS): c.append(('tier%d' % k, 500, 24, 'tier', '(%d) %s' % (n, t)))
    for k, n in enumerate(base.TABS): c.append(('tab%d' % k, 202, 50, 'tab', n))
    c += [('rtab0', 202, 38, 'rtab', 'EQUIPMENT'), ('rtab1', 240, 38, 'rtab', 'SET PROGRESS'),
          ('rsel', 447, 74, 'rsel', ''), ('slotsel', 70, 70, 'slotsel', ''), ('setpiece', 120, 24, 'setpiece', 'SET BUNDLE'),
          ('owned', 100, 26, 'state', 'OWNED'), ('worn', 100, 26, 'state', 'WORN'), ('forging', 110, 26, 'state', 'FORGING'),
          ('btn_on', 530, 44, 'btn', 'on'), ('btn_off', 530, 44, 'btn', 'off'), ('key_e', 36, 26, 'key', 'E'),
          ('dot_on', 12, 12, 'dot', 'on'), ('dot_off', 12, 12, 'dot', 'off'), ('coin', 22, 22, 'coin', ''),
          ('nogold', 330, 26, 'msg', 'Not enough gold, hunter.'), ('forgemsg', 420, 30, 'msg2', 'IN VESNA’S FORGE — NOT YET FOR SALE'),
          ('tierrow', 470, 30, 'tierrow', '')]
    for i, gname in {0: 'helm', -1: 'shield', 29: 'shield'}.items(): c.append(('glyph%d' % i, 128, 128, 'glyph', gname))
    for k, sid in enumerate(SLOTS_L + SLOTS_R): c.append(('out%d' % k, 128, 128, 'glyph', OUTLINE[sid]))
    return c


def write():
    L['atlas'] = base.pack(cells())
    L['pieces'] = [dict(id=i, name=n, title=t, tag=g, deff=d, art=a) for i, n, t, g, d, a in ROWS]
    L['slotsL'], L['slotsR'], L['tiers'], L['tabnames'] = SLOTS_L, SLOTS_R, [dict(n=n, t=t) for n, t in TIERS], base.TABS
    L['contents'] = CONTENTS
    open(os.path.join(HERE, 'layout_bd.json'), 'w').write(json.dumps(L, indent=1))
    open(os.path.join(HERE, 'layout_bd.js'), 'w').write('window.L = ' + json.dumps(L) + ';\n')
    return L


if __name__ == '__main__':
    write(); print('layout_bd: %d rows, %d slots, %d atlas cells' % (len(ROWS), len(SLOTS_L) + len(SLOTS_R), len(L['atlas'])))
