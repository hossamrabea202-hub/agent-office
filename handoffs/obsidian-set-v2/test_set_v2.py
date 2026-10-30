# Obsidian set v2 test (checkking, 2026-10-30): run while Play is running (the hero needs his anim, so not Simulate).
# One step per run, chosen by STEP. Each prints the component state and the MPC vectors to the Output Log.
#   state  just print
#   give   DebugGiveAll: every piece with art goes on (expect the meshes on the hero, Tier from the worn count)
#   none   take everything off (LoadState 0): pieces hidden, knight slots back, Tier 0, ObsSet.R 0
#   buy    LoadState 0, then BuyPiece on 11..20: pieces without art are refused (Owned unchanged), the rest go on,
#          NextPrice climbs 450 -> 650 -> 950 ...
#   off13  ToggleWear(13) twice: boots off, then on again
import unreal
STEP = 'give'

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = ues.get_game_world()
if not w: raise RuntimeError('start Play first')
hero = unreal.GameplayStatics.get_player_character(w, 0)
comp = [c for c in hero.get_components_by_class(unreal.ActorComponent) if 'ObsidianSet' in c.get_name()][0]
mpc = unreal.load_asset('/Game/CastleDefender/UI/SkillTree/MPC_SkillTree')

def show(tag):
    v = {n: comp.get_editor_property(n) for n in ('AvailMask', 'ObsOwned', 'ObsWorn', 'WornEff', 'WornCount', 'Tier', 'ObsBought', 'NextPrice')}
    o = unreal.KismetMaterialLibrary.get_vector_parameter_value(w, mpc, 'ObsSet')
    vis = [(c.get_name(), c.is_visible()) for c in comp.get_editor_property('PieceComps') if c]
    unreal.log('set v2 %s %s ObsSet=(%.2f, %.1f, %.1f, %.0f) damage x%.3f pieces %s' % (tag, v, o.r, o.g, o.b, o.a, 1 - o.r * 0.15, vis))

if STEP == 'state':
    show('state')
elif STEP == 'give':
    comp.call_method('DebugGiveAll'); show('give')
elif STEP == 'none':
    comp.call_method('LoadState', args=(0, 0, 0, comp.get_editor_property('ShieldLevel'))); show('none')
elif STEP == 'buy':
    comp.call_method('LoadState', args=(0, 0, 0, 0))
    for i in range(11, 21):
        comp.call_method('BuyPiece', args=(i,)); show('buy %d' % i)
elif STEP == 'off13':
    comp.call_method('ToggleWear', args=(13,)); show('boots off')
    comp.call_method('ToggleWear', args=(13,)); show('boots on')
