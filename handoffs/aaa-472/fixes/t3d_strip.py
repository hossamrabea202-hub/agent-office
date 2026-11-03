# #472 (i5): remove named nodes from a graph copy (Ctrl+A / Ctrl+C format), cleanly: the back-links on the other nodes go too, and pure
# helper nodes that only fed the removed nodes go with them. applyall can add and rewire but not delete.
#   python t3d_strip.py in.txt out.txt Node [Node ...]     (import: strip(text, names) -> (text, removed))
import re, sys
BLOCK = re.compile(r'^Begin Object .*?^End Object\r?\n?', re.S | re.M)
def parse(t):
    out = []
    for m in BLOCK.finditer(t):
        b = m.group(0); out.append({'name': re.search(r'Name="([^"]+)"', b).group(1), 'text': b})
    return out
def pins(b): return re.findall(r'CustomProperties Pin \((.*)\)', b)
def has_exec(b): return 'PinCategory="exec"' in b
def links_of(b): return [x.split(' ')[0] for p in pins(b) for x in re.findall(r'(\w+ [0-9A-F]{32}),', (re.search(r'LinkedTo=\(([^)]*)\)', p) or [None, ''])[1])]
def drop_links(b, gone):
    def fix(m):
        kept = [x for x in re.findall(r'[^,()]+ [0-9A-F]{32},', m.group(1)) if x.strip().split(' ')[0] not in gone]
        return 'LinkedTo=(%s),' % ''.join(kept) if kept else ''
    return re.sub(r'LinkedTo=\(([^)]*)\),', fix, b)
def strip(t, names):
    nodes = parse(t); by = {n['name']: n for n in nodes}
    missing = [n for n in names if n not in by]
    if missing: raise SystemExit('t3d_strip: not in the graph: %s' % missing)
    gone, front = set(), set(names)
    while front:
        gone |= front
        hit = {l for n in front for l in links_of(by[n]['text'])} - gone
        for n in nodes:
            if n['name'] in gone: continue
            n['text'] = drop_links(n['text'], front)
        # pure helper that fed a removed node and now has no consumer left
        front = {h for h in hit if h in by and not has_exec(by[h]['text']) and not any('Direction="EGPD_Output"' in p and 'LinkedTo=' in p for p in pins(by[h]['text']))}
    head = t[:BLOCK.search(t).start()] if BLOCK.search(t) else ''
    return head + ''.join(n['text'] for n in nodes if n['name'] not in gone), sorted(gone)
if __name__ == '__main__':
    t = open(sys.argv[1], encoding='utf-8', newline='').read()
    r, gone = strip(t, sys.argv[3:]); open(sys.argv[2], 'w', encoding='utf-8', newline='').write(r); print('removed', len(gone), gone)
