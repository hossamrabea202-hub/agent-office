# F11 step 1 (Master): add member variable RQ3 (int array) to BPC_Muster, needed by the F11 paste. Safe to re-run.
import unreal
BEL = unreal.BlueprintEditorLibrary
bp = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BPC_Muster')
cdo = unreal.get_default_object(bp.generated_class())
try:
    cdo.get_editor_property('RQ3'); print('RQ3 already there')
except Exception:
    print('add RQ3', BEL.add_member_variable(bp, 'RQ3', BEL.get_array_type(BEL.get_basic_type_by_name('int'))))
    BEL.compile_blueprint(bp)
