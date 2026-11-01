# The Muster v2 (#420): owner rejected v1 in Play (21:01, "barely things click ... better layout, easier menus, better icons
# for soldiers commanders etc like before"). One screen, no side panels: big tabs, one row of big cards (portrait + name +
# cost + its own button), a garrison strip, key hints. Every card, tab and button is a click target with hover / press art.
#   python layout_mu2.py -> layout_mu2.js (muster2.html) + layout_mu2.json (gen_muster2.py). Coordinates in 1672x941 target px.
import json, os
from layout import TW, TH, S, pack
from layout_mu import ITEMS, WALLS, TOWERS, ORES
ITEMS = [(i[:4] + ('LEADER  (TWO)',) + i[5:]) if i[0] == 'cmdr' else i for i in ITEMS]   # owner 21:02: two commanders per army
HERE = os.path.dirname(os.path.abspath(__file__))

TABS = ['RECRUIT', 'ARTILLERY', 'FORTIFY', 'SUPPLIES']
TABICON = ['helm', 'cannon', 'tower', 'flask']
BUSTS = {'sword': 'BP_SoldierSword', 'xbow': 'BP_SoldierXbow', 'cmdr': 'BP_SoldierCommander', 'medic': 'BP_Medic'}
VERB = {'rec0': 'RECRUIT', 'rec1': 'RECRUIT', 'rec2': 'RECRUIT', 'medic': 'HIRE', 'mech': 'TRAIN', 'cannon': 'ORDER',
        'walls': 'BUILD', 'towers': 'BUILD', 'gate': 'FORGE', 'flares': 'BUY'}

CW, CH, CG = 290, 548, 16                  # card size and gap
CY = 196
def card_x0(n): return round(TW / 2 - (n * CW + (n - 1) * CG) / 2)
TABW, TABG, TABY, TABH = 300, 12, 116, 58
TABX0 = round(TW / 2 - (4 * TABW + 3 * TABG) / 2)

L = dict(
    TW=TW, TH=TH, S=S, tabnames=TABS, walls=WALLS, towers=TOWERS, ores=ORES,
    tabs=[dict(x=TABX0 + i * (TABW + TABG), y=TABY, w=TABW, h=TABH) for i in range(4)],
    card=dict(y=CY, w=CW, h=CH, step=CW + CG,
              por=dict(dx=12, dy=12, w=CW - 24, h=262),            # portrait window
              name=290, tag=318, rule=336, d1=360, d2=382, sub=414, cost=446,
              btn=dict(dx=14, dy=478, w=CW - 28, h=54)),
    close=dict(x=26, y=30, w=150, h=50),
    purse=dict(x=1300, y=30, w=346, h=50),
    strip=dict(x=card_x0(5), y=CY + CH + 24, w=5 * CW + 4 * CG, h=74),
    hints_y=98,                         # header: the bottom strip of the screen is the hero's ability icons
    hover_pad=6,
)
st = L['strip']
L['strip'].update(cols=[st['x'] + 50, st['x'] + 262, st['x'] + 502, st['x'] + 782, st['x'] + 992], qx0=st['x'] + 1190, qstep=96, qw=84, qh=56)

def cells():
    c = []
    for k, tab, name, title, tag, glyph, desc, kind in ITEMS:
        c += [('name_' + k, CW - 20, 34, 'name', title), ('tag_' + k, CW - 20, 22, 'tag', tag),
              ('d1_' + k, CW - 24, 22, 'desc', desc[0]), ('d2_' + k, CW - 24, 22, 'desc', desc[1])]
    c += [('card_bg', CW, CH, 'card', 'bg'), ('card_hover', CW + 12, CH + 12, 'card', 'hover'), ('card_sel', CW + 12, CH + 12, 'card', 'sel'),
          ('vignette', CW - 24, 262, 'vignette', ''),
          ('btn_on', CW - 28, 54, 'btn', 'on'), ('btn_hover', CW - 28, 54, 'btn', 'hover'), ('btn_press', CW - 28, 54, 'btn', 'press'), ('btn_off', CW - 28, 54, 'btn', 'off'),
          ('tab_on', TABW, TABH, 'tab', 'on'), ('tab_hover', TABW, TABH, 'tab', 'hover'),
          ('close_hover', 150, 50, 'close', 'hover'), ('coin', 22, 22, 'coin', ''),
          ('qslot', 84, 56, 'qslot', ''), ('pip_on', 16, 16, 'pip', 'on'), ('pip_off', 16, 16, 'pip', 'off')]
    for g in sorted({i[5] for i in ITEMS}):
        c.append(('med_' + g, 200, 200, 'medal', g))     # big medallion for items without a bust (and the bust fallback)
        c.append(('mini_' + g, 40, 40, 'mini', g))       # garrison strip / queue
    return c

def write():
    L['atlas'] = pack(sorted(cells(), key=lambda q: -q[2]))      # tallest first: the shelf packer wastes less
    L['items'] = [dict(key=k, tab=t, name=n, title=ti, tag=tg, glyph=g, desc=list(d), kind=kd, verb=VERB[kd], bust=BUSTS.get(k, ''))
                  for k, t, n, ti, tg, g, d, kd in ITEMS]
    L['tabicons'] = TABICON
    open(os.path.join(HERE, 'layout_mu2.json'), 'w').write(json.dumps(L, indent=1))
    open(os.path.join(HERE, 'layout_mu2.js'), 'w').write('window.L = ' + json.dumps(L) + ';\n')
    return L

if __name__ == '__main__':
    write(); print('muster v2 layout: %d items, %d atlas cells, cards x0(5)=%d' % (len(ITEMS), len(L['atlas']), card_x0(5)))
