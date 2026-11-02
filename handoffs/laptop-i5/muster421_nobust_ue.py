# i5 #421: the editor bust captures came out white on i5; clear BustTex so every card shows its medallion
# (TGA's fallback) until TGA tunes the capture. The T_MU_Bust_* assets stay (unused).
import unreal
p = '/Game/CastleDefender/Gameplay/Castle/BPC_Muster'
bp = unreal.load_asset(p); cdo = unreal.get_default_object(bp.generated_class())
n = len(cdo.get_editor_property('BustTex')); cdo.set_editor_property('BustTex', [None] * n)
print('BustTex cleared:', n, 'entries; saved', unreal.EditorAssetLibrary.save_asset(p))
