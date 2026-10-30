# Imports the realm dome mesh:  py "<repo>/assets/laptop2/RealmKit/import_realm_ue.py"
# -> /Game/CastleDefender/Realm/SM_RealmDome (unit half-ellipsoid: radius 1 m, height 1 m; place_realm_ue.py scales it to the
#    realm box). No collision, no shadow. Then run handoffs/realm-169/make_realm_bubble.py for its material.
import os, unreal
SRC = os.path.dirname(os.path.abspath(__file__)); DST = '/Game/CastleDefender/Realm'
EAL, tools = unreal.EditorAssetLibrary, unreal.AssetToolsHelpers.get_asset_tools()
if not EAL.does_directory_exist(DST): EAL.make_directory(DST)
t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, 'SM_RealmDome.fbx'); t.destination_path = DST; t.automated = True; t.replace_existing = True; t.save = True
o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
o.static_mesh_import_data.set_editor_property('combine_meshes', True); o.static_mesh_import_data.set_editor_property('generate_lightmap_u_vs', False)
o.static_mesh_import_data.set_editor_property('auto_generate_collision', False)
t.options = o; tools.import_asset_tasks([t])
sm = unreal.load_asset(DST + '/SM_RealmDome')
if sm:
    bs = sm.get_editor_property('body_setup')
    if bs: bs.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    EAL.save_asset(sm.get_path_name()); unreal.log('SM_RealmDome imported to ' + DST)
