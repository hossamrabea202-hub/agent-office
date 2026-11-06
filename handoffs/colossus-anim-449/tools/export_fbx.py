# Scratch lab only: export SK_Zombie and chosen zombie clips to FBX for Blender. env Z_CLIPS (comma, relative to Zombie/), Z_OUT, Z_MESH
import unreal, os
OUT = os.environ.get('Z_OUT', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fbx_before')); os.makedirs(OUT, exist_ok=True)
R = '/Game/CastleDefender/Characters/Enemies/Zombie/'
clips = os.environ.get('Z_CLIPS', 'Anims/A_Walk,Anims/A_Run,Anims/A_Attack,Anims/A_Hit,Anims/A_Death,AnimsPack/ZA_Idle_A,AnimsPack/ZA_Walk_A,AnimsPack/ZA_Run_A,AnimsPack/ZA_Attack_D,AnimsPack/ZA_Taking_Damage_A,AnimsPack/ZA_Taking_Damage_B').split(',')
def export(obj, fn, mesh):
    t = unreal.AssetExportTask(); t.object = obj; t.filename = fn; t.automated = True; t.prompt = False; t.replace_identical = True
    o = unreal.FbxExportOption()
    for k, v in [('export_preview_mesh', mesh), ('collision', False), ('level_of_detail', False), ('export_morph_targets', False)]:
        try: o.set_editor_property(k, v)
        except Exception as e: print('opt', k, e)
    t.options = o; ok = unreal.Exporter.run_asset_export_task(t); print('EXPORT', ok, fn, [str(e) for e in t.errors])
if os.environ.get('Z_MESH', '0') == '1': export(unreal.load_asset(R + 'SK_Zombie'), os.path.join(OUT, 'SK_Zombie.fbx'), False)
for c in clips:
    s = unreal.load_asset(R + c.strip())
    if s: export(s, os.path.join(OUT, c.strip().split('/')[-1] + '.fbx'), False)
    else: print('MISSING', c)
print('EXPORT OK')
