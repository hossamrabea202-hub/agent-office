"""pastecheck.py: for each 10-27 paste file, which pasted nodes (class+member) are missing from the LIVE graph
(export filtered by the graphs' Nodes() lists). Catches silently dropped nodes, e.g. self-calls with MemberParent=own class."""
import re, os
from collections import Counter
W = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
PAIRS = [('cmdwheel/paste_armyhud_counters.t3d', 'BP_ArmyHUD'), ('cmdwheel/paste_barracks_cmdwheel.t3d', 'BP_BarracksHUD'),
         ('cmdwheel/paste_commanderhud_cmdreq.t3d', 'BP_CommanderHUD'), ('cmdwheel/paste_soldiercommander_front.t3d', 'BP_SoldierCommander'),
         ('checkking_pastes/paste_hero_full.t3d', 'BP_ThirdPersonCharacter'), ('checkking_pastes/paste_slash_levels_2_callers_selfctx.t3d', 'BP_ThirdPersonCharacter'),
         ('checkking_pastes/paste_jellyblob_mines.t3d', 'BP_JellyBlob'), ('checkking_pastes/paste_soldierfx_levelup.t3d', 'BP_SoldierLevelUpFX'),
         ('checkking_pastes/paste_soldierwatch_levelup.t3d', 'BP_SoldierLevelWatch'), ('zombiecharge/paste_zombiecharge.t3d', 'BP_ZombieCharge'),
         ('auras/paste_heroauras.t3d', 'BP_HeroAuras'), ('auras/paste_burnaura.t3d', 'BP_BurnAura'), ('auras/paste_defenseaura_grow.t3d', 'BP_DefenseAura'),
         ('auras/paste_healaura_grow.t3d', 'BP_HealAura'), ('auras/paste_skilltree_full.t3d', 'BP_SkillTreeHUD'),
         ('jellytrail/paste_zombie_trailhook.t3d', 'BP_Zombie'), ('jellytrail/paste_cannonball_ignite.t3d', 'BP_Cannonball')]


def key(cls, b):
    m = re.search(r'(?:FunctionReference|VariableReference|EventReference|DelegateReference)=\((?:MemberParent=[^,]*,)?MemberName="([^"]+)"', b)
    cf = re.search(r'CustomFunctionName="([^"]+)"', b)
    tt = re.search(r'TargetType="?[^\']*\'([^\']+)\'', b)
    mac = re.search(r'MacroGraphReference=\(MacroGraph="[^:]*:([^"]+)"', b)
    return cls.rsplit('.', 1)[-1] + ':' + (m.group(1) if m else cf.group(1) if cf else tt.group(1).rsplit('.', 1)[-1] if tt else mac.group(1) if mac else '')


def read(p):
    raw = open(p, 'rb').read()
    return raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8', 'ignore')


for paste, bp in PAIRS:
    pp, lp = os.path.join(W, paste), os.path.join(W, 't3d', 'chk_%s.t3d' % bp)
    if not (os.path.exists(pp) and os.path.exists(lp)):
        print('SKIP', paste, bp); continue
    pt, lt = read(pp), read(lp)
    pc = Counter(key(c, b) for c, n, b in re.findall(r'Begin Object Class=(\S+) Name="([^"]+)"(.*?)\nEnd Object', pt, re.S) if 'K2Node' in c)
    live = set(re.findall(r"Nodes\(\d+\)=\"[^']*'([^']+)'\"", lt))
    cls, body = {}, {}
    for m in re.finditer(r'Begin Object (?:Class=(\S+) )?Name="([^"]+)"(.*?)\n\s*End Object', lt, re.S):
        if m.group(1): cls.setdefault(m.group(2), m.group(1))
        body[m.group(2)] = body.get(m.group(2), '') + m.group(3)
    lc = Counter(key(cls[n], body[n]) for n in live if n in cls and 'K2Node' in cls[n])
    miss = {k: pc[k] - lc[k] for k in pc if pc[k] > lc[k]}
    print('%-50s %-24s paste %4d live %4d  %s' % (paste, bp, sum(pc.values()), sum(lc.values()), ('MISSING %s' % miss) if miss else 'ok'))
