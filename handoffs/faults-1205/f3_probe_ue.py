# F3 (i5): READ-ONLY. Which BPC_ObsidianSet values does the HERO actually use? Class defaults vs the hero BP's component.
import unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
N = ('AvailMask', 'BundleMask', 'BundleAvail', 'BundleOwned', 'BundleWorn', 'ObsOwned', 'ObsWorn', 'PieceId', 'TierAt')
setc = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet').generated_class()
cdo = unreal.get_default_object(setc)
def show(tag, o):
    out = []
    for n in N:
        try: v = o.get_editor_property(n); out.append('%s=%s' % (n, list(v) if hasattr(v, '__iter__') and not isinstance(v, str) else v))
        except Exception as e: out.append('%s=?' % n)
    print(tag, ' | '.join(out))
show('CLASS', cdo)
hero = unreal.load_asset('/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter')
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sub.k2_gather_subobject_data_for_blueprint(hero)
for h in handles:
    d = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
    if o and o.get_class() == setc: show('HERO ' + o.get_name(), o)
