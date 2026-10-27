/* Codex asset library: shared files, independent of the office's browser-local agent records. */
(()=>{'use strict';
const script=document.currentScript;
const base=new URL('./',script.src);
const part=new URL('Obsidian-Sovereign/Helmet/',base);
const repo='https://github.com/hossamrabea202-hub/agent-office';
const archive=repo+'/releases/download/helmet-wip-2026-10-27/Obsidian_Sovereign_Helmet_WIP_2026-10-27.zip';
const grid=document.getElementById('assetGrid');
if(!grid||document.getElementById('codex-assets'))return;
const style=document.createElement('style');
style.textContent=`
.codex-asset-folder{display:flex;align-items:center;gap:calc(6*var(--u));padding:calc(4*var(--u)) calc(7*var(--u));border:1px solid #c49b59;border-radius:6px;background:#30283d;color:#f1dfb5;font-size:calc(10*var(--u));text-align:left;cursor:pointer}
.codex-asset-folder img{width:calc(34*var(--u));height:calc(34*var(--u));min-width:24px;min-height:24px;object-fit:cover;border-radius:4px}
.codex-asset-folder span{display:grid;gap:2px}.codex-asset-folder small{font-size:.85em;color:#c9bbd6}
#codex-assets{background:#141d2b;color:#e9edf3;border:1px solid #b18b50;border-radius:14px;width:min(800px,calc(100% - 28px));max-height:88vh;padding:22px;box-shadow:0 20px 70px #000a}
#codex-assets::backdrop{background:#060b14d9}
#codex-assets .ca-head{display:flex;align-items:start;justify-content:space-between;gap:16px}
#codex-assets h2{margin:3px 0 16px;font-size:23px}#codex-assets h3{margin:0 0 7px}
#codex-assets .ca-breadcrumb{display:flex;gap:7px;flex-wrap:wrap;align-items:center;color:#a9b9cc;font-size:12px}
#codex-assets .ca-breadcrumb button{border:0;background:none;padding:2px 0;color:#dfb874;font-size:12px}
#codex-assets .ca-folder{display:flex;align-items:center;gap:14px;width:100%;padding:15px;text-align:left;background:#1c293d;border:1px solid #455674;border-radius:10px;margin:10px 0}
#codex-assets .ca-folder img{width:74px;height:74px;object-fit:cover;border-radius:7px;border:1px solid #78603a}
#codex-assets .ca-folder .ca-label{display:grid;gap:6px}#codex-assets .ca-folder strong{font-size:18px;color:#e8c784}
#codex-assets .ca-muted{color:#a9b9cc;line-height:1.6;font-size:13px}
#codex-assets .ca-hero{display:grid;grid-template-columns:minmax(180px,.85fr) 1.15fr;gap:22px;align-items:start}
#codex-assets .ca-preview{width:100%;border-radius:9px;background:#0d1521;border:1px solid #40506a}
#codex-assets .ca-badge{display:inline-block;padding:5px 8px;border:1px solid #936d3c;background:#342b1d;color:#f0cf94;border-radius:6px;font-size:11px;margin-bottom:12px}
#codex-assets .ca-files{display:grid;gap:9px;margin:15px 0}
#codex-assets .ca-files a{color:#e9c783;border:1px solid #465674;border-radius:7px;padding:10px 12px;text-decoration:none;background:#1b2940;font-size:13px}
#codex-assets .ca-files a:hover{background:#293d58}#codex-assets a:focus-visible,#codex-assets button:focus-visible{outline:2px solid #ebc77f;outline-offset:3px}
#codex-assets .ca-note{padding:12px;background:#211f1b;border-left:3px solid #b38b4e;line-height:1.6;font-size:12px;color:#d9c6a6;margin-top:16px}
#codex-assets .ca-folder-glyph{font-size:38px;color:#d9af65;line-height:1}
@media(max-width:580px){#codex-assets{padding:15px}#codex-assets .ca-hero{grid-template-columns:1fr}#codex-assets .ca-preview{max-width:270px;justify-self:center}}
`;
document.head.append(style);
const launch=document.createElement('button');launch.type='button';launch.className='codex-asset-folder';launch.setAttribute('aria-label','Open Codex asset folder');
launch.innerHTML='<img src="'+new URL('icon.png',part).href+'" alt="Black and gold Obsidian Sovereign helmet"><span><b>Codex</b><small>1 set · 1 part · WIP</small></span>';
grid.prepend(launch);
const dialog=document.createElement('dialog');dialog.id='codex-assets';dialog.setAttribute('aria-labelledby','ca-title');document.body.append(dialog);
const crumb=(name,level)=>'<button type="button" data-ca="'+level+'">'+name+'</button>';
function render(level){
 let title='Codex',body='',trail=crumb('3D Assets','close')+'<span>/</span>';
 if(level===0){
  trail+='<span>Codex</span>';
  body='<p class="ca-muted">Shared model files and editable handoffs created by Codex.</p><button type="button" class="ca-folder" data-ca="1"><span class="ca-folder-glyph" aria-hidden="true">▰</span><span class="ca-label"><strong>Obsidian Sovereign</strong><span class="ca-muted">Modular black-and-gold armour set · 1 part uploaded</span></span></button>';
 }else if(level===1){
  title='Obsidian Sovereign';trail+=crumb('Codex','0')+'<span>/</span><span>Obsidian Sovereign</span>';
  body='<p class="ca-muted">The armour set is in progress. Helmet is the first uploaded part; the remaining equipment has not been delivered.</p><button type="button" class="ca-folder" data-ca="2"><img src="'+new URL('icon.png',part).href+'" alt="Helmet preview"><span class="ca-label"><strong>Helmet</strong><span class="ca-muted">FBX + textured GLB + complete Blender/4K package</span><span class="ca-muted">18,720 triangles · static, unskinned WIP</span></span></button>';
 }else{
  title='Helmet';trail+=crumb('Codex','0')+'<span>/</span>'+crumb('Obsidian Sovereign','1')+'<span>/</span><span>Helmet</span>';
  body='<div class="ca-hero"><img class="ca-preview" src="'+new URL('preview.png',part).href+'" alt="Rendered black and gold helmet, three-quarter view"><div><span class="ca-badge">WORK IN PROGRESS · UNSKINNED</span><h3>Obsidian Sovereign Helmet</h3><p class="ca-muted">One connected hollow shell with eye apertures and inner lining. 18,720 triangles. The game master has 4K baked maps; the lightweight GLB uses 2K maps.</p><div class="ca-files"><a href="'+new URL('SM_ObsidianSovereign_Helmet.fbx',part).href+'" download>Download FBX geometry · 0.67 MB</a><a href="'+new URL('Obsidian_Sovereign_Helmet_preview_2K.glb',part).href+'" download>Download textured GLB preview · 8.2 MB</a><a href="'+archive+'">Download Blender + high-poly + 4K master · 177 MB</a><a href="'+repo+'/blob/main/assets/Codex/Obsidian-Sovereign/Helmet/README.md" target="_blank" rel="noopener">Read takeover instructions and file inventory ↗</a><a href="'+repo+'/blob/main/assets/Codex/Obsidian-Sovereign/Helmet/validation.json" target="_blank" rel="noopener">Read technical validation ↗</a><a href="'+repo+'/issues/1" target="_blank" rel="noopener">Open project-PC reference-export task ↗</a></div></div></div><div class="ca-note">Not AAA-approved or character-fitted. Artistic refinement, head/neck skinning, gorget clearance, HelmW visibility, and Unreal Engine 5.3 import remain outstanding. Keep the full Blender folder and textures together when another agent takes over.</div>';
 }
 dialog.innerHTML='<div class="ca-head"><div><nav class="ca-breadcrumb" aria-label="Asset folders">'+trail+'</nav><h2 id="ca-title">'+title+'</h2></div><button type="button" data-ca="close" aria-label="Close Codex assets">Close</button></div>'+body;
}
launch.addEventListener('click',()=>{render(0);dialog.showModal()});
dialog.addEventListener('click',ev=>{if(ev.target===dialog){dialog.close();return}const b=ev.target.closest('[data-ca]');if(!b)return;if(b.dataset.ca==='close')dialog.close();else render(Number(b.dataset.ca))});
})();