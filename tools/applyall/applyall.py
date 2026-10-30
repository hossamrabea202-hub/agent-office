#!/usr/bin/env python3
"""applyall.py - merge Unreal Engine 5.3 Blueprint paste text (T3D) into an
exported live graph, apply rewires, validate, and write one merged T3D.

Pure standard library. Python 3.8+.

Commands
  merge  --live LIVE.t3d --manifest MANIFEST.json --out MERGED.t3d [--dry-run]
  check  FILE.t3d [Node ...]
  manifest-from-readme README.md [--out DRAFT.json]

See README.md and manifest_schema.md next to this file.
"""

import argparse
import json
import os
import re
import sys

HEX32 = re.compile(r"^[0-9A-Fa-f]{32}$")
PIN_PREFIX = "CustomProperties Pin ("
DEFAULT_GAP_Y = 600  # space between live graph and a paste placed below it


class MergeError(Exception):
    """A problem that stops the merge. Nothing is written."""


# --------------------------------------------------------------------------
# Low level text helpers
# --------------------------------------------------------------------------

def split_fields(text, start, end):
    """Split text[start:end] at top-level commas (outside quotes and parens).

    Returns a list of (field_start, field_end) absolute indices. field_end is
    the index of the separating comma (or `end` for a last field without one).
    """
    fields = []
    depth = 0
    in_quote = False
    escape = False
    fstart = start
    for i in range(start, end):
        ch = text[i]
        if in_quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_quote = False
            continue
        if ch == '"':
            in_quote = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            fields.append((fstart, i))
            fstart = i + 1
    if text[fstart:end].strip():
        fields.append((fstart, end))
    return fields


def read_text(path):
    with open(path, "rb") as f:
        data = f.read()
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        text = data.decode("utf-16")
    else:
        text = data.decode("utf-8", errors="surrogateescape")
    if text.startswith("﻿"):
        text = text[1:]
    return text


def write_text(path, text):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(text.encode("utf-8", errors="surrogateescape"))
    os.replace(tmp, path)


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

class Pin:
    def __init__(self, node, line_index, raw):
        self.node = node
        self.line_index = line_index
        self.raw = raw
        self.dirty = False
        self.pin_id = None
        self.name = None
        self.direction = "in"
        self.category = ""
        self.links = []  # list of [node_name, pin_id]
        self._linked_span = None  # (start, end_inclusive_comma) of LinkedTo field
        self._insert_at = None  # where to insert LinkedTo if absent
        self._parse()

    def _parse(self):
        line = self.raw
        open_i = line.index(PIN_PREFIX) + len(PIN_PREFIX) - 1
        close_i = line.rstrip().rfind(")")
        if close_i <= open_i:
            raise MergeError("Bad pin line in node %s: %s" % (self.node.name, line[:120]))
        persistent_at = None
        for (s, e) in split_fields(line, open_i + 1, close_i):
            field = line[s:e]
            key, _, value = field.partition("=")
            key = key.strip()
            if key == "PinId":
                self.pin_id = value.strip().upper()
            elif key == "PinName":
                self.name = unquote(value.strip())
            elif key == "Direction":
                self.direction = "out" if "Output" in value else "in"
            elif key == "PinType.PinCategory":
                self.category = unquote(value.strip())
            elif key == "LinkedTo":
                end_incl = e if e < len(line) and line[e] == "," else e - 1
                self._linked_span = (s, end_incl)
                self.links = parse_link_list(value.strip())
            elif key == "PersistentGuid" and persistent_at is None:
                persistent_at = s
        self._insert_at = persistent_at if persistent_at is not None else close_i
        if not self.pin_id:
            raise MergeError("Pin without PinId in node %s" % self.node.name)

    @property
    def single_link(self):
        """Exec outputs and data inputs may hold only one link."""
        if self.category == "exec":
            return self.direction == "out"
        return self.direction == "in"

    def kind(self):
        cat = "exec" if self.category == "exec" else (self.category or "data")
        return "%s %s" % (cat, self.direction)

    def label(self):
        return "%s.%s" % (self.node.name, self.name)

    def render(self):
        if not self.dirty:
            return self.raw
        line = self.raw
        new = ""
        if self.links:
            new = "LinkedTo=(" + "".join("%s %s," % (n, p) for n, p in self.links) + "),"
        if self._linked_span:
            s, e = self._linked_span
            return line[:s] + new + line[e + 1:]
        if not new:
            return line
        at = self._insert_at
        if at == line.rstrip().rfind(")") and line[:at].rstrip()[-1:] not in (",", "("):
            new = "," + new
        return line[:at] + new + line[at:]


def unquote(v):
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        return v[1:-1]
    return v


def parse_link_list(value):
    v = value.strip()
    if v.startswith("(") and v.endswith(")"):
        v = v[1:-1]
    out = []
    for part in v.split(","):
        part = part.strip()
        if not part:
            continue
        name, _, pid = part.rpartition(" ")
        out.append([name.strip(), pid.strip().upper()])
    return out


class Node:
    def __init__(self, lines):
        self.lines = list(lines)
        header = self.lines[0]
        m = re.search(r'Name="([^"]+)"', header)
        if not m:
            raise MergeError("Begin Object line without Name=: %s" % header[:120])
        self.name = m.group(1)
        mc = re.search(r"Class=(\S+)", header)
        self.cls = mc.group(1) if mc else "?"
        mp = re.search(r'ExportPath="([^"]*)"', header)
        self.export_path = mp.group(1) if mp else None
        self.guid = None
        self.pos_index = {}  # "X"/"Y" -> line index
        self.pins = []
        depth = 0
        for i, line in enumerate(self.lines):
            s = line.strip()
            if s.startswith("Begin Object"):
                depth += 1
                continue
            if s.startswith("End Object"):
                depth -= 1
                continue
            if depth != 1:
                continue
            if s.startswith(PIN_PREFIX):
                self.pins.append(Pin(self, i, line))
            elif s.startswith("NodeGuid="):
                self.guid = s.split("=", 1)[1].strip().upper()
            elif s.startswith("NodePosX="):
                self.pos_index["X"] = i
            elif s.startswith("NodePosY="):
                self.pos_index["Y"] = i

    def short_class(self):
        return self.cls.rsplit(".", 1)[-1]

    def pos(self, axis):
        i = self.pos_index.get(axis)
        if i is None:
            return 0
        try:
            return int(float(self.lines[i].split("=", 1)[1]))
        except ValueError:
            return 0

    def set_pos(self, axis, value):
        i = self.pos_index.get(axis)
        if i is None:
            # add the line after the header (UE accepts any order)
            indent = "   "
            self.lines.insert(1, "%sNodePos%s=%d" % (indent, axis, value))
            self.__init__(self.lines)
            return
        line = self.lines[i]
        prefix = line[:line.index("=") + 1]
        self.lines[i] = "%s%d" % (prefix, value)

    def pin_by_id(self, pin_id):
        pin_id = pin_id.upper()
        for p in self.pins:
            if p.pin_id == pin_id:
                return p
        return None

    def render_lines(self):
        out = list(self.lines)
        for p in self.pins:
            out[p.line_index] = p.render()
        return out


class Graph:
    """A parsed T3D text: a list of items, each a Node or a raw line."""

    def __init__(self, text, source="<text>"):
        self.source = source
        self.newline = "\r\n" if "\r\n" in text else "\n"
        lines = text.replace("\r\n", "\n").split("\n")
        self.items = []
        depth = 0
        cur = None
        for ln, line in enumerate(lines, 1):
            s = line.strip()
            if depth == 0:
                if s.startswith("Begin Object"):
                    cur = [line]
                    depth = 1
                else:
                    self.items.append(line)
                continue
            cur.append(line)
            if s.startswith("Begin Object"):
                depth += 1
            elif s.startswith("End Object"):
                depth -= 1
                if depth == 0:
                    self.items.append(Node(cur))
                    cur = None
        if depth != 0:
            raise MergeError("%s: 'Begin Object' without matching 'End Object' "
                             "(file cut off?)" % source)
        self.reindex()

    @classmethod
    def load(cls, path):
        return cls(read_text(path), source=path)

    def reindex(self):
        self.nodes = [it for it in self.items if isinstance(it, Node)]
        self.by_name = {}
        for n in self.nodes:
            self.by_name.setdefault(n.name, n)

    def add_nodes(self, nodes):
        last = max((i for i, it in enumerate(self.items) if isinstance(it, Node)), default=-1)
        self.items[last + 1:last + 1] = list(nodes)
        self.reindex()

    def link_count(self):
        return sum(len(p.links) for n in self.nodes for p in n.pins)

    def bbox(self):
        if not self.nodes:
            return None
        xs = [n.pos("X") for n in self.nodes]
        ys = [n.pos("Y") for n in self.nodes]
        return min(xs), min(ys), max(xs), max(ys)

    def render(self):
        out = []
        for it in self.items:
            if isinstance(it, Node):
                out.extend(it.render_lines())
            else:
                out.append(it)
        return self.newline.join(out)

    # ---- pin lookup -------------------------------------------------------
    def find_pin(self, node_name, pin_spec):
        node = self.by_name.get(node_name)
        if node is None:
            raise MergeError("Node '%s' not found in the graph." % node_name)
        if HEX32.match(pin_spec):
            p = node.pin_by_id(pin_spec)
            if p:
                return p
        want_dir = None
        spec = pin_spec
        for suffix, d in (("@out", "out"), ("@in", "in")):
            if spec.endswith(suffix):
                spec, want_dir = spec[:-len(suffix)], d
        found = [p for p in node.pins if p.name == spec and (want_dir is None or p.direction == want_dir)]
        if not found:
            found = [p for p in node.pins if p.name.lower() == spec.lower()
                     and (want_dir is None or p.direction == want_dir)]
        if not found:
            names = ", ".join(sorted(set(p.name for p in node.pins)))
            raise MergeError("Pin '%s' not found on node '%s'. Its pins: %s" % (pin_spec, node_name, names))
        if len(found) > 1:
            opts = ", ".join("%s (%s, PinId %s)" % (p.name, p.direction, p.pin_id) for p in found)
            raise MergeError("Pin name '%s' on '%s' is not unique: %s. Add @in / @out or use the PinId."
                             % (pin_spec, node_name, opts))
        return found[0]

    def resolve(self, ref):
        """[node_name, pin_id] -> Pin or None"""
        n = self.by_name.get(ref[0])
        return n.pin_by_id(ref[1]) if n else None

    # ---- link editing -----------------------------------------------------
    def has_link(self, a, b):
        return [b.node.name, b.pin_id] in a.links

    def add_link(self, a, b):
        a.links.append([b.node.name, b.pin_id])
        b.links.append([a.node.name, a.pin_id])
        a.dirty = b.dirty = True

    def remove_link(self, a, b):
        ra = [b.node.name, b.pin_id]
        rb = [a.node.name, a.pin_id]
        removed = False
        if ra in a.links:
            a.links.remove(ra)
            a.dirty = removed = True
        if rb in b.links:
            b.links.remove(rb)
            b.dirty = removed = True
        return removed

    def clear_links(self, pin):
        """Remove every link of `pin` on both ends. Returns list of other pins."""
        others = []
        for ref in list(pin.links):
            other = self.resolve(ref)
            if other is not None:
                self.remove_link(pin, other)
            else:
                pin.links.remove(ref)
                pin.dirty = True
            others.append(ref)
        return others


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def validate(graph, max_each=25):
    """Return a list of problem strings (empty = OK)."""
    problems = []
    seen_names = {}
    for n in graph.nodes:
        if n.name in seen_names:
            problems.append("Duplicate node name '%s'." % n.name)
        seen_names[n.name] = n
    seen_ids = {}
    for n in graph.nodes:
        for p in n.pins:
            if p.pin_id in seen_ids:
                problems.append("Duplicate PinId %s on %s and %s."
                                % (p.pin_id, seen_ids[p.pin_id].label(), p.label()))
            else:
                seen_ids[p.pin_id] = p
    for n in graph.nodes:
        for p in n.pins:
            refs = [tuple(r) for r in p.links]
            if len(set(refs)) != len(refs):
                problems.append("%s lists the same link twice." % p.label())
            if p.single_link and len(p.links) > 1:
                problems.append("%s (%s) may hold only 1 link but has %d: %s"
                                % (p.label(), p.kind(), len(p.links),
                                   ", ".join(fmt_ref(graph, r) for r in p.links)))
            for ref in p.links:
                tn = graph.by_name.get(ref[0])
                if tn is None:
                    problems.append("%s links to missing node '%s'." % (p.label(), ref[0]))
                    continue
                tp = tn.pin_by_id(ref[1])
                if tp is None:
                    problems.append("%s links to missing pin %s on node '%s'." % (p.label(), ref[1], ref[0]))
                    continue
                if [n.name, p.pin_id] not in tp.links:
                    problems.append("One-way link: %s -> %s, but %s has no link back."
                                    % (p.label(), tp.label(), tp.label()))
                if tp.direction == p.direction:
                    problems.append("Link joins two %s pins: %s and %s."
                                    % ("output" if p.direction == "out" else "input", p.label(), tp.label()))
    # keep the output readable on very broken files
    if len(problems) > max_each * 4:
        extra = len(problems) - max_each * 4
        problems = problems[:max_each * 4] + ["... and %d more problems." % extra]
    return problems


def fmt_ref(graph, ref):
    p = graph.resolve(ref)
    return p.label() if p else "%s[%s]" % (ref[0], ref[1])


# --------------------------------------------------------------------------
# Paste handling
# --------------------------------------------------------------------------

def rename_nodes_in_text(graph, mapping):
    """Rename nodes inside a parsed paste graph (header + every reference).

    References are 'Name PINID' tokens after '(', ',' or '=' (LinkedTo,
    SubPins, ParentPin). Returns a new Graph.
    """
    if not mapping:
        return graph
    names = sorted(mapping, key=len, reverse=True)
    ref_re = re.compile(r"(?<=[(,=])(" + "|".join(re.escape(n) for n in names) + r")(?= [0-9A-Fa-f]{32}\b)")
    for n in graph.nodes:
        new_lines = []
        for i, line in enumerate(n.lines):
            if i == 0 and n.name in mapping:
                new = mapping[n.name]
                line = line.replace('Name="%s"' % n.name, 'Name="%s"' % new, 1)
                line = re.sub(r"(?<=[.:])" + re.escape(n.name) + r"(?=')", new, line)
            line = ref_re.sub(lambda m: mapping[m.group(1)], line)
            new_lines.append(line)
        n.lines = new_lines
    text = graph.newline.join(
        it if not isinstance(it, Node) else graph.newline.join(it.lines) for it in graph.items)
    return Graph(text, source=graph.source)


def find_existing(live, paste):
    """Match paste nodes to live nodes. Returns dict paste_name -> live_name.

    A paste node is 'already in live' when its NodeGuid is in live, or when
    all its PinIds are found on one live node (UE gives pasted nodes a new
    NodeGuid but keeps PinIds and names, so PinIds are the reliable key).
    """
    guid_map = {n.guid: n for n in live.nodes if n.guid}
    pin_owner = {}
    for n in live.nodes:
        for p in n.pins:
            pin_owner[p.pin_id] = n
    found = {}
    conflicts = []
    for pn in paste.nodes:
        if pn.guid and pn.guid in guid_map:
            found[pn.name] = guid_map[pn.guid].name
            continue
        if pn.pins:
            owners = set()
            missing = 0
            for p in pn.pins:
                o = pin_owner.get(p.pin_id)
                if o is None:
                    missing += 1
                else:
                    owners.add(o.name)
            if missing == 0 and len(owners) == 1:
                found[pn.name] = owners.pop()
            elif len(owners) == 1 and live.by_name[next(iter(owners))].cls == pn.cls \
                    and missing < len(pn.pins) - missing + 1:
                # the editor rebuilt some pins (e.g. hidden 'self') with new PinIds
                found[pn.name] = owners.pop()
            elif owners:
                conflicts.append("%s (PinIds partly in live node(s) %s)" % (pn.name, ", ".join(sorted(owners))))
    return found, conflicts


def unique_name(base, taken):
    i = 1
    while True:
        cand = "%s_m%d" % (base, i)
        if cand not in taken:
            return cand
        i += 1


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------

def load_manifest(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            m = json.load(f)
    except json.JSONDecodeError as e:
        raise MergeError("Manifest %s is not valid JSON: %s" % (path, e))
    if not isinstance(m, dict):
        raise MergeError("Manifest must be a JSON object.")
    base = os.path.dirname(os.path.abspath(path))
    pastes = []
    for i, p in enumerate(m.get("pastes", [])):
        if isinstance(p, str):
            p = {"file": p}
        if "file" not in p:
            raise MergeError("pastes[%d] has no 'file'." % i)
        fp = p["file"]
        full = fp if os.path.isabs(fp) else os.path.join(base, fp)
        off = p.get("offset")
        if off is not None:
            if isinstance(off, dict):
                off = [off.get("dx", 0), off.get("dy", 0)]
            if not (isinstance(off, list) and len(off) == 2):
                raise MergeError("pastes[%d].offset must be [dx, dy] or {\"dx\":..,\"dy\":..}." % i)
            off = [int(off[0]), int(off[1])]
        pastes.append({"file": fp, "path": full, "offset": off})
    rewires = []
    for i, r in enumerate(m.get("rewires", [])):
        if not isinstance(r, dict) or "from" not in r or "to" not in r:
            raise MergeError("rewires[%d] needs 'from' and 'to' (\"Node.Pin\")." % i)
        rewires.append({
            "from": r["from"], "to": r["to"],
            "replace": bool(r.get("replace", False)),
            "unlink": bool(r.get("unlink", False)),
            "note": r.get("note", ""),
        })
    return {"blueprint": m.get("blueprint"), "pastes": pastes, "rewires": rewires}


def check_blueprint(live, name, log):
    if not name:
        return
    paths = [n.export_path for n in live.nodes if n.export_path]
    if not paths:
        log("  note: live file has no ExportPath, so the blueprint name '%s' was not checked." % name)
        return
    needle = "/%s.%s:" % (name, name)
    if not any(needle in p for p in paths):
        sample = paths[0]
        raise MergeError("Manifest is for blueprint '%s' but the live file is from: %s" % (name, sample))


# --------------------------------------------------------------------------
# Merge
# --------------------------------------------------------------------------

def split_ref(text):
    """'Node.Pin' -> (scope, node, pin). scope is None, 'live' or 'new'."""
    scope = None
    t = text.strip()
    for pre in ("live:", "new:"):
        if t.startswith(pre):
            scope, t = pre[:-1], t[len(pre):]
    node, dot, pin = t.partition(".")
    if not dot or not node or not pin:
        raise MergeError("Bad pin reference '%s'. Use Node.Pin, e.g. CX_1.then" % text)
    return scope, node.strip(), pin.strip()


def merge(live, manifest, log=print):
    """Merge in place. Returns a summary dict. Raises MergeError on problems."""
    check_blueprint(live, manifest.get("blueprint"), log)
    before_problems = validate(live)
    if before_problems:
        raise MergeError("The live file already has problems (fix or re-export it first):\n  - "
                         + "\n  - ".join(before_problems))
    before = live.link_count()
    new_links = 0  # links added minus links removed
    live_names = set(live.by_name)
    paste_maps = []  # list of dicts: original paste name -> name in merged graph
    summary = {"pastes": [], "rewires": [], "renamed": {}}

    for pinfo in manifest["pastes"]:
        if not os.path.exists(pinfo["path"]):
            raise MergeError("Paste file not found: %s" % pinfo["path"])
        paste = Graph.load(pinfo["path"])
        if not paste.nodes:
            raise MergeError("Paste file has no nodes: %s" % pinfo["path"])
        problems = validate(paste)
        if problems:
            raise MergeError("Paste file %s has problems:\n  - %s" % (pinfo["file"], "\n  - ".join(problems)))
        found, conflicts = find_existing(live, paste)
        pinned = [n for n in paste.nodes if n.pins]
        n_found = sum(1 for n in pinned if n.name in found)
        if conflicts:
            raise MergeError("Paste %s overlaps the live graph in a strange way: %s"
                             % (pinfo["file"], "; ".join(conflicts)))
        if pinned and n_found == len(pinned):
            # already merged: map every node; pinless nodes (comments) map by name
            mp = {}
            for n in paste.nodes:
                mp[n.name] = found.get(n.name, n.name if n.name in live.by_name else None)
            mp = {k: v for k, v in mp.items() if v}
            paste_maps.append(mp)
            log("Paste %s: already in the live graph (%d nodes matched by NodeGuid/PinIds). Not added again."
                % (pinfo["file"], n_found))
            summary["pastes"].append({"file": pinfo["file"], "status": "already-merged", "nodes": n_found})
            continue
        if n_found:
            names = sorted(n for n in found)[:10]
            raise MergeError("Paste %s is PARTLY in the live graph already (%d of %d nodes, e.g. %s). "
                             "Delete those nodes in the editor and re-export, or remove them from the paste."
                             % (pinfo["file"], n_found, len(pinned), ", ".join(names)))
        # new paste: rename collisions
        taken = set(live_names)
        for m in paste_maps:
            taken.update(m.values())
        taken.update(n.name for n in paste.nodes)
        mapping = {}
        for n in paste.nodes:
            if n.name in live_names or any(n.name in m.values() for m in paste_maps):
                new = unique_name(n.name, taken)
                taken.add(new)
                mapping[n.name] = new
        if mapping:
            paste = rename_nodes_in_text(paste, mapping)
            for old, new in mapping.items():
                log("  renamed paste node %s -> %s (name already used in live)" % (old, new))
            summary["renamed"].update(mapping)
        # position
        off = pinfo["offset"]
        if off is None:
            lb = live.bbox()
            pb = paste.bbox()
            if lb is None:
                off = [0, 0]
            else:
                off = [lb[0] - pb[0], lb[3] + DEFAULT_GAP_Y - pb[1]]
        for n in paste.nodes:
            n.set_pos("X", n.pos("X") + off[0])
            n.set_pos("Y", n.pos("Y") + off[1])
        paste_links = paste.link_count()
        live.add_nodes(paste.nodes)
        live_names.update(n.name for n in paste.nodes)
        new_links += paste_links // 2
        mp = {orig: mapping.get(orig, orig) for orig in [mapping_inv(mapping, n.name) for n in paste.nodes]}
        paste_maps.append(mp)
        log("Paste %s: added %d nodes, %d links, offset dx=%d dy=%d."
            % (pinfo["file"], len(paste.nodes), paste_links // 2, off[0], off[1]))
        summary["pastes"].append({"file": pinfo["file"], "status": "added", "nodes": len(paste.nodes),
                                  "links": paste_links // 2, "offset": off, "renamed": mapping})

    # names of paste nodes (original -> merged), for rewires
    def resolve_node(scope, name):
        hits = set(m[name] for m in paste_maps if name in m)
        if scope == "live":
            return name
        if scope == "new":
            if not hits:
                raise MergeError("'new:%s' is not a node of any paste." % name)
            if len(hits) > 1:
                raise MergeError("'new:%s' is in more than one paste." % name)
            return hits.pop()
        if hits:
            target = hits.pop() if len(hits) == 1 else None
            if target is None:
                raise MergeError("Node name '%s' is in more than one paste; use the merged name." % name)
            if target != name and name in live.by_name:
                raise MergeError("Node name '%s' is both a live node and a (renamed) paste node. "
                                 "Write 'live:%s.Pin' or 'new:%s.Pin'." % (name, name, name))
            return target
        return name

    for r in manifest["rewires"]:
        fs, fnode, fpin = split_ref(r["from"])
        ts, tnode, tpin = split_ref(r["to"])
        a = live.find_pin(resolve_node(fs, fnode), fpin)
        b = live.find_pin(resolve_node(ts, tnode), tpin)
        if a.direction == "in" and b.direction == "out":
            a, b = b, a
            log("  note: %s -> %s was written backwards; using %s -> %s"
                % (r["from"], r["to"], a.label(), b.label()))
        if a.direction == b.direction:
            raise MergeError("Rewire %s -> %s joins two %s pins." % (r["from"], r["to"],
                             "output" if a.direction == "out" else "input"))
        if (a.category == "exec") != (b.category == "exec"):
            raise MergeError("Rewire %s -> %s joins an exec pin to a data pin." % (r["from"], r["to"]))
        entry = {"from": a.label(), "to": b.label(), "removed": [], "status": ""}
        if r["unlink"]:
            if live.remove_link(a, b):
                new_links -= 1
                entry["status"] = "unlinked"
            else:
                entry["status"] = "was not linked (nothing to do)"
            log("Rewire %s -x- %s: %s" % (a.label(), b.label(), entry["status"]))
            summary["rewires"].append(entry)
            continue
        if live.has_link(a, b):
            entry["status"] = "already linked (nothing to do)"
            # with replace, also drop other links on the single-link ends
            if r["replace"]:
                for pin, other in ((a, b), (b, a)):
                    if pin.single_link:
                        for ref in list(pin.links):
                            if ref != [other.node.name, other.pin_id]:
                                op = live.resolve(ref)
                                if op is not None and live.remove_link(pin, op):
                                    new_links -= 1
                                    entry["removed"].append("%s -- %s" % (pin.label(), op.label()))
            log("Rewire %s -> %s: %s" % (a.label(), b.label(), entry["status"]))
            summary["rewires"].append(entry)
            continue
        for pin in (a, b):
            if pin.single_link and pin.links:
                if not r["replace"]:
                    raise MergeError("Rewire %s -> %s: %s (%s) already has a link to %s and can hold only one. "
                                     "Set \"replace\": true to remove the old link."
                                     % (r["from"], r["to"], pin.label(), pin.kind(),
                                        ", ".join(fmt_ref(live, x) for x in pin.links)))
                for ref in list(pin.links):
                    op = live.resolve(ref)
                    label = fmt_ref(live, ref)
                    if op is not None:
                        live.remove_link(pin, op)
                    else:
                        pin.links.remove(ref)
                        pin.dirty = True
                    new_links -= 1
                    entry["removed"].append("%s -- %s" % (pin.label(), label))
        live.add_link(a, b)
        new_links += 1
        entry["status"] = "linked" + (" (removed: %s)" % "; ".join(entry["removed"]) if entry["removed"] else "")
        log("Rewire %s -> %s: %s" % (a.label(), b.label(), entry["status"]))
        summary["rewires"].append(entry)

    after = live.link_count()
    problems = validate(live)
    delta = after - before
    summary.update({"links_before": before, "links_after": after, "delta": delta,
                    "net_new_links": new_links})
    log("LinkedTo entries: before %d, after %d, delta %+d (expected %+d = 2 x %d net new links)"
        % (before, after, delta, 2 * new_links, new_links))
    if delta != 2 * new_links:
        problems.append("Link count delta %+d does not match 2 x net new links (%+d)." % (delta, 2 * new_links))
    if problems:
        raise MergeError("Validation failed after merge (nothing written):\n  - " + "\n  - ".join(problems))
    return summary


def mapping_inv(mapping, merged_name):
    for k, v in mapping.items():
        if v == merged_name:
            return k
    return merged_name


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

def describe_node(graph, node):
    out = ["%s  [%s]  pos (%d, %d)" % (node.name, node.short_class(), node.pos("X"), node.pos("Y"))]
    for p in node.pins:
        if not p.links:
            continue
        arrow = "->" if p.direction == "out" else "<-"
        targets = ", ".join(fmt_ref(graph, r) for r in p.links)
        out.append("    %-22s (%s) %s %s" % (p.name, p.kind(), arrow, targets))
    if len(out) == 1:
        out.append("    (no links)")
    return out


def cmd_check(args):
    try:
        g = Graph.load(args.file)
    except (MergeError, OSError) as e:
        print("ERROR: %s" % e)
        return 1
    rc = 0
    for name in args.nodes:
        n = g.by_name.get(name)
        if n is None:
            print("Node '%s' not found." % name)
            rc = 1
            continue
        print("\n".join(describe_node(g, n)))
    print("%s: %d nodes, %d pins, %d LinkedTo entries (%d links)"
          % (args.file, len(g.nodes), sum(len(n.pins) for n in g.nodes), g.link_count(), g.link_count() // 2))
    problems = validate(g)
    if problems:
        print("Validation: %d problem(s)" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("Validation: OK")
    return rc


# --------------------------------------------------------------------------
# merge command
# --------------------------------------------------------------------------

def cmd_merge(args):
    try:
        manifest = load_manifest(args.manifest)
        live = Graph.load(args.live)
        print("Live: %s (%d nodes, %d LinkedTo entries)" % (args.live, len(live.nodes), live.link_count()))
        merge(live, manifest)
    except (MergeError, OSError) as e:
        print("ERROR: %s" % e)
        print("Nothing was written.")
        return 1
    print("Validation: OK")
    if args.dry_run:
        print("Dry run: not writing %s" % args.out)
        return 0
    write_text(args.out, live.render())
    print("Wrote %s" % args.out)
    return 0


# --------------------------------------------------------------------------
# manifest-from-readme
# --------------------------------------------------------------------------

ENDPOINT_RE = re.compile(r"(?<![\w.])([A-Za-z_]\w*)[ \t]*\.[ \t]?([A-Za-z_]\w*)")
PASTE_FILE_RE = re.compile(r"[`\"]?([\w./-]+\.(?:txt|t3d))[`\"]?")
REPLACE_HINTS = ("replac", "used to", "they go to", "old link", "instead of its", "go to #", "currently go")


def clean_md(text):
    t = text.replace("**", "").replace("`", "").replace("…", "")
    # drop parenthesised remarks, repeat for nesting
    for _ in range(3):
        t = re.sub(r"\([^()]*\)", " ", t)
    return t


def endpoints(text):
    return ["%s.%s" % m for m in ENDPOINT_RE.findall(clean_md(text))]


def readme_rewires(lines):
    """Yield (from, to, replace, source_line, line_no) from README lines."""
    table_cols = None
    for i, raw in enumerate(lines):
        line = raw.strip()
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        hint_text = (raw + " " + nxt).lower()
        replace = any(h in hint_text for h in REPLACE_HINTS)
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            low = [c.lower().strip("* ") for c in cells]
            if "from" in low and "to" in low:
                table_cols = (low.index("from"), low.index("to"))
                continue
            if table_cols and not set(line) <= set("|-: "):
                fi, ti = table_cols
                if max(fi, ti) < len(cells):
                    rep = any(h in raw.lower() for h in REPLACE_HINTS)
                    src = endpoints(cells[fi])
                    dst = endpoints(cells[ti])
                    for s in src:
                        if dst:
                            yield s, dst[0], rep, line, i + 1
            continue
        table_cols = None
        if "->" not in line:
            continue
        parts = line.split("->")
        for left, right in zip(parts, parts[1:]):
            src = endpoints(left)
            dst = endpoints(right)
            if not src or not dst:
                continue
            # a chain "A.x -> B.y -> C.z": only the last endpoint on the left matters
            # unless joined by "and"
            if " and " not in clean_md(left):
                src = src[-1:]
            for s in src:
                yield s, dst[0], replace, line, i + 1


def cmd_manifest_from_readme(args):
    try:
        lines = read_text(args.readme).replace("\r\n", "\n").split("\n")
    except OSError as e:
        print("ERROR: %s" % e)
        return 1
    groups = []  # each: {"paste": name or None, "blueprint": str or None, "rewires": []}
    cur = {"paste": None, "blueprint": None, "rewires": []}
    groups.append(cur)
    rewire_iter = {}
    for f, t, rep, src, ln in readme_rewires(lines):
        rewire_iter.setdefault(ln, []).append((f, t, rep, src))
    for i, raw in enumerate(lines, 1):
        low = raw.lower()
        if "paste" in low and not raw.strip().startswith("|"):
            files = [m for m in PASTE_FILE_RE.findall(raw) if not m.startswith("../")]
            if files:
                no_files = PASTE_FILE_RE.sub(" ", raw)
                bp = re.findall(r"\b(BPC?_[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*)", no_files)
                cur = {"paste": files[0], "blueprint": bp[0] if bp else None, "rewires": []}
                groups.append(cur)
        for f, t, rep, src in rewire_iter.get(i, []):
            cur["rewires"].append({"from": f, "to": t, "replace": rep,
                                   "note": "README line %d: %s" % (i, src[:160])})
    drafts = []
    readme_dir = os.path.dirname(os.path.abspath(args.readme))
    for g in groups:
        if not g["paste"] and not g["rewires"]:
            continue
        d = {"blueprint": g["blueprint"] or "TODO_BP_NAME",
             "pastes": [{"file": g["paste"]}] if g["paste"] else [],
             "rewires": g["rewires"],
             "_draft": "Made by manifest-from-readme. CHECK every rewire, the replace flags and the "
                       "blueprint name, then delete this line."}
        if g["paste"] and not os.path.exists(os.path.join(readme_dir, g["paste"])):
            d["_warning"] = "paste file %s is not next to the README" % g["paste"]
        drafts.append(d)
    if not drafts:
        print("No 'X.pin -> Y.pin' lines or paste files found.")
        return 1
    out = drafts[0] if len(drafts) == 1 else drafts
    text = json.dumps(out, indent=2)
    if args.out:
        if len(drafts) == 1:
            write_text(args.out, text + "\n")
            print("Wrote %s" % args.out)
        else:
            stem, ext = os.path.splitext(args.out)
            for d in drafts:
                tag = os.path.splitext(os.path.basename(d["pastes"][0]["file"]))[0] if d["pastes"] else "no_paste"
                p = "%s.%s%s" % (stem, tag, ext or ".json")
                write_text(p, json.dumps(d, indent=2) + "\n")
                print("Wrote %s (%d rewires)" % (p, len(d["rewires"])))
    else:
        print(text)
    return 0


# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="applyall.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    m = sub.add_parser("merge", help="merge paste files + rewires into a live export")
    m.add_argument("--live", required=True)
    m.add_argument("--manifest", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--dry-run", action="store_true", help="validate only, do not write")
    c = sub.add_parser("check", help="print links of nodes and validate a T3D file")
    c.add_argument("file")
    c.add_argument("nodes", nargs="*")
    r = sub.add_parser("manifest-from-readme", help="draft a manifest from README arrow lines")
    r.add_argument("readme")
    r.add_argument("--out")
    args = ap.parse_args(argv)
    if args.cmd == "merge":
        return cmd_merge(args)
    if args.cmd == "check":
        return cmd_check(args)
    if args.cmd == "manifest-from-readme":
        return cmd_manifest_from_readme(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
