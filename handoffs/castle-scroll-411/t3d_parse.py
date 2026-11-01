# Minimal T3D graph parser (i5, #411): nodes {name: {cls, props, pins:{pinid:(name, dir, linked[(node,pinid)], default)}}}.
import re, sys
def parse(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    nodes = {}
    for m in re.finditer(r'(?ms)^Begin Object Class=(\S+) Name="([^"]+)"[^\n]*\n(.*?)^End Object', txt):
        cls, name, body = m.group(1), m.group(2), m.group(3)
        pins = {}
        for pm in re.finditer(r'CustomProperties Pin \((.*)\)\s*$', body, re.M):
            s = pm.group(1)
            pid = re.search(r'PinId=(\w+)', s).group(1)
            pn = re.search(r'PinName="([^"]*)"', s).group(1)
            out = 'Direction="EGPD_Output"' in s
            dv = re.search(r'DefaultValue="((?:[^"\\]|\\.)*)"', s)
            lk = re.search(r'LinkedTo=\(([^)]*)\)', s)
            links = [tuple(x.split(' ')) for x in lk.group(1).split(',') if x.strip()] if lk else []
            pins[pid] = (pn, out, links, dv.group(1) if dv else None)
        props = body[:2000]
        nodes[name] = {'cls': cls.split('.')[-1].strip('"\''), 'body': body, 'pins': pins}
    return nodes
def member(n):
    m = re.search(r'MemberName="([^"]+)"', n['body']); return m.group(1) if m else ''
def comment(n):
    m = re.search(r'NodeComment="([^"]*)"', n['body']); return m.group(1) if m else ''
