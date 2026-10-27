"""pie_smoke.py: short Play smoke test of the 10-27 pastes. MODE file pie_smoke_mode.txt: mark | setup | probe | zombie"""
import unreal, os, re, json
from collections import Counter
D = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
OUT = os.path.join(D, 'pie_smoke_log.txt')
LOGF = r'C:\Unreal Backups\Castle Defender\Saved\Logs\CastleDefender.log'
mode = open(os.path.join(D, 'pie_smoke_mode.txt')).read().strip()
GS = unreal.GameplayStatics; KML = unreal.MaterialLibrary
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
L = ['--- %s' % mode]
unreal.SystemLibrary.execute_console_command(None, 'FlushLog')
if mode == 'mark':
    json.dump({'off': os.path.getsize(LOGF)}, open(os.path.join(D, 'pie_smoke_mark.json'), 'w'))
    L.append('marked at %d' % os.path.getsize(LOGF))
if w is None:
    L.append('NO PLAY WORLD')
else:
    hero = GS.get_player_character(w, 0)
    if mode == 'setup':
        GS.set_game_paused(w, False)
        H = unreal.load_asset('/Game/CastleDefender/Gameplay/Skills/MPC_HeroAbilities')
        S = unreal.load_asset('/Game/CastleDefender/UI/SkillTree/MPC_SkillTree')
        KML.set_scalar_parameter_value(w, S, 'BookAge', 10.0)
        for n in ('AuraDef', 'AuraHeal', 'AuraBurn'): KML.set_scalar_parameter_value(w, H, n, 2.0)
        L.append('unpaused, BookAge 10, aura ranks 2')
    if mode == 'zombie' and hero:
        zc = unreal.load_class(None, '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie.BP_Zombie_C')
        hl = hero.get_actor_location(); fw = hero.get_actor_forward_vector(); n = 0
        for z in sorted(GS.get_all_actors_of_class(w, zc), key=lambda z: (z.get_actor_location() - hl).length())[:4]:
            z.set_actor_location(hl + fw * (700.0 + 150 * n) + unreal.Vector(0, 120 * n, 0), False, True); n += 1
        L.append('moved %d zombies 7-11 m in front of the hero' % n)
    acts = GS.get_all_actors_of_class(w, unreal.Actor)
    c = Counter(a.get_class().get_name() for a in acts)
    keys = ('BP_Zombie_C', 'BP_JellyBlob_C', 'BP_JellyTrailManager_C', 'BP_ZombieCharge_C', 'BP_SoldierSword_C', 'BP_SoldierXbow_C', 'BP_SoldierCommander_C',
            'BP_DefenseAura_C', 'BP_HealAura_C', 'BP_BurnAura_C', 'BP_SoldierLevelUpFX_C', 'BP_Cannonball_C', 'BP_CrossbowBolt_C', 'BP_JellyMine_C')
    L.append('t=%.1f paused=%s hero=%s | %s' % (GS.get_time_seconds(w), GS.is_game_paused(w), hero.get_name() if hero else None, ' '.join('%s=%d' % (k[:-2], c[k]) for k in keys if c[k])))
    L.append('other new-ish classes: %s' % [k for k in c if any(s in k for s in ('Jelly', 'Mine', 'Charge', 'Aura', 'Level', 'Slash', 'Bolt', 'Fire', 'Slime'))])
    for a in acts:
        n = a.get_class().get_name()
        if n == 'BP_JellyTrailManager_C':
            for p in ('Active', 'Flames'):
                try: L.append('  trail %s len %d' % (p, len(a.get_editor_property(p))))
                except Exception as e: L.append('  trail %s ? %s' % (p, str(e)[:50]))
        if n == 'BP_ZombieCharge_C':
            for p in ('ChargeZ', 'CoolZ'):
                try: v = a.get_editor_property(p); L.append('  charge %s %s' % (p, v.get_name() if hasattr(v, 'get_name') else v))
                except Exception as e: L.append('  charge %s ? %s' % (p, str(e)[:50]))
# runtime errors since mark
try:
    off = json.load(open(os.path.join(D, 'pie_smoke_mark.json')))['off']
    f = open(LOGF, 'rb'); f.seek(off); new = f.read().decode('utf-8', 'ignore'); f.close()
    errs = Counter()
    for m in re.finditer(r'Blueprint Runtime Error: "([^"]*)"\.\s+Node:\s+(.*?)\s+Graph:\s+(\S+).*?Blueprint:\s+(\S+)', new):
        errs['%s | %s | %s' % (m.group(4), m.group(2), m.group(1)[:70])] += 1
    L.append('runtime errors since mark: %d' % sum(errs.values()))
    for k, v in errs.most_common(15): L.append('  %4d %s' % (v, k))
    other = Counter(re.sub(r'\[.*?\]', '', s)[:120] for s in new.splitlines() if ('Error' in s or 'Warning: Script' in s) and 'Blueprint Runtime Error' not in s)
    for k, v in other.most_common(6): L.append('  other %3d %s' % (v, k))
except Exception as e:
    L.append('no mark: %s' % e)
open(OUT, 'a').write('\n'.join(L) + '\n')
