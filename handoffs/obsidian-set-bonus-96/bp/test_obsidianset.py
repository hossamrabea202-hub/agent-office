# #96 test (laptop2, 2026-10-29): run while Play/Simulate is running. Drives the hero's ObsidianSet component and prints
# the variables and the MPC vectors. One step per run, chosen by STEP:
#   prices  buy 11 pieces one by one, print NextPrice after each (expect 650 950 1350 ... 18500, then 0)
#   full    LoadState(2047, 2047, 11, 4): set complete without the burst (ObsSet.R 1, G unchanged)
#   off     take piece 15 off: ObsSet.R 0, WornCount 10;  on: put it back: R 1 and G = now (burst plays)
#   hit     fire the shockwave by hand (OnOwnerHit): ObsSet.B = now, ShockReadyAt = now + 12
#   shield  BuyShield x5: ShieldLevel 1..4 (stays 4), NextShieldPrice 800 1400 2400 0 0
import unreal
STEP = 'prices'

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = ues.get_game_world()
if not w: raise RuntimeError('start Play or Simulate first')
hero = unreal.GameplayStatics.get_player_character(w, 0)
comp = [c for c in hero.get_components_by_class(unreal.ActorComponent) if 'ObsidianSet' in c.get_name()][0]
mpc = unreal.load_asset('/Game/CastleDefender/UI/SkillTree/MPC_SkillTree')
now = lambda: unreal.GameplayStatics.get_time_seconds(w)

def show(tag):
    v = {n: comp.get_editor_property(n) for n in ('ObsOwned', 'ObsWorn', 'ObsBought', 'WornCount', 'NextPrice', 'ShieldLevel', 'NextShieldPrice', 'WasComplete')}
    o = unreal.KismetMaterialLibrary.get_vector_parameter_value(w, mpc, 'ObsSet')
    s = unreal.KismetMaterialLibrary.get_vector_parameter_value(w, mpc, 'Shield')
    unreal.log('#96 %s t=%.1f %s ObsSet=(%.0f, %.1f, %.1f, %.0f) Shield=(%.0f, %.1f)' % (tag, now(), v, o.r, o.g, o.b, o.a, s.r, s.g))

if STEP == 'prices':
    comp.call_method('LoadState', args=(0, 0, 0, 0))
    for i in range(11):
        comp.call_method('BuyPiece', args=(10 + i,)); show('bought %d' % (10 + i))
elif STEP == 'full':
    comp.call_method('LoadState', args=(2047, 2047, 11, 4)); show('full')
elif STEP in ('off', 'on'):
    comp.call_method('SetPieceWorn', args=(15, STEP == 'on')); show(STEP)
elif STEP == 'hit':
    comp.call_method('OnOwnerHit', args=(hero, 10.0, None, None, None)); show('hit')
elif STEP == 'shield':
    comp.call_method('LoadState', args=(0, 0, 0, 0))
    for i in range(5):
        comp.call_method('BuyShield'); show('shield buy %d' % (i + 1))
