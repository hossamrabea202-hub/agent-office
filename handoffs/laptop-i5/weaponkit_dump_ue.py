# Dump BPC_WeaponKit's weapon table (CDO arrays) to handoffs/exports/adjustedfilm/shop-v2/weaponkit_table.txt. Read-only.
import unreal
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/exports/adjustedfilm/shop-v2/weaponkit_table.txt'
bp = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit')
cdo = unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(bp))
cols = {}
for n in ('Names', 'Prices', 'Damage', 'Speed', 'Meshes', 'Owned', 'Equipped', 'WeaponRot', 'KnightSwordBone'):
    try: cols[n] = cdo.get_editor_property(n)
    except Exception as e: cols[n] = 'ERR %s' % e
log = ['%s = %s' % (k, cols[k]) for k in ('Owned', 'Equipped', 'WeaponRot', 'KnightSwordBone')]
for i in range(len(cols['Names'])):
    m = cols['Meshes'][i]
    log.append('%2d  %-28s price %6s  dmg %4s  speed %5s  %s' % (i, cols['Names'][i], cols['Prices'][i], cols['Damage'][i], cols['Speed'][i],
                                                                m.get_path_name() if m else None))
open(OUT, 'w', encoding='utf-8').write('\n'.join(log))
unreal.log('i5 weaponkit dump: %d rows' % len(cols['Names']))
