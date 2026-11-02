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
W, H = 61.0, 52.0            # board size (mm)
HOLE_INSET = 3.2             # M2 hole centre from both edges
HOLE_FP = "MountingHole:MountingHole_2.2mm_M2"

# ref: (x, y, rotation, connector label side, reference text side), mm from the board's
# top-left corner. Reference side: "above"/"below"/"left"/"right", or None = library default.
# U1 is turned 180 degrees: antenna at the top edge, USB-C pointing down into the board.
# Its left socket row (x 13.38) is then GPIO0-4/3V3/GND/5V from the top, the right row
# (x 28.62) GPIO21/20/10/9/8/7/6/5.
PLACE = {
    "U1": (21.0, 11.56, 180, None, None),
    # LDR strip: connector on the left edge; the four R/C filters sit under the module
    # (it stands ~8.5 mm up on its sockets), right next to GPIO0/1/3/4.
    "J2": (4.45, 8.9, 270, "right", None),
    "R11": (19.2, 8.2, 0, None, "above"), "C11": (23.5, 8.2, 0, None, "above"),
    "R12": (19.2, 11.6, 0, None, "above"), "C12": (23.5, 11.6, 0, None, "above"),
    "R13": (19.2, 15.0, 0, None, "above"), "C13": (23.5, 15.0, 0, None, "above"),
    "R14": (19.2, 18.4, 0, None, "above"), "C14": (23.5, 18.4, 0, None, "above"),
    "C4": (21.35, 21.8, 0, None, "left"),
    # Charger on the left edge, power path + regulator below the module (SMD only, so a
    # USB-C cable can still be plugged into the SuperMini on the board)
    "J9": (4.45, 26.5, 270, "right", None),
    "D1": (21.0, 26.5, 0, None, "above"),
    "Q1": (18.0, 32.0, 0, None, "above"), "R1": (24.5, 32.0, 0, None, "above"),
    "U3": (18.0, 38.0, 0, None, "above"), "C1": (24.5, 36.4, 0, None, "above"),
    "C2": (24.5, 39.8, 0, None, "above"), "C3": (24.5, 43.2, 0, None, "above"),
    # Bottom edge: battery left of the USB path, then power switch, LED, buzzer
    "J1": (9.0, 48.18, 0, "above", None),
    "J6": (29.8, 47.6, 0, "above", None),
    "J3": (39.9, 47.6, 0, "above", None),
    "J7": (49.0, 47.6, 0, "above", None),
    # Right edge: expansion, OLED, button
    "J5": (58.7, 7.7, 0, "left", None),
    "J4": (58.7, 21.9, 0, "left", None),
    "J8": (57.6, 34.6, 270, "left", None),
    "C6": (50.5, 36.0, 90, None, "left"),
    # I2C pull-ups (DNP) next to GPIO8/9
    "R24": (33.0, 9.0, 0, None, "above"), "R23": (33.0, 12.4, 0, None, "above"),
    # Battery sense: switch + divider next to GPIO7; BAT_SENSE runs under the module to GPIO2
    "R4": (33.0, 15.8, 0, None, "above"), "Q2": (38.5, 16.0, 0, None, "above"),
    "R5": (38.5, 11.2, 0, None, "above"), "R2": (44.0, 9.0, 0, None, "above"),
    "C5": (44.0, 12.4, 0, None, "above"), "R3": (44.0, 15.8, 0, None, "above"),
    # Buzzer driver next to GPIO6, LED resistor next to GPIO5
    "R21": (33.0, 21.5, 0, None, "above"), "R22": (33.0, 24.9, 0, None, "above"),
    "Q3": (38.5, 23.5, 0, None, "above"), "D3": (44.0, 23.5, 0, None, "above"),
    "R20": (33.0, 28.3, 0, None, "above"),
}
SILK_TEXT = [("IVFlow v1", 42.0, 33.0, 1.5)]   # (text, x, y, height)

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
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
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


def load_footprint(lib_id):
    nick, name = lib_id.split(":")
    lib_dir = os.path.join(OUT, "ivflow_lib", "ivflow_lib.pretty") if nick == "ivflow_lib" \
        else os.path.join(FP_ROOT, f"{nick}.pretty")
    fp = pcbnew.FootprintLoad(lib_dir, name)
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

    for text, x, y, h in SILK_TEXT:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetLayer(pcbnew.F_SilkS)
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
    for item in list(board.GetFootprints()) + list(board.GetDrawings()):
        board.Remove(item)
    n = build(board)
    pcbnew.SaveBoard(PCB, board, True)
    set_project_rules([ni.GetNetname() for ni in board.GetNetsByName().values() if ni.GetNetname()])
    print(f"wrote: {PCB} ({n} footprints + 4 mounting holes)")
    run_drc()
