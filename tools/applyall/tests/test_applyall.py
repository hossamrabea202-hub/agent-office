"""Unit tests for applyall.py. Run from the applyall folder:

    python3 -m unittest -v
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import applyall as A  # noqa: E402

TAIL = ("PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,"
        "bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)")


def pid(n):
    """Deterministic 32-hex PinId from an int."""
    return "%032X" % n


def pin(pin_id, name, out=False, cat="exec", links=(), default=None):
    s = '   CustomProperties Pin (PinId=%s,PinName="%s",' % (pin_id, name)
    if out:
        s += 'Direction="EGPD_Output",'
    s += 'PinType.PinCategory="%s",PinType.PinSubCategory="",PinType.PinSubCategoryObject=None,' % cat
    if default is not None:
        s += 'DefaultValue="%s",' % default
    if links:
        s += "LinkedTo=(" + "".join("%s %s," % l for l in links) + "),"
    return s + TAIL


def node(name, pins, x=0, y=0, guid=None, cls="/Script/BlueprintGraph.K2Node_CallFunction", export=None):
    head = 'Begin Object Class=%s Name="%s"' % (cls, name)
    if export:
        head += ' ExportPath="%s"' % export
    lines = [head, "   NodePosX=%d" % x, "   NodePosY=%d" % y,
             "   NodeGuid=%s" % (guid or pid(abs(hash(name)) % (16 ** 12)))]
    lines += pins
    lines.append("End Object")
    return "\n".join(lines)


def doc(*nodes, crlf=False):
    t = "\n".join(nodes) + "\n"
    return t.replace("\n", "\r\n") if crlf else t


# A tiny live graph: Ev.then -> Print.execute ; Ev.Size -> Conv.In
def live_text(crlf=False, export=False):
    ep = ("/Script/BlueprintGraph.K2Node_Event'/Game/UI/BP_Test.BP_Test:EventGraph.%s'" if export else None)
    return doc(
        node("Ev", [pin(pid(1), "then", out=True, links=[("Print", pid(2))]),
                    pin(pid(10), "Size", out=True, cat="int", links=[("Conv", pid(11))])],
             x=0, y=0, guid=pid(1001), export=ep % "Ev" if ep else None),
        node("Print", [pin(pid(2), "execute", links=[("Ev", pid(1))]),
                       pin(pid(3), "then", out=True),
                       pin(pid(4), "InString", cat="string", default="a, (b), \\\"c\\\"")],
             x=400, y=100, guid=pid(1002), export=ep % "Print" if ep else None),
        node("Conv", [pin(pid(11), "In", cat="int", links=[("Ev", pid(10))]),
                      pin(pid(12), "Ret", out=True, cat="real")],
             x=400, y=300, guid=pid(1003), export=ep % "Conv" if ep else None),
        crlf=crlf)


# A paste: Seq(execute, then_0) -> Draw(execute); Size input on Draw
def paste_text(seq_name="Seq", crlf=False):
    return doc(
        node(seq_name, [pin(pid(21), "execute"),
                        pin(pid(22), "then_0", out=True, links=[("Draw", pid(23))])],
             x=0, y=0, guid=pid(2001), cls="/Script/BlueprintGraph.K2Node_ExecutionSequence"),
        node("Draw", [pin(pid(23), "execute", links=[(seq_name, pid(22))]),
                      pin(pid(24), "W", cat="int")],
             x=300, y=50, guid=pid(2002)),
        crlf=crlf)


class Tmp(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="applyall_test_")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, name, text):
        p = os.path.join(self.dir, name)
        with open(p, "w", newline="") as f:
            f.write(text)
        return p

    def manifest(self, rewires=(), pastes=("paste.txt",), **extra):
        m = {"blueprint": "BP_Test", "pastes": list(pastes), "rewires": list(rewires)}
        m.update(extra)
        return self.write("manifest.json", json.dumps(m))

    def run_merge(self, live, manifest, out="out.t3d"):
        outp = os.path.join(self.dir, out)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = A.main(["merge", "--live", live, "--manifest", manifest, "--out", outp])
        return rc, buf.getvalue(), outp


class ParseTests(Tmp):
    def test_roundtrip_identical(self):
        for crlf in (False, True):
            t = live_text(crlf=crlf)
            g = A.Graph(t)
            self.assertEqual(g.render(), t)
            self.assertEqual(len(g.nodes), 3)
            self.assertEqual(g.link_count(), 4)

    def test_quoted_default_with_commas_and_parens(self):
        g = A.Graph(live_text())
        p = g.by_name["Print"].pins[2]
        self.assertEqual(p.name, "InString")
        self.assertEqual(p.links, [])
        self.assertEqual(A.validate(g), [])

    def test_insert_linkedto_before_persistentguid_and_remove(self):
        g = A.Graph(live_text())
        a = g.find_pin("Print", "then")
        b = g.find_pin("Conv", "In")  # wrong types but fine for text test
        g.add_link(a, b)
        line = a.render()
        self.assertIn("LinkedTo=(Conv %s,),PersistentGuid=" % pid(11), line)
        g.remove_link(a, b)
        self.assertNotIn("LinkedTo", a.render())

    def test_single_link_rule_kinds(self):
        g = A.Graph(live_text())
        self.assertTrue(g.find_pin("Ev", "then").single_link)      # exec out
        self.assertFalse(g.find_pin("Print", "execute").single_link)  # exec in
        self.assertTrue(g.find_pin("Conv", "In").single_link)      # data in
        self.assertFalse(g.find_pin("Ev", "Size").single_link)     # data out


class ValidateTests(Tmp):
    def test_ok(self):
        self.assertEqual(A.validate(A.Graph(live_text())), [])

    def test_one_way_link(self):
        t = live_text().replace('LinkedTo=(Ev %s,),' % pid(1), "")
        probs = A.validate(A.Graph(t))
        self.assertTrue(any("One-way" in p for p in probs), probs)

    def test_missing_target(self):
        t = live_text().replace("Print %s" % pid(2), "Nope %s" % pid(2))
        probs = A.validate(A.Graph(t))
        self.assertTrue(any("missing node 'Nope'" in p for p in probs), probs)

    def test_duplicate_pinid(self):
        t = live_text().replace("PinId=%s" % pid(12), "PinId=%s" % pid(3))
        probs = A.validate(A.Graph(t))
        self.assertTrue(any("Duplicate PinId" in p for p in probs), probs)

    def test_single_link_violation(self):
        g2 = A.Graph(live_text())
        ev = g2.find_pin("Ev", "then")
        ev.links.append(["Conv", pid(11)])
        probs = A.validate(g2)
        self.assertTrue(any("may hold only 1 link" in p for p in probs), probs)


class MergeTests(Tmp):
    def test_add_paste_default_position_and_rewires(self):
        live = self.write("live.t3d", live_text(crlf=True))
        self.write("paste.txt", paste_text(crlf=True))
        man = self.manifest(rewires=[
            {"from": "Ev.then", "to": "Seq.execute", "replace": True},
            {"from": "Ev.Size", "to": "Draw.W"},
        ])
        rc, out, outp = self.run_merge(live, man)
        self.assertEqual(rc, 0, out)
        self.assertIn("delta +4", out)  # net new links: 1 (paste) + 2 (rewires) - 1 (replaced) = 2
        g = A.Graph.load(outp)
        self.assertEqual(A.validate(g), [])
        self.assertEqual(g.find_pin("Ev", "then").links, [["Seq", pid(21)]])
        self.assertEqual(g.find_pin("Print", "execute").links, [])
        self.assertIn(["Draw", pid(24)], g.find_pin("Ev", "Size").links)
        # placed below live bbox (live max y = 300)
        self.assertEqual(g.by_name["Seq"].pos("Y"), 300 + A.DEFAULT_GAP_Y)
        self.assertEqual(g.by_name["Seq"].pos("X"), 0)
        self.assertEqual(g.by_name["Draw"].pos("X"), 300)
        with open(outp, "rb") as f:
            self.assertIn(b"\r\n", f.read())

    def test_offset_from_manifest(self):
        live = self.write("live.t3d", live_text())
        self.write("paste.txt", paste_text())
        man = self.manifest(pastes=[{"file": "paste.txt", "offset": [1000, -50]}])
        rc, out, outp = self.run_merge(live, man)
        self.assertEqual(rc, 0, out)
        g = A.Graph.load(outp)
        self.assertEqual((g.by_name["Draw"].pos("X"), g.by_name["Draw"].pos("Y")), (1300, 0))

    def test_replace_false_on_used_exec_output_fails_and_writes_nothing(self):
        live = self.write("live.t3d", live_text())
        self.write("paste.txt", paste_text())
        man = self.manifest(rewires=[{"from": "Ev.then", "to": "Seq.execute"}])
        rc, out, outp = self.run_merge(live, man)
        self.assertEqual(rc, 1)
        self.assertIn('"replace": true', out)
        self.assertFalse(os.path.exists(outp))

    def test_name_collision_renamed(self):
        live = self.write("live.t3d", live_text())
        # paste node named "Print" collides with live "Print"
        self.write("paste.txt", paste_text(seq_name="Print"))
        man = self.manifest(rewires=[{"from": "Ev.then", "to": "new:Print.execute", "replace": True}])
        rc, out, outp = self.run_merge(live, man)
        self.assertEqual(rc, 0, out)
        self.assertIn("renamed paste node Print -> Print_m1", out)
        g = A.Graph.load(outp)
        self.assertEqual(A.validate(g), [])
        self.assertIn("Print_m1", g.by_name)
        self.assertEqual(g.find_pin("Draw", "execute").links, [["Print_m1", pid(22)]])
        self.assertEqual(g.find_pin("Ev", "then").links, [["Print_m1", pid(21)]])

    def test_ambiguous_name_needs_prefix(self):
        live = self.write("live.t3d", live_text())
        self.write("paste.txt", paste_text(seq_name="Print"))
        man = self.manifest(rewires=[{"from": "Ev.then", "to": "Print.execute", "replace": True}])
        rc, out, _ = self.run_merge(live, man)
        self.assertEqual(rc, 1)
        self.assertIn("live:Print", out)

    def test_idempotent_by_pinids_even_with_new_guids(self):
        live = self.write("live.t3d", live_text())
        self.write("paste.txt", paste_text())
        man = self.manifest(rewires=[{"from": "Ev.then", "to": "Seq.execute", "replace": True}])
        rc, out, out1 = self.run_merge(live, man, "m1.t3d")
        self.assertEqual(rc, 0, out)
        # simulate an editor round trip: UE gives every node a new NodeGuid
        with open(out1) as f:
            t = f.read()
        t = t.replace("NodeGuid=%s" % pid(2001), "NodeGuid=%s" % pid(9001))
        t = t.replace("NodeGuid=%s" % pid(2002), "NodeGuid=%s" % pid(9002))
        live2 = self.write("live2.t3d", t)
        rc, out, out2 = self.run_merge(live2, man, "m2.t3d")
        self.assertEqual(rc, 0, out)
        self.assertIn("already in the live graph", out)
        self.assertIn("already linked", out)
        with open(out2) as f:
            self.assertEqual(f.read(), t)

    def test_partial_paste_is_an_error(self):
        live_nodes = live_text() + paste_text().split("End Object")[0] + "End Object\n"
        # live now has Seq but no Draw; Seq.then_0 points to Draw -> fix it to keep live valid
        live_nodes = live_nodes.replace("LinkedTo=(Draw %s,)," % pid(23), "")
        live = self.write("live.t3d", live_nodes)
        self.write("paste.txt", paste_text())
        rc, out, _ = self.run_merge(live, self.manifest())
        self.assertEqual(rc, 1)
        self.assertIn("PARTLY", out)

    def test_blueprint_mismatch(self):
        live = self.write("live.t3d", live_text(export=True))
        self.write("paste.txt", paste_text())
        rc, out, _ = self.run_merge(live, self.manifest(blueprint="BP_Other"))
        self.assertEqual(rc, 1)
        self.assertIn("BP_Other", out)
        rc, out, _ = self.run_merge(live, self.manifest())
        self.assertEqual(rc, 0, out)

    def test_broken_paste_rejected(self):
        live = self.write("live.t3d", live_text())
        self.write("paste.txt", paste_text().replace("LinkedTo=(Seq %s,)," % pid(22), ""))
        rc, out, _ = self.run_merge(live, self.manifest())
        self.assertEqual(rc, 1)
        self.assertIn("One-way", out)

    def test_unlink(self):
        live = self.write("live.t3d", live_text())
        man = self.manifest(pastes=[], rewires=[{"from": "Ev.then", "to": "Print.execute", "unlink": True}])
        rc, out, outp = self.run_merge(live, man)
        self.assertEqual(rc, 0, out)
        g = A.Graph.load(outp)
        self.assertEqual(g.link_count(), 2)

    def test_backwards_rewire_is_swapped(self):
        live = self.write("live.t3d", live_text())
        self.write("paste.txt", paste_text())
        man = self.manifest(rewires=[{"from": "Seq.execute", "to": "Ev.then", "replace": True}])
        rc, out, outp = self.run_merge(live, man)
        self.assertEqual(rc, 0, out)
        self.assertIn("backwards", out)


class CheckTests(Tmp):
    def test_check_prints_links(self):
        p = self.write("g.t3d", live_text())
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = A.main(["check", p, "Ev"])
        self.assertEqual(rc, 0)
        self.assertIn("then", buf.getvalue())
        self.assertIn("-> Print.execute", buf.getvalue())
        self.assertIn("Validation: OK", buf.getvalue())

    def test_check_fails_on_broken(self):
        p = self.write("g.t3d", live_text().replace('LinkedTo=(Ev %s,),' % pid(1), ""))
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = A.main(["check", p])
        self.assertEqual(rc, 1)


class ReadmeTests(Tmp):
    README = "\n".join([
        "4. **BP_NoticeHUD:** paste `Notice_graph.txt` into the EventGraph, then make rewires:",
        "",
        "   | # | From | To |",
        "   |---|---|---|",
        "   | 1 | `DrawText` CX_208 .then **and** Branch CX_138 .else (they go to NoticeIn now) | **InfIn**.execute |",
        "   | 3 | Event ReceiveDrawHUD CX_1 .SizeX | **InfSizeX**.InInt |",
        "",
        "5. **Soldier hook** (BP_SoldierSword EventGraph): paste `Hook_graph.txt` near the death branch.",
        "   - `CX_447` (Set Relative Location, target State).then -> **FallIn**.execute (the Sequence).",
        "     This replaces its old link to CX_549.",
        "   - **FallOut**.then_0 -> `CX_549` (Set Visibility).execute.",
        "Get Player Character -> Cast to BP_Hero -> `Infection`.",
    ])

    def test_draft(self):
        p = self.write("README.md", self.README)
        self.write("Notice_graph.txt", "")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = A.main(["manifest-from-readme", p])
        self.assertEqual(rc, 0)
        drafts = json.loads(buf.getvalue())
        self.assertEqual(len(drafts), 2)
        n, s = drafts
        self.assertEqual(n["blueprint"], "BP_NoticeHUD")
        self.assertEqual([(r["from"], r["to"], r["replace"]) for r in n["rewires"]], [
            ("CX_208.then", "InfIn.execute", True),
            ("CX_138.else", "InfIn.execute", True),
            ("CX_1.SizeX", "InfSizeX.InInt", False)])
        self.assertEqual(s["blueprint"], "BP_SoldierSword")
        self.assertEqual([(r["from"], r["to"], r["replace"]) for r in s["rewires"]], [
            ("CX_447.then", "FallIn.execute", True),
            ("FallOut.then_0", "CX_549.execute", False)])
        self.assertIn("_warning", s)  # Hook_graph.txt is missing


REAL_EXP = "/mnt/user-data/uploads/_claude/exp"
REAL_MANIFEST = os.path.join(os.path.dirname(HERE), "examples", "infection73_noticehud.json")


@unittest.skipUnless(os.path.exists(os.path.join(REAL_EXP, "nh3.t3d")), "real exports not present")
class RealNoticeHUDTest(Tmp):
    """nh2 (paste already in, no rewires) + manifest must give nh3's links."""

    def test_nh2_to_nh3(self):
        rc, out, outp = self.run_merge(os.path.join(REAL_EXP, "nh2.t3d"), REAL_MANIFEST)
        self.assertEqual(rc, 0, out)
        self.assertIn("already in the live graph", out)
        got = A.Graph.load(outp)
        want = A.Graph.load(os.path.join(REAL_EXP, "nh3.t3d"))
        self.assertEqual(got.link_count(), 1616)

        def links(g):
            return {(n.name, p.pin_id): sorted(map(tuple, p.links)) for n in g.nodes for p in n.pins}
        self.assertEqual(links(got), links(want))
        # second run changes nothing
        rc, out, out2 = self.run_merge(outp, REAL_MANIFEST, "again.t3d")
        self.assertEqual(rc, 0, out)
        with open(outp, "rb") as a, open(out2, "rb") as b:
            self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
