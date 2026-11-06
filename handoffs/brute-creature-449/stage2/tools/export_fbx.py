# Scratch lab only: export SK_FleshBrute and chosen clips to FBX for Blender previews.
# Clip list from env FB_CLIPS (comma separated, asset paths relative to FleshBrute/), default = the originals.
import unreal, os
OUT = os.environ.get('FB_OUT', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fbx'))
os.makedirs(OUT, exist_ok=True)
R = '/Game/CastleDefender/Characters/Enemies/FleshBrute/'
clips = os.environ.get('FB_CLIPS', 'Anims/FB_A_Walk,Anims/FB_A_Run,Anims/FB_ZA_Idle_A,Anims/FB_A_Attack,Anims/FB_ZA_Attack_D,Anims/FB_A_Hit,Anims/FB_A_Death').split(',')
def export(obj, fn, mesh):
    t = unreal.AssetExportTask()
    t.object = obj; t.filename = fn; t.automated = True; t.prompt = False; t.replace_identical = True
    o = unreal.FbxExportOption()
    for k, v in [('export_preview_mesh', mesh), ('collision', False), ('level_of_detail', False), ('export_morph_targets', False)]:
        try: o.set_editor_property(k, v)
        except Exception as e: print('opt', k, e)
    t.options = o
    ok = unreal.Exporter.run_asset_export_task(t)
    print('EXPORT', ok, fn, [str(e) for e in t.errors])
if os.environ.get('FB_MESH', '1') == '1':
    export(unreal.load_asset(R + 'SK_FleshBrute'), os.path.join(OUT, 'SK_FleshBrute.fbx'), False)
for c in clips:
    s = unreal.load_asset(R + c.strip())
    export(s, os.path.join(OUT, c.strip().split('/')[-1] + '.fbx'), False)
print('EXPORT OK')
