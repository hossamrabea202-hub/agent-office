# #410 lookdev: preview MIs (new assets only) of the walk flagstone and the courtyard paving on the wet copies,
# WetPreview 0 (dry) and 1 (soaked), in /Game/CastleDefender/Dev/Wet410. Opens the soaked one in the editor.
#   py "<repo>/handoffs/rain-wet-410/preview410_ue.py"
import unreal
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
DST = '/Game/CastleDefender/Dev/Wet410'
C = '/Game/CastleDefender/Shared/Materials/Castle/'
SETS = [('WalkFlag', C + 'MI_Castle_WalkFlag_World', C + 'M_Castle_StoneWall_World_Wet410'),
        ('Paving', C + 'MI_Castle_Paving_POM', C + 'M_Castle_Paving_POM_Wet410')]
made = []
for tag, src, wet_parent in SETS:
    for state, v in (('Dry', 0.0), ('Soaked', 1.0)):
        p = '%s/MI_Wet410_%s_%s' % (DST, tag, state)
        if EAL.does_asset_exist(p): EAL.delete_asset(p)
        mi = EAL.duplicate_asset(src, p)
        MEL.set_material_instance_parent(mi, unreal.load_asset(wet_parent))
        MEL.set_material_instance_scalar_parameter_value(mi, 'WetPreview', v)
        EAL.save_asset(p); made.append(p)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([unreal.load_asset(made[0])])
unreal.log('I5CHK 410 preview: ' + ', '.join(m.split('/')[-1] for m in made))
