# #431 (no sunny days, sun too bright) + #432 (slower day/night, playable nights). i9, 2026-11-02. UE 5.8 Python.
#   py wx_daynight_ue.py             REPORT (default): current graph constants + placed-actor / CDO values, changes nothing
#   py wx_daynight_ue.py --apply     sets the values below, compiles + saves the two BPs, sets placed instances (map NOT saved)
#   py wx_daynight_ue.py --revert    puts every value back from wx_daynight_backup.json
# BP_DayNight graph constants (pin defaults, no links):
#   sun intensity  = 1 + SUN_SCALE * daylight     (was 9 -> noon 10; now 3 -> noon 4, overcast-soft)
#   sky light      = SKY_FLOOR + (1-SKY_FLOOR) * daylight   (was 0.15 + 0.85*d -> night 0.15; now 0.35 + 0.65*d)
# Variables: DayLengthMin x DAY_MULT, MoonLux x MOON_MULT, FogNightExtra x FOG_NIGHT_MULT; BPC_Weather PClear 0
# (P* are cumulative cut-offs: clear is dropped, rain/fog/storm keep their old proportions; first day overcast).
import json, os, sys, unreal
A = sys.argv[1:]
APPLY, REV = '--apply' in A, '--revert' in A
HERE = os.path.dirname(os.path.abspath(__file__)); BACKUP = os.path.join(HERE, 'wx_daynight_backup.json')
BEL, PL, EAL = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.EditorAssetLibrary
DN, WX = '/Game/CastleDefender/Environment/DayNight/BP_DayNight', None
SUN_SCALE, SKY_FLOOR = 3.0, 0.35
DAY_MULT, MOON_MULT, FOG_NIGHT_MULT = 4.0, 2.5, 0.5
log = ['wx/daynight ' + ('APPLY' if APPLY else 'REVERT' if REV else 'REPORT')]
reg = unreal.AssetRegistryHelpers.get_asset_registry()
WX = [str(a.package_name) for a in reg.get_assets(unreal.ARFilter(package_paths=['/Game'], recursive_paths=True)) if str(a.asset_name) == 'BPC_Weather'][0]


def pins_with(bp, member, pin, value):
    eg = BEL.find_event_graph(bp); out = []
    graphs = [eg] + [g for g in unreal.ObjectIterator(unreal.EdGraph) if g.get_outer() == bp]
    for n in unreal.ObjectIterator(unreal.K2Node_CallFunction):
        if n.get_outer() not in graphs: continue
        p = BEL.find_input_pin(n, pin)
        if p and abs(float(PL.get_pin_value(p) or 0) - value) < 1e-6 and member in n.get_name() + str(n.get_editor_property('function_reference') if False else ''):
            out.append((n, p))
    return out


def const_pins(bp):
    # find by value: Multiply B=9 (sun), Add B=0.15 + Multiply B=0.85 (sky). Each must be unique.
    found = {}
    for key, val in (('sun_mul', 9.0), ('sky_add', 0.15), ('sky_mul', 0.85)):
        hits = []
        for n in unreal.ObjectIterator(unreal.K2Node_CallFunction):
            if n.get_outermost() != bp.get_outermost(): continue
            p = BEL.find_input_pin(n, 'B')
            try: v = float(PL.get_pin_value(p)) if p else None
            except Exception: v = None
            if v is not None and abs(v - val) < 1e-6: hits.append((n, p))
        found[key] = hits
    return found


dnbp, wxbp = unreal.load_asset(DN), unreal.load_asset(WX)
dncdo = unreal.get_default_object(BEL.generated_class(dnbp)); wxcdo = unreal.get_default_object(BEL.generated_class(wxbp))
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
dnacts = [a for a in acts if a.get_class() == BEL.generated_class(dnbp)]
wxcomps = [c for a in acts for c in a.get_components_by_class(unreal.ActorComponent) if c.get_class() == BEL.generated_class(wxbp)]
VARS_DN, VARS_WX = ('DayLengthMin', 'MoonLux', 'FogNightExtra', 'FogDay', 'StartHour'), ('PClear', 'PRain', 'PFog', 'BlendSec', 'Today', 'Tomorrow')


def get(o, k):
    try: return o.get_editor_property(k)
    except Exception as e: return 'n/a'


cp = const_pins(dnbp)
for k, v in cp.items(): log.append('graph %-8s %d hit(s) %s' % (k, len(v), [n.get_name() for n, _ in v]))
log.append('BP_DayNight CDO %s' % {k: get(dncdo, k) for k in VARS_DN})
for a in dnacts: log.append('  placed %s %s' % (a.get_actor_label(), {k: get(a, k) for k in VARS_DN}))
log.append('BPC_Weather CDO %s' % {k: get(wxcdo, k) for k in VARS_WX})
for c in wxcomps: log.append('  placed %s.%s %s' % (c.get_owner().get_actor_label(), c.get_name(), {k: get(c, k) for k in VARS_WX}))

if APPLY or REV:
    if APPLY:
        if os.path.exists(BACKUP): raise SystemExit('already applied (backup exists): --revert first')
        if any(len(v) != 1 for v in cp.values()): raise SystemExit('graph constants not unique/missing: %s' % {k: len(v) for k, v in cp.items()})
        objs = [('dncdo', dncdo, VARS_DN), ('wxcdo', wxcdo, VARS_WX)] + [('dn:' + a.get_actor_label(), a, VARS_DN) for a in dnacts] + [('wx:' + c.get_owner().get_actor_label(), c, VARS_WX) for c in wxcomps]
        saved = {'vars': {name: {k: get(o, k) for k in ks if get(o, k) != 'n/a'} for name, o, ks in objs},
                 'consts': {'sun_mul': 9.0, 'sky_add': 0.15, 'sky_mul': 0.85}}
        json.dump(saved, open(BACKUP, 'w'), indent=1)
        newc = {'sun_mul': SUN_SCALE, 'sky_add': SKY_FLOOR, 'sky_mul': 1.0 - SKY_FLOOR}
        for k, v in cp.items(): PL.set_pin_value(v[0][1], '%.6f' % newc[k])

        def newvals(name, cur):
            out = {}
            if name.startswith('dn'):
                for k, m in (('DayLengthMin', DAY_MULT), ('MoonLux', MOON_MULT), ('FogNightExtra', FOG_NIGHT_MULT)):
                    if k in cur: out[k] = float(cur[k]) * m
            else:
                # P* are CUMULATIVE cut-offs on one roll r in 0..1: r<PClear clear, r<PRain rain, r<PFog fog, else storm.
                # Drop clear, keep rain/fog/storm in their old proportions.
                if all(k in cur for k in ('PClear', 'PRain', 'PFog')):
                    c, r, f = float(cur['PClear']), float(cur['PRain']), float(cur['PFog'])
                    rest = max(1.0 - c, 1e-6)
                    out = {'PClear': 0.0, 'PRain': (r - c) / rest, 'PFog': (f - c) / rest}
                    if 'Today' in cur and int(cur['Today']) == 0: out['Today'] = 2      # first day overcast, not clear
                    if 'Tomorrow' in cur and int(cur['Tomorrow']) == 0: out['Tomorrow'] = 2
            return out
        for name, o, ks in objs:
            for k, v in newvals(name, saved['vars'][name]).items():
                try: o.set_editor_property(k, v)
                except Exception as e: log.append('  could not set %s.%s (%s)' % (name, k, str(e)[:60]))
            log.append('set %s -> %s' % (name, {k: get(o, k) for k in ks}))
    else:
        if not os.path.exists(BACKUP): raise SystemExit('no backup to revert')
        saved = json.load(open(BACKUP))
        for k, v in cp.items(): pass
        # constants: find by NEW values and put the old back
        for key, newv, oldv in (('sun_mul', SUN_SCALE, 9.0), ('sky_add', SKY_FLOOR, 0.15), ('sky_mul', 1.0 - SKY_FLOOR, 0.85)):
            for n in unreal.ObjectIterator(unreal.K2Node_CallFunction):
                if n.get_outermost() != dnbp.get_outermost(): continue
                p = BEL.find_input_pin(n, 'B')
                try:
                    if p and abs(float(PL.get_pin_value(p)) - newv) < 1e-6: PL.set_pin_value(p, '%.6f' % oldv); log.append('const %s back to %s' % (key, oldv))
                except Exception: pass
        objs = {'dncdo': dncdo, 'wxcdo': wxcdo}
        objs.update({'dn:' + a.get_actor_label(): a for a in dnacts}); objs.update({'wx:' + c.get_owner().get_actor_label(): c for c in wxcomps})
        for name, vals in saved['vars'].items():
            o = objs.get(name)
            if not o: continue
            for k, v in vals.items():
                try: o.set_editor_property(k, v)
                except Exception: pass
        os.remove(BACKUP); log.append('reverted')
    for bp, p in ((dnbp, DN), (wxbp, WX)):
        BEL.compile_blueprint(bp); EAL.save_asset(p)
    log.append('compiled + saved BP_DayNight and BPC_Weather; map NOT saved (placed values: save the level after the look check)')
print('\n'.join(str(x) for x in log))
