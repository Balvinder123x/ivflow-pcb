"""Stage 4: build the IVFlow board from the schematic.

Board outline, 4 M2 mounting holes, every footprint placed from the PLACE table,
connector labels, "IVFlow v1", JLCPCB design rules and net classes. No tracks yet.

Footprints, values, nets and the schematic links (symbol UUIDs) come from KiCad's own
netlist export of the schematic, so the board matches the schematic exactly (checked
by `kicad-cli pcb drc --schematic-parity`).

Run with KiCad's bundled Python, with KiCad closed:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts\\make_board.py [--out DIR] [--force]

Refuses to overwrite a board that already has footprints unless --force is given
(once the board is edited in KiCad, make targeted edits instead).
"""
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import pcbnew

import silk_labels

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(ROOT, "ivflow")
PCB = os.path.join(OUT, "ivflow.kicad_pcb")
SCH = os.path.join(OUT, "ivflow.kicad_sch")
PRO = os.path.join(OUT, "ivflow.kicad_pro")
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
FP_ROOT = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
FORCE = "--force" in sys.argv

# ---------------------------------------------------------------- board
ORIGIN = (100.0, 100.0)      # page position of the board's top-left corner (mm)
W, H = 46.0, 41.5            # board size (mm)
HOLE_INSET = 3.2             # M2 hole centre from both edges
HOLE_FP = "MountingHole:MountingHole_2.2mm_M2"

# ref: (x, y, rotation, connector label side, reference text side), mm from the board's
# top-left corner. Reference side: "above"/"below"/"left"/"right", or None = library default.
# Parts listed in BOTTOM are mounted on the bottom side (same x/y, seen from the top).
# U1 is turned 180 degrees: antenna at the top edge, USB-C pointing down into the board.
# Its left socket row (x 15.38) is then GPIO0-4/3V3/GND/5V from the top, the right row
# (x 30.62) GPIO21/20/10/9/8/7/6/5.
PLACE = {
    "U1": (23.0, 11.56, 180, None, None),
    # Top, left edge: LDR strip. Its R/C filters sit under the module (it stands ~8.5 mm
    # up on its sockets), right next to GPIO0/1/3/4, with the 3V3 bulk capacitor C4.
    "J2": (4.45, 8.9, 270, "right", None),
    "R11": (21.2, 8.2, 0, None, "above"), "C11": (25.5, 8.2, 0, None, "above"),
    "R12": (21.2, 11.6, 0, None, "above"), "C12": (25.5, 11.6, 0, None, "above"),
    "R13": (21.2, 15.0, 0, None, "above"), "C13": (25.5, 15.0, 0, None, "above"),
    "R14": (21.2, 18.4, 0, None, "above"), "C14": (25.5, 18.4, 0, None, "above"),
    "C4": (23.35, 21.8, 0, None, "left"),
    # Top, right edge: expansion and OLED headers
    "J5": (43.7, 7.7, 0, "left", None),
    "J4": (43.7, 21.7, 0, "left", None),
    # Top, row below the module: charger, power switch
    "J9": (3.475, 25.975, 0, "below-right", None),
    "J6": (26.5, 25.975, 0, "below", None),
    # Top, bottom edge: battery, LED, buzzer, button
    "J1": (8.375, 37.675, 0, "above", None),
    "J3": (16.325, 37.075, 0, "above", None),
    "J7": (25.275, 37.075, 0, "above", None),
    "J8": (34.225, 37.075, 0, "above", None),
    # Bottom, strip between the two connector rows: power path + 3.3 V regulator
    "D1": (8.0, 31.8, 0, None, "above"), "Q1": (16.0, 31.8, 0, None, "above"),
    "R1": (21.5, 31.8, 0, None, "above"), "U3": (27.0, 31.8, 0, None, "above"),
    "C1": (32.5, 31.8, 0, None, "above"), "C2": (37.0, 31.8, 0, None, "above"),
    "C3": (41.5, 31.8, 0, None, "above"),
    # Bottom, under the module: battery sense (divider next to GPIO2, switch next to GPIO7)
    "R2": (20.0, 8.5, 0, None, "above"), "C5": (20.0, 11.9, 0, None, "above"),
    "R3": (20.0, 15.3, 0, None, "above"), "Q2": (26.0, 9.5, 0, None, "above"),
    "R4": (26.0, 14.4, 0, None, "above"), "R5": (26.0, 17.8, 0, None, "above"),
    # Bottom, right of the module: button cap, buzzer driver, LED resistor
    "C6": (35.5, 8.0, 0, None, "above"), "R21": (35.5, 12.0, 0, None, "above"),
    "R22": (35.5, 15.4, 0, None, "above"), "Q3": (36.0, 19.5, 0, None, "above"),
    "D3": (36.0, 24.0, 0, None, "above"), "R20": (35.5, 28.0, 0, None, "above"),
}
BOTTOM = {"D1", "Q1", "R1", "U3", "C1", "C2", "C3", "R2", "C5", "R3", "Q2", "R4", "R5",
          "C6", "R21", "R22", "Q3", "D3", "R20"}
SILK_TEXT = [("IVFlow v1", 23.0, 21.2, 1.2, pcbnew.B_SilkS)]   # (text, x, y, height, layer)

# ---------------------------------------------------------------- rules (JLCPCB 2-layer)
RULES = {
    "min_clearance": 0.127,             # JLCPCB min trace spacing, 1-2 layers
    "min_track_width": 0.127,           # JLCPCB min trace width, 1-2 layers
    "min_via_diameter": 0.5,
    "min_through_hole_diameter": 0.3,   # JLCPCB min via drill, 1-2 layers
    "min_via_annular_width": 0.1,
    "min_copper_edge_clearance": 0.3,   # JLCPCB 0.2 trace-to-outline, plus margin
    "min_hole_to_hole": 0.5,
    "min_text_height": 1.0,             # silkscreen
    "min_text_thickness": 0.15,
    "min_resolved_spokes": 1,           # a few crowded THT GND pins get 1 spoke; they also join the other layer's pour
}
NETCLASSES = {   # name: (track, clearance, via diameter, via drill)
    "Default": (0.25, 0.2, 0.6, 0.3),
    "Power": (0.5, 0.2, 0.6, 0.3),
}
POWER_NETS = ["VBUS", "VBAT_P", "VSYS", "VSYS_SW", "+3V3", "BATT+", "BATT-"]


def mm(v):
    return pcbnew.FromMM(v)


def at(x, y):
    return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))


# ---------------------------------------------------------------- netlist
def read_netlist():
    """Components and nets from the schematic, via kicad-cli's KiCad XML netlist."""
    xml_path = os.path.join(tempfile.mkdtemp(), "ivflow.xml")
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", xml_path, SCH],
                   check=True, capture_output=True)
    root = ET.parse(xml_path).getroot()
    comps = []
    for c in root.iter("comp"):
        props = {p.get("name"): p.get("value") for p in c.iter("property")}
        fields = {f.get("name"): (f.text or "") for f in c.iter("field")}
        comps.append(dict(ref=c.get("ref"), value=c.findtext("value"), footprint=c.findtext("footprint") or "",
                          uuid=c.findtext("tstamps").split()[0],
                          fields={k: v for k, v in fields.items() if k != "Footprint"},
                          dnp="dnp" in props, offboard="exclude_from_board" in props))
    nets = {}
    for n in root.iter("net"):
        for node in n.iter("node"):
            nets[(node.get("ref"), node.get("pin"))] = n.get("name")
    return comps, nets


def place_reference(fp, side):
    """Put the reference text on one side of the part's courtyard, reading horizontally."""
    box = None
    crtyd = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    for g in fp.GraphicalItems():
        if g.GetLayer() == crtyd:
            if box is None:
                box = g.GetBoundingBox()
            else:
                box.Merge(g.GetBoundingBox())
    ref = fp.Reference()
    ref.SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
    ref.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    h = pcbnew.ToMM(ref.GetTextHeight())
    cx, cy = box.GetCenter().x, box.GetCenter().y
    if side in ("above", "below"):
        ref.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        y = box.GetTop() - mm(h / 2 + 0.15) if side == "above" else box.GetBottom() + mm(h / 2 + 0.15)
        ref.SetPosition(pcbnew.VECTOR2I(cx, y))
    else:
        left = side == "left"
        ref.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT if left else pcbnew.GR_TEXT_H_ALIGN_LEFT)
        x = box.GetLeft() - mm(0.2) if left else box.GetRight() + mm(0.2)
        ref.SetPosition(pcbnew.VECTOR2I(x, cy))


_IO = None


def load_footprint(lib_id):
    nick, name = lib_id.split(":")
    lib_dir = os.path.join(OUT, "ivflow_lib", "ivflow_lib.pretty") if nick == "ivflow_lib" \
        else os.path.join(FP_ROOT, f"{nick}.pretty")
    global _IO
    if _IO is None:     # one explicit KiCad-format plugin (pcbnew.FootprintLoad's lookup is flaky)
        _IO = pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    fp = _IO.FootprintLoad(lib_dir, name)
    if fp is None:
        raise SystemExit(f"footprint not found: {lib_id}")
    fp.SetFPID(pcbnew.LIB_ID(nick, name))
    return fp


# ---------------------------------------------------------------- build
def build(board):
    comps, pin_nets = read_netlist()
    netinfo = {}
    for name in sorted(set(pin_nets.values())):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni

    placed = set()
    for c in comps:
        if c["offboard"] or not c["footprint"]:
            continue
        ref = c["ref"]
        if ref not in PLACE:
            raise SystemExit(f"{ref} has no entry in PLACE")
        x, y, rot, side, ref_side = PLACE[ref]
        fp = load_footprint(c["footprint"])
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH(f"/{c['uuid']}"))
        fp.SetSheetname("/")
        fp.SetSheetfile("ivflow.kicad_sch")
        for key, val in c["fields"].items():     # Datasheet, Description, LCSC (schematic parity)
            fp.SetField(key, val)
            fp.GetField(key).SetVisible(False)
        if c["dnp"]:
            fp.SetDNP(True)
        board.Add(fp)
        fp.SetPosition(at(x, y))
        if ref in BOTTOM:
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            net = pin_nets.get((ref, pad.GetNumber()))
            if net:
                pad.SetNet(netinfo[net])
        if ref in silk_labels.CONNECTOR_LABELS:
            silk_labels.add_labels(fp, ref, side)
        if ref_side:
            place_reference(fp, ref_side)
        placed.add(ref)
    unused = set(PLACE) - placed
    if unused:
        raise SystemExit(f"PLACE entries without a footprint: {sorted(unused)}")

    # Outline
    edge = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECTANGLE)
    edge.SetStart(at(0, 0))
    edge.SetEnd(at(W, H))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mm(0.1))
    board.Add(edge)

    # Mounting holes (board-only: not in the schematic or BOM)
    for i, (x, y) in enumerate([(HOLE_INSET, HOLE_INSET), (W - HOLE_INSET, HOLE_INSET),
                                (HOLE_INSET, H - HOLE_INSET), (W - HOLE_INSET, H - HOLE_INSET)], 1):
        fp = load_footprint(HOLE_FP)
        fp.SetReference(f"H{i}")
        fp.Reference().SetVisible(False)
        fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
        board.Add(fp)
        fp.SetPosition(at(x, y))

    for text, x, y, h, layer in SILK_TEXT:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetLayer(layer)
        t.SetMirrored(layer == pcbnew.B_SilkS)     # reads correctly when the board is turned over
        t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h)))
        t.SetTextThickness(mm(0.25))
        t.SetPosition(at(x, y))
        board.Add(t)
    return len(placed)


def set_project_rules(net_names):
    """Design rules and net classes live in the .kicad_pro file."""
    with open(PRO, encoding="utf-8") as f:
        pro = json.load(f)
    pro["board"]["design_settings"]["rules"].update(RULES)
    ns = pro["net_settings"]
    template = next(c for c in ns["classes"] if c["name"] == "Default")
    classes = []
    for i, (name, (track, clr, via_d, via_drill)) in enumerate(NETCLASSES.items()):
        cls = dict(template, name=name, track_width=track, clearance=clr, via_diameter=via_d, via_drill=via_drill)
        if name != "Default":
            cls["priority"] = i
        classes.append(cls)
    ns["classes"] = classes
    # Local labels are named "/NAME" in the netlist, power symbols are global ("+3V3")
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n}
                               for n in net_names if n.lstrip("/") in POWER_NETS]
    with open(PRO, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pro, f, indent=2)
        f.write("\n")


def run_drc():
    rpt = os.path.join(OUT, "ivflow_drc.rpt")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--schematic-parity", "--severity-all", "-o", rpt, PCB],
                   capture_output=True)
    with open(rpt, encoding="utf-8") as f:
        text = f.read()
    # Summary only; the full list (mostly unconnected pads before routing) is in the report
    print("\n".join(line for line in text.splitlines() if line.startswith("** Found")))
    print(f"full report: {rpt}")
    return rpt


if __name__ == "__main__":
    board = pcbnew.LoadBoard(PCB)
    if len(board.GetFootprints()) and not FORCE:
        raise SystemExit(f"{PCB} already has footprints; refusing to regenerate (use --force)")
    # Delete (not Remove): Remove leaves orphaned objects that break pcbnew's SWIG types
    for item in (list(board.GetFootprints()) + list(board.GetDrawings()) + list(board.GetTracks())
                 + list(board.Zones())):
        board.Delete(item)
    n = build(board)
    pcbnew.SaveBoard(PCB, board, True)
    set_project_rules([ni.GetNetname() for ni in board.GetNetsByName().values() if ni.GetNetname()])
    print(f"wrote: {PCB} ({n} footprints + 4 mounting holes)")
    run_drc()
