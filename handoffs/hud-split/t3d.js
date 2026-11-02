// i5: tiny T3D graph-export model shared by the HUD-split tools. parse(text) -> {order, N}; node.pins[]: {id,name,dir,cat,links:[[node,pinId]],line}
exports.parse = txt => {
  const N = {}, order = [];
  for (const raw of txt.split(/^(?=Begin Object )/m)) {
    if (!raw.startsWith('Begin Object')) continue;
    const name = (raw.match(/Name="([^"]+)"/) || [])[1];
    const cls = ((raw.match(/Class=([^\s]+)/) || [])[1] || '').split('.').pop();
    const lines = raw.split(/\r?\n/);
    const pins = lines.map((l, i) => ({ l, i })).filter(o => /^\s*CustomProperties Pin \(/.test(o.l)).map(({ l, i }) => ({
      id: (l.match(/PinId=([0-9A-F]+)/) || [])[1], name: (l.match(/PinName="([^"]*)"/) || [])[1],
      dir: /Direction="EGPD_Output"/.test(l) ? 'out' : 'in', cat: (l.match(/PinType\.PinCategory="([^"]*)"/) || [])[1],
      links: ((l.match(/LinkedTo=\(([^)]*)\)/) || [])[1] || '').split(',').map(s => s.trim()).filter(Boolean).map(s => s.split(' ')),
      lineIdx: i }));
    N[name] = { name, cls, lines, pins, y: +((raw.match(/NodePosY=(-?\d+)/) || [])[1] || 0), x: +((raw.match(/NodePosX=(-?\d+)/) || [])[1] || 0) };
    order.push(name);
  }
  return { N, order };
};
exports.pinOf = (node, id) => node.pins.find(p => p.id === id);
