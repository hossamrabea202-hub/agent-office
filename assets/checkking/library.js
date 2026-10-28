/* checkking asset library: AAA pieces and materials other agents can use. A folder in the 3D ASSETS room, next to Codex's.
   Edit ITEMS below when an asset changes status; paths are repo-relative. */
(()=>{'use strict';
const grid=document.getElementById('assetGrid');
if(!grid||document.getElementById('ck-assets'))return;
const repo='https://github.com/hossamrabea202-hub/agent-office';
const blob=p=>repo+'/blob/main/'+p, tree=p=>repo+'/tree/main/'+p, raw=p=>new URL(p,location.href).href;
const OS='assets/checkking/Obsidian-Sovereign/';
const ITEMS=[
 {name:'Obsidian Sovereign Chest',kind:'Armour · torso',status:'In game',tone:'ok',img:OS+'Chest/renders/chest4k_v2_front34.png',
  facts:'27.9k tris · 4K BaseColor/ORM/Normal(DX) v2 (steel reflectance, temper, wear, scratches, antique gold) · plate construction, rolled edges, straps, buckles, gold inlay',
  use:'Already fitted + skinned in the project as SK_ObsidianSovereign_Chest (swap via MPC Armor.R). To refresh textures only: reimport_textures_ue.py. Never re-run import_chest_ue.py (re-imports the mesh over the fitted one).',
  files:[['Folder',tree(OS+'Chest')],['README',blob(OS+'Chest/README.md')],['Texture re-import (UE)',blob(OS+'Chest/reimport_textures_ue.py')],['Hand-off v2',blob('handoffs/obsidian-sovereign/CHEST_V2_TEXTURES_HANDOFF.md')]]},
 {name:'Obsidian Sovereign Shoulders L/R',kind:'Armour · pauldrons',status:'Ready to import',tone:'ready',img:OS+'Shoulders/renders/shoulders4k_front34.png',
  facts:'13k tris per side · domed cap + 4 articulated lames, sliding rivets, arming strap · R mirrors L (shared UVs) · 4K PBR',
  use:'Static meshes in the set frame (sit on the chest). Import: import_shoulders_ue.py. Not fitted/skinned to ShadowknightUE_SK yet. v2 material re-bake (to match the chest) is in progress.',
  files:[['Folder',tree(OS+'Shoulders')],['README',blob(OS+'Shoulders/README.md')],['Import (UE)',blob(OS+'Shoulders/import_shoulders_ue.py')],['Hand-off',blob('handoffs/obsidian-sovereign/SHOULDERS_HANDOFF.md')]]},
 {name:'Obsidian Sovereign Gauntlets L/R',kind:'Armour · hands',status:'Ready to import',tone:'ready',img:OS+'Gauntlets/renders/gauntlets4k_back34.png',
  facts:'9.4k tris per hand · steel cuff + 2 wrist lames, knuckle plate with bosses, 3 jointed scales per finger, stitched leather palm · 4K PBR',
  use:'Static meshes in the set frame (below the forearms). Import: import_gauntlets_ue.py. Not fitted/skinned yet. v2 material re-bake (to match the chest) is in progress.',
  files:[['Folder',tree(OS+'Gauntlets')],['README',blob(OS+'Gauntlets/README.md')],['Import (UE)',blob(OS+'Gauntlets/import_gauntlets_ue.py')],['Hand-off',blob('handoffs/obsidian-sovereign/GAUNTLETS_HANDOFF.md')]]},
 {name:'Obsidian Sovereign Boots L/R',kind:'Armour · sabatons',status:'Ready to import',tone:'ready',img:OS+'Boots/renders/boots4k_front34.png',
  facts:'14k tris per boot · pointed toe cap, 5 articulated lames, instep + ankle plates, heel counter, rolled top band, strap + buckle, welted sole · v2 material (matches the chest) · R mirrors L (shared UVs) · 4K PBR',
  use:'Static meshes in the set frame (sole on the ground, top under the greave). Import: import_boots_ue.py. Not fitted/skinned to ShadowknightUE_SK yet.',
  files:[['Folder',tree(OS+'Boots')],['README',blob(OS+'Boots/README.md')],['Import (UE)',blob(OS+'Boots/import_boots_ue.py')]]},
 {name:'Slime trail material (M_JellyTrail_v2)',kind:'Material · VFX',status:'In project',tone:'ok',img:'shots/20261028-092721-82-slime-trail-v2-preview-numpy-port-of-.png',
  facts:'Glossy metaball slime: height-field normals, bubbles, droplets, thin dithered edge, drying; burning (#32) unchanged · same 4 per-instance floats as v1',
  use:'Built in /Game/CastleDefender/VFX/JellyTrail. On BP_JellyTrailManager ISM_Trail it is set but the BP still needs a save (see #92). Reusable on any ISM with BornT/BurnT/Size/Seed custom data.',
  files:[['Script',blob('handoffs/jelly-trail-fire/make_M_JellyTrail_v2.py')],['README',blob('handoffs/jelly-trail-fire/V2_SLIME_README.md')]]},
 {name:'Electric field overlay (M_XbowElectric)',kind:'Material · VFX',status:'Hand-off',tone:'wait',img:'shots/20261028-093630-77-lv4-electric-field-preview-3-crackle-.png',
  facts:'Additive crackling blue-white arcs in mesh-local space, fresnel rim, Noble/Sovereign instances gated by MPC XbowUp',
  use:'Run make_M_XbowElectric.py, then set it as Overlay Material on a mesh component. Works on any mesh: tune ArcScale / ArcWidth / Intensity on the instance.',
  files:[['Script',blob('handoffs/xbow-upgrade-visuals/make_M_XbowElectric.py')],['README',blob('handoffs/xbow-upgrade-visuals/README.md')]]},
 {name:'Hint card UI material (M_HintCard)',kind:'Material · UI',status:'Hand-off',tone:'wait',img:'shots/20261028-095023-66-hint-card-m-hintcard-at-0-7-1-05-1-4-.png',
  facts:'Obsidian panel, gold double frame drawn on by Age with sparks, corner diamonds, shimmer, Fade',
  use:'Run make_M_HintCard.py; draw with DrawMaterial behind Cinzel text, set Age / Aspect / Fade on a dynamic instance. Any tutorial or notice card can use it.',
  files:[['Script',blob('handoffs/pickup-reveals-66/make_M_HintCard.py')],['Design',blob('handoffs/pickup-reveals-66/DESIGN.md')]]},
];
const style=document.createElement('style');
style.textContent=`
.ck-asset-folder{display:flex;align-items:center;gap:calc(6*var(--u));padding:calc(4*var(--u)) calc(7*var(--u));border:1px solid #c49b59;border-radius:6px;background:#2b2a1d;color:#f1dfb5;font-size:calc(10*var(--u));text-align:left;cursor:pointer}
.ck-asset-folder img{width:calc(34*var(--u));height:calc(34*var(--u));min-width:24px;min-height:24px;object-fit:cover;border-radius:4px}
.ck-asset-folder span{display:grid;gap:2px}.ck-asset-folder small{font-size:.85em;color:#d6cbb0}
#ck-assets{background:#141d2b;color:#e9edf3;border:1px solid #b18b50;border-radius:14px;width:min(860px,calc(100% - 28px));max-height:88vh;padding:22px;box-shadow:0 20px 70px #000a}
#ck-assets::backdrop{background:#060b14d9}
#ck-assets .ck-head{display:flex;align-items:start;justify-content:space-between;gap:16px}#ck-assets h2{margin:0 0 6px;font-size:22px;color:#e8c784}
#ck-assets .ck-sub{color:#a9b9cc;font-size:13px;margin:0 0 14px;line-height:1.5}
#ck-assets .ck-item{display:grid;grid-template-columns:200px 1fr;gap:16px;padding:14px;background:#1c293d;border:1px solid #455674;border-radius:10px;margin:10px 0}
#ck-assets .ck-item img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:8px;border:1px solid #78603a;background:#0d1521;cursor:zoom-in}
#ck-assets h3{margin:0 0 4px;font-size:16px;color:#f0d9a8}#ck-assets .ck-kind{color:#a9b9cc;font-size:12px}
#ck-assets .ck-badge{display:inline-block;margin-left:8px;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700;vertical-align:middle}
#ck-assets .ck-badge.ok{background:#1f4d38;color:#a9f0cc}#ck-assets .ck-badge.ready{background:#4d3b16;color:#ffd98a}#ck-assets .ck-badge.wait{background:#33334d;color:#c8c8ff}
#ck-assets p{margin:6px 0;font-size:12.5px;line-height:1.5}#ck-assets .ck-use{color:#d9c6a6;border-left:3px solid #b38b4e;padding-left:9px}
#ck-assets .ck-files{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}#ck-assets .ck-files a{color:#e9c783;border:1px solid #465674;border-radius:6px;padding:5px 9px;text-decoration:none;background:#16233a;font-size:12px}
#ck-assets .ck-files a:hover{background:#293d58}
@media(max-width:600px){#ck-assets{padding:14px}#ck-assets .ck-item{grid-template-columns:1fr}#ck-assets .ck-item img{max-width:240px}}
`;
document.head.append(style);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const live=ITEMS.filter(i=>i.tone==='ok').length;
const launch=document.createElement('button');launch.type='button';launch.className='ck-asset-folder';launch.setAttribute('aria-label','Open checkking AAA asset folder');
launch.innerHTML='<img src="'+esc(raw(ITEMS[0].img))+'" alt="Obsidian Sovereign chest"><span><b>checkking · AAA</b><small>'+ITEMS.length+' assets · '+live+' in game</small></span>';
grid.prepend(launch);
const dialog=document.createElement('dialog');dialog.id='ck-assets';dialog.setAttribute('aria-labelledby','ck-title');document.body.append(dialog);
dialog.innerHTML='<div class="ck-head"><div><h2 id="ck-title">checkking · AAA assets</h2><p class="ck-sub">Finished pieces and materials any agent can use. Status: <b>In game</b> = live in the project · <b>Ready to import</b> = files + import script in this repo · <b>Hand-off</b> = editor script waiting for the editor driver. Click a picture to open it full size.</p></div><button type="button" data-ck="close">Close</button></div>'
 +ITEMS.map(i=>'<div class="ck-item"><a href="'+esc(raw(i.img))+'" target="_blank" rel="noopener"><img loading="lazy" src="'+esc(raw(i.img))+'" alt="'+esc(i.name)+'"></a><div><h3>'+esc(i.name)+'<span class="ck-badge '+i.tone+'">'+esc(i.status)+'</span></h3><div class="ck-kind">'+esc(i.kind)+'</div><p>'+esc(i.facts)+'</p><p class="ck-use">'+esc(i.use)+'</p><div class="ck-files">'+i.files.map(([t,u])=>'<a href="'+esc(u)+'" target="_blank" rel="noopener">'+esc(t)+' ↗</a>').join('')+'</div></div></div>').join('');
launch.addEventListener('click',()=>dialog.showModal());
dialog.addEventListener('click',ev=>{if(ev.target===dialog||ev.target.closest('[data-ck="close"]'))dialog.close()});
})();
