# i5 #421: run TGA's setup_muster2_ue.py from its own folder (ue_run.sh copies scripts into ue_inbox, so its HERE
# would point there). Arg 1: "apply" sets DRY_RUN = False; anything else / none = dry run.
import sys
SRC = 'C:/Users/hossam.rabea/agent-office/handoffs/muster-v2-420/build/setup_muster2_ue.py'
code = open(SRC, encoding='utf-8').read()
if len(sys.argv) > 1 and sys.argv[1] == 'apply':
    code = code.replace('DRY_RUN = True\n', 'DRY_RUN = False\n', 1)
# UE 5.8 refuses set_editor_property('show_only_actors') on a spawned capture ("cannot be edited on templates"); use the call.
code = code.replace("cc.set_editor_property('show_only_actors', [a])", "cc.show_only_actor_components(a, True)")
# Bust look (first pass was blown out and ghosted): fixed exposure, no eye adaptation / TAA / motion blur / fog, 3 captures.
if 'recapture' in sys.argv:
    code = code.replace('RECAPTURE = False\n', 'RECAPTURE = True\n', 1)
    code = code.replace("for n in ('Fog', 'Atmosphere', 'VolumetricFog')]",
                        "for n in ('Fog', 'Atmosphere', 'VolumetricFog', 'TemporalAA', 'AntiAliasing', 'MotionBlur', 'Bloom', 'LensFlares', 'DepthOfField', 'SkyLighting', 'Lighting' if False else 'AmbientOcclusion')]")
    code = code.replace("        cc.capture_scene()\n",
                        "        pp = cc.get_editor_property('post_process_settings')\n"
                        "        pp.set_editor_property('override_auto_exposure_method', True); pp.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL)\n"
                        "        pp.set_editor_property('override_auto_exposure_bias', True); pp.set_editor_property('auto_exposure_bias', float(EXPO))\n"
                        "        cc.set_editor_property('post_process_settings', pp); cc.set_editor_property('post_process_blend_weight', 1.0)\n"
                        "        for _ in range(3): cc.capture_scene()\n", 1)
EXPO = next((a.split('=')[1] for a in sys.argv if a.startswith('expo=')), '9')
code = code.replace('import os, json, unreal', 'import os, json, unreal\nEXPO = %r' % EXPO, 1)
exec(compile(code, SRC, 'exec'), {'__name__': '__main__', '__file__': SRC})
print(open(SRC.rsplit('/', 1)[0] + '/setup_muster2.txt', encoding='utf-8').read())
