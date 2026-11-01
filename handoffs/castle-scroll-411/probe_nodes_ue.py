# Read-only: which pasted #411 nodes exist in BPC_CastleScroll's EventGraph (and duplicate copies), via find_object.
import unreal
bp = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BPC_CastleScroll')
G = '/Game/CastleDefender/Gameplay/Castle/BPC_CastleScroll.BPC_CastleScroll:EventGraph.'
out = []
for n in ('DrawScroll', 'csIfToggle22', 'csDrawIcon', 'csAsZHud'):
    hits = [n] + ['%s_%d' % (n, i) for i in range(6)]
    out.append('%s: %s' % (n, [h for h in hits if unreal.find_object(None, G + h)]))
fns = unreal.BlueprintEditorLibrary.list_events(bp) if hasattr(unreal.BlueprintEditorLibrary, 'list_events') else 'n/a'
out.append('events: %s' % fns)
unreal.log('i5 nodes411: ' + ' | '.join(out))
