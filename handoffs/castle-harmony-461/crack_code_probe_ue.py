# #470 (i5): READ-ONLY. Find the Custom (HLSL) nodes and crack parameter nodes in the stone base materials.
import unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
MATS = ['/Game/CastleDefender/Environment/Castle/KeepEntrance/M_KeepEntrance_Baked', '/Game/CastleDefender/Shared/Materials/Castle/M_Castle_StoneWall_World',
        '/Game/CastleDefender/Environment/Castle/KeepMasonry/M_CastleAshlarWeathered2', '/Game/CastleDefender/Environment/Castle/StairsBaked/M_Castle_StairBaked']
for p in MATS:
    m = unreal.load_asset(p)
    if not m: print('MISSING', p); continue
    mp = m.get_path_name()
    exprs = [x for cls in (unreal.MaterialExpressionCustom, unreal.MaterialExpressionScalarParameter, unreal.MaterialExpressionTextureObjectParameter,
                           unreal.MaterialExpressionTextureSampleParameter2D, unreal.MaterialExpressionVectorParameter)
             for x in unreal.ObjectIterator(cls) if x.get_path_name().startswith(mp + ':') or x.get_path_name().startswith(mp + '.')]
    print('==', p.split('/')[-1], len(exprs), 'expressions')
    for x in exprs:
        cls = x.get_class().get_name()
        if cls == 'MaterialExpressionCustom':
            code = x.get_editor_property('code'); ins = [str(i.get_editor_property('input_name')) for i in x.get_editor_property('inputs')]
            lines = [l.strip() for l in code.split('\n') if 'rack' in l or 'c*=1.0-k' in l or 'float k=' in l]
            print('  CUSTOM', x.get_name(), 'inputs', ins); [print('     |', l[:150]) for l in lines]
        elif 'Parameter' in cls:
            n = str(x.get_editor_property('parameter_name'))
            if 'rack' in n: print('  PARAM', cls, n)
