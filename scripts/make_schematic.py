"""Stage 2: generate the IVFlow schematic (one A4 sheet) and verify it.

Each part is placed with an explicit net for EVERY pin. Pins get a short stub with a
net label, a GND/+3V3 power symbol, a no-connect flag, or a direct wire to a
neighbouring pin. After writing, the script exports KiCad's netlist and checks that
every pin landed on the intended net, then runs ERC.

Run with KiCad's bundled Python:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts\\make_schematic.py [--out DIR] [--force]

Refuses to overwrite a schematic that already contains symbols unless --force is
given (once the user edits the schematic in KiCad, make targeted edits instead).
"""
import datetime
import math
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

import kisexpr as k
from kisexpr import QStr, q

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = "ivflow"
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(ROOT, "ivflow")
SCH = os.path.join(OUT, f"{PROJECT}.kicad_sch")
LIB_FILE = os.path.join(OUT, "ivflow_lib", "ivflow_lib.kicad_sym")
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
FORCE = "--force" in sys.argv

G = 2.54          # layout grid: all coordinates below are in units of 2.54 mm
POWER_NETS = {"GND": "power:GND", "+3V3": "power:+3V3"}
NC = "NC"

# ---------------------------------------------------------------- footprints + LCSC (Stage 3)
# Hand-assembled: 0805 passives and SOT parts use KiCad's hand-soldering pad variants.
FP_R = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
FP_C = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_SOT23 = "Package_TO_SOT_SMD:SOT-23_Handsoldering"
FP_XH2 = "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
FP_XH5 = "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical"
FP_PH2 = "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"
FP_HDR = "Connector_PinHeader_2.54mm:PinHeader_1x{:02d}_P2.54mm_Vertical"
# LCSC numbers checked against lcsc.com product pages (2026-11-01)
LCSC_R = {"100k": "C149504", "10k": "C17414", "100": "C17408", "4.7k": "C17673", "82": "C17841"}
LCSC_C = {"100n": "C49678", "10u": "C15850", "22u": "C45783", "10n": "C1710"}
LCSC_XH2, LCSC_XH5, LCSC_PH2 = "C158012", "C157991", "C131337"

# ---------------------------------------------------------------- the design
# Blocks: (title, frame origin, frame size). Part coordinates are relative to the origin.
BLOCKS = {
    "POWER": ((5, 5), (66, 29)),
    "MCU": ((73, 5), (39, 29)),
    "BATTERY SENSE": ((5, 36), (30, 28)),
    "SENSORS (LDR strip)": ((37, 36), (32, 24)),
    "LED (drip chamber)": ((73, 36), (16, 16)),
    "BUZZER": ((91, 36), (21, 29)),
    "OLED / BUTTON / EXPANSION": ((5, 66), (62, 12.5)),
}

# part: ref, lib_id, value, block, (x, y), rotation, {pin number or name: net}, extras
PARTS = [
    # ---- POWER
    dict(ref="U2", lib="ivflow_lib:TP4056_Module_USB-C", value="TP4056 USB-C", block="POWER", at=(8, 10),
         nets={"IN+": "VBUS", "IN-": "GND", "OUT+": "VBAT_P", "OUT-": "GND", "BAT+": "BATT+", "BAT-": "BATT-"},
         fp="ivflow_lib:TP4056_Module_USB-C"),
    dict(ref="J1", lib="Connector_Generic:Conn_01x02", value="BATTERY", block="POWER", at=(24, 11),
         nets={"1": "BATT+", "2": "BATT-"}, desc="Li-Po 3.7 V, JST-PH 2-pin. BAT- is NOT system GND.",
         fp=FP_PH2, lcsc=LCSC_PH2),
    dict(ref="D1", lib="Diode:SS14", value="SS14", block="POWER", at=(34, 7), rot=180,
         nets={"A": "VBUS", "K": "VSYS"}, fp="Diode_SMD:D_SMA_Handsoldering", lcsc="C2480"),
    dict(ref="Q1", lib="Transistor_FET:AO3401A", value="AO3401A", block="POWER", at=(34, 18),
         nets={"G": "VBUS", "D": "VBAT_P", "S": "VSYS"}, fp=FP_SOT23, lcsc="C15127"),
    dict(ref="R1", lib="Device:R", value="100k", block="POWER", at=(42, 18), nets={"1": "VBUS", "2": "GND"}),
    dict(ref="J6", lib="Connector_Generic:Conn_01x02", value="POWER SW", block="POWER", at=(52, 8),
         nets={"1": "VSYS", "2": "VSYS_SW"}, fp=FP_XH2, lcsc=LCSC_XH2,
         desc="JST-XH 2-pin to the panel-mount power switch (rated >= 1 A). Closed = ON"),
    dict(ref="C1", lib="Device:C", value="10u", block="POWER", at=(60, 10), nets={"1": "VSYS_SW", "2": "GND"}),
    dict(ref="#FLG01", lib="power:PWR_FLAG", value="PWR_FLAG", block="POWER", at=(64, 6), nets={"1": "VSYS_SW"}),
    dict(ref="U3", lib="Regulator_Linear:AP2112K-3.3", value="AP2112K-3.3", block="POWER", at=(52, 23),
         nets={"VIN": "VSYS_SW", "EN": "VSYS_SW", "GND": "GND", "NC": NC, "VOUT": "+3V3"},
         fp="Package_TO_SOT_SMD:SOT-23-5_HandSoldering", lcsc="C51118"),
    dict(ref="C2", lib="Device:C", value="10u", block="POWER", at=(60, 24), nets={"1": "+3V3", "2": "GND"}),
    dict(ref="C3", lib="Device:C", value="100n", block="POWER", at=(64, 24), nets={"1": "+3V3", "2": "GND"}),
    # ---- MCU
    dict(ref="U1", lib="ivflow_lib:ESP32-C3_SuperMini", value="ESP32-C3 SuperMini", block="MCU", at=(20, 16),
         nets={"5V": NC, "3V3": "+3V3", "GND": "GND",
               "GPIO0": "LDR1", "GPIO1": "LDR2", "GPIO2": "BAT_SENSE", "GPIO3": "LDR3", "GPIO4": "LDR4",
               "GPIO5": "LED_EN", "GPIO6": "BUZ_EN", "GPIO7": "BAT_EN", "GPIO8": "SDA", "GPIO9": "SCL",
               "GPIO10": "BTN", "GPIO20": "EXP_IO20", "GPIO21": "EXP_IO21"},
         fp="ivflow_lib:ESP32-C3_SuperMini"),
    dict(ref="C4", lib="Device:C", value="22u", block="MCU", at=(6, 16), nets={"1": "+3V3", "2": "GND"},
         desc="Bulk capacitor, place next to U1 3V3 pin"),
    # ---- BATTERY SENSE
    dict(ref="R2", lib="Device:R", value="100k", block="BATTERY SENSE", at=(4, 10),
         nets={"1": "VSYS_SW", "2": "BAT_SENSE"}),
    dict(ref="C5", lib="Device:C", value="100n", block="BATTERY SENSE", at=(9, 10),
         nets={"1": "BAT_SENSE", "2": "GND"}),
    dict(ref="R3", lib="Device:R", value="100k", block="BATTERY SENSE", at=(14, 10),
         nets={"1": "BAT_SENSE", "2": "Q2_D"}),
    dict(ref="Q2", lib="Transistor_FET:2N7002", value="2N7002", block="BATTERY SENSE", at=(18, 21),
         nets={"D": "Q2_D", "G": "Q2_G", "S": "GND"}, fp=FP_SOT23, lcsc="C8545"),
    dict(ref="R4", lib="Device:R", value="100", block="BATTERY SENSE", at=(21, 10),
         nets={"1": "BAT_EN", "2": "Q2_G"}),
    dict(ref="R5", lib="Device:R", value="100k", block="BATTERY SENSE", at=(26, 10),
         nets={"1": "Q2_G", "2": "GND"}),
    # ---- SENSORS
    dict(ref="J2", lib="Connector_Generic:Conn_01x05", value="LDR STRIP", block="SENSORS (LDR strip)",
         at=(29, 12), nets={"1": "+3V3", "2": "LDR1", "3": "LDR2", "4": "LDR3", "5": "LDR4"},
         desc="JST-XH 5-pin to the off-board LDR strip", fp=FP_XH5, lcsc=LCSC_XH5),
    # ---- LED
    dict(ref="R20", lib="Device:R", value="82", block="LED (drip chamber)", at=(4, 8),
         nets={"1": "LED_EN", "2": "LED_A"}),
    dict(ref="J3", lib="Connector_Generic:Conn_01x02", value="LED", block="LED (drip chamber)", at=(14, 8),
         nets={"1": "LED_A", "2": "GND"}, desc="JST-XH 2-pin to the off-board 5 mm LED. 1 = anode (+)",
         fp=FP_XH2, lcsc=LCSC_XH2),
    # ---- BUZZER
    dict(ref="J7", lib="Connector_Generic:Conn_01x02", value="BUZZER", block="BUZZER", at=(14, 8),
         nets={"1": "VSYS_SW", "2": "BUZ_N"}, fp=FP_XH2, lcsc=LCSC_XH2,
         desc="JST-XH 2-pin to the off-board 3-5 V active buzzer. 1 = +, 2 = -"),
    dict(ref="D3", lib="Diode:1N4148W", value="1N4148W", block="BUZZER", at=(19, 15), rot=270,
         nets={"K": "VSYS_SW", "A": "BUZ_N"}, fields=((-2.5, -0.5), (-2.5, 0.5)),
         fp="Diode_SMD:D_SOD-123", lcsc="C81598"),
    dict(ref="Q3", lib="Transistor_FET:AO3400A", value="AO3400A", block="BUZZER", at=(12, 20),
         nets={"D": "BUZ_N", "G": "Q3_G", "S": "GND"}, fp=FP_SOT23, lcsc="C20917"),
    dict(ref="R21", lib="Device:R", value="100", block="BUZZER", at=(6, 20), rot=90,
         nets={"1": "BUZ_EN", "2": "Q3_G"}, fields=((0, -1.5), (0, 1.5))),
    dict(ref="R22", lib="Device:R", value="100k", block="BUZZER", at=(10, 25),
         nets={"1": "Q3_G", "2": "GND"}, fields=((-1, -0.5), (-1, 0.5))),
    # ---- OLED / BUTTON / EXPANSION
    dict(ref="J4", lib="Connector_Generic:Conn_01x04", value="OLED", block="OLED / BUTTON / EXPANSION",
         at=(12, 6), nets={"1": "GND", "2": "+3V3", "3": "SCL", "4": "SDA"}, stub={"1": 3},
         desc="1x4 2.54 mm header, jumper wires to the I2C OLED", fp=FP_HDR.format(4)),
    dict(ref="R23", lib="Device:R", value="4.7k", block="OLED / BUTTON / EXPANSION", at=(24, 6), dnp=True,
         nets={"1": "+3V3", "2": "SDA"}),
    dict(ref="R24", lib="Device:R", value="4.7k", block="OLED / BUTTON / EXPANSION", at=(28, 6), dnp=True,
         nets={"1": "+3V3", "2": "SCL"}),
    dict(ref="J8", lib="Connector_Generic:Conn_01x02", value="BUTTON", block="OLED / BUTTON / EXPANSION",
         at=(40, 5), nets={"1": "BTN", "2": "GND"}, fp=FP_XH2, lcsc=LCSC_XH2,
         desc="JST-XH 2-pin to the off-board push button (BTN to GND)"),
    dict(ref="C6", lib="Device:C", value="100n", block="OLED / BUTTON / EXPANSION", at=(45, 6),
         nets={"1": "BTN", "2": "GND"}),
    dict(ref="J5", lib="Connector_Generic:Conn_01x05", value="EXPANSION", block="OLED / BUTTON / EXPANSION",
         at=(57, 6), nets={"1": "GND", "2": "VSYS_SW", "3": "+3V3", "4": "EXP_IO20", "5": "EXP_IO21"},
         desc="1x5 2.54 mm header: future servo / spare I/O", fp=FP_HDR.format(5)),
]
# LDR channel n: R(10+n) 10k and C(10+n) 10n from LDRn to GND, R row above C row
for n in range(1, 5):
    PARTS.append(dict(ref=f"R{10 + n}", lib="Device:R", value="10k", block="SENSORS (LDR strip)",
                      at=(3 + 5 * (n - 1), 8), nets={"1": f"LDR{n}", "2": "GND"}))
    PARTS.append(dict(ref=f"C{10 + n}", lib="Device:C", value="10n", block="SENSORS (LDR strip)",
                      at=(5 + 5 * (n - 1), 17), nets={"1": f"LDR{n}", "2": "GND"}))
for _p in PARTS:
    if _p["lib"] == "Device:R":
        _p.setdefault("fp", FP_R)
        _p.setdefault("lcsc", LCSC_R[_p["value"]])
    elif _p["lib"] == "Device:C":
        _p.setdefault("fp", FP_C)
        _p.setdefault("lcsc", LCSC_C[_p["value"]])

# Direct wires between neighbouring pins (both pins must be on the same net)
LINKS = [
    (("R21", "2"), ("Q3", "G")),
    (("R22", "1"), ("Q3", "G")),
]
# Linked pins normally get no stub; these still get their label / power symbol
# because the net continues elsewhere on the sheet.
KEEP_STUB = set()
# Nets that only exist as wires still get a name: (ref, pin) -> label direction
LINK_LABELS = {("Q3", "G"): 90}

NOTES = [
    ("POWER", (1, 27), "USB 5 V feeds VSYS through D1; Q1 connects the battery when USB is absent."),
    ("POWER", (1, 28), "J6 goes to a panel-mount power switch on the case (closed = ON)."),
    ("MCU", (1, 27), "SuperMini 5V pin intentionally unconnected. Antenna end over keepout / board edge."),
    ("BUZZER", (1, 3.2), "Buzzer off-board on J7; D3 stays on board"),
    ("BATTERY SENSE", (1, 26.5), "GPIO7 high enables the divider; BAT_SENSE = VSYS_SW / 2"),
    ("SENSORS (LDR strip)", (1, 22.5), "R11-R14 value is a placeholder: tune for the LDRs used"),
    ("OLED / BUTTON / EXPANSION", (1, 11.4), "R23/R24 DNP: most OLED modules already have I2C pull-ups"),
]

# ---------------------------------------------------------------- geometry
def rot_vec(x, y, deg):
    r = math.radians(deg)
    return x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)


def lib_to_sch(origin, rot, px, py):
    """Library coords (mm, y up) -> schematic coords (mm, y down)."""
    rx, ry = rot_vec(px, py, rot)
    return round(origin[0] + rx, 4), round(origin[1] - ry, 4)


def direction(deg):
    """Unit step in schematic coords for a library-frame angle."""
    r = math.radians(deg)
    return round(math.cos(r)), -round(math.sin(r))


def at(x, y, a=0):
    return ["at", x, y, a]


def font_effects(size=1.27, justify=None, hide=False, bold=False):
    f = ["font", ["size", size, size]]
    if bold:
        f.append(["bold", "yes"])
    e = ["effects", f]
    if justify:
        e.append(["justify"] + justify.split())
    if hide:
        e.append(["hide", "yes"])
    return e


# ---------------------------------------------------------------- builder
class Sheet:
    def __init__(self, root_uuid):
        self.root_uuid = root_uuid
        self.items = []
        self.lib_symbols = {}
        self.pin_points = {}      # (ref, pin number) -> (x, y)
        self.expected = {}        # (ref, pin number) -> net
        self.pwr_count = 0

    def lib_symbol(self, lib_id):
        if lib_id not in self.lib_symbols:
            nick, name = lib_id.split(":")
            path = LIB_FILE if nick == "ivflow_lib" else k.official_lib(nick)
            self.lib_symbols[lib_id] = k.flat_symbol(path, name, nick)
        return self.lib_symbols[lib_id]

    def place(self, ref, lib_id, value, origin, rot=0, dnp=False, fields=None, desc=None, hide_ref=False,
              value_at=None, fp=None, lcsc=None):
        sym = self.lib_symbol(lib_id)
        pins = k.symbol_pins(sym)
        node = ["symbol", ["lib_id", q(lib_id)], at(origin[0], origin[1], rot), ["unit", 1], ["body_style", 1],
                ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
                ["in_pos_files", "yes"], ["dnp", "yes" if dnp else "no"], ["uuid", k.new_uuid()]]
        for prop in k.find_all(sym, "property"):
            key = str(prop[1])
            if key.startswith("ki_"):
                continue
            text = {"Reference": ref, "Value": value}.get(key, str(prop[2]))
            if key == "Description" and desc:
                text = desc
            if key == "Footprint" and fp:
                text = fp
            pat = k.find(prop, "at")
            px, py = lib_to_sch(origin, rot, float(pat[1]), float(pat[2]))
            lib_eff = k.find(prop, "effects")
            lib_just = k.find(lib_eff, "justify") if lib_eff else None
            justify = " ".join(str(j) for j in lib_just[1:]) if lib_just and rot == 0 else None
            if fields and key in ("Reference", "Value"):
                dx, dy = fields[0] if key == "Reference" else fields[1]
                px, py = origin[0] + dx * G, origin[1] + dy * G
                justify = ("left" if dx > 0 else "right" if dx < 0 else None) if rot == 0 else None
            elif lib_id in ("Device:R", "Device:C") and rot == 0 and key in ("Reference", "Value"):
                px = origin[0] + 1.5 * G
                py = origin[1] + (-0.5 if key == "Reference" else 0.5) * G
                justify = "left"
            if value_at and key == "Value":
                (px, py), justify = value_at, None
            hidden = (k.find(prop, "hide") is not None and k.find(prop, "hide")[1] == "yes") \
                or key not in ("Reference", "Value") or (key == "Reference" and hide_ref)
            # Field angles are relative to the symbol: 90 on a 90/270 symbol reads horizontally
            fangle = 90 if rot in (90, 270) else 0
            node.append(["property", q(key), q(text), at(px, py, fangle),
                         font_effects(justify=justify, hide=hidden)])
        if lcsc:
            node.append(["property", q("LCSC"), q(lcsc), at(origin[0], origin[1], 0), font_effects(hide=True)])
        for num in pins:
            node.append(["pin", q(num), ["uuid", k.new_uuid()]])
        node.append(["instances", ["project", q(PROJECT),
                                   ["path", q("/" + self.root_uuid), ["reference", q(ref)], ["unit", 1]]]])
        self.items.append(node)
        for num, p in pins.items():
            self.pin_points[(ref, num)] = lib_to_sch(origin, rot, p["x"], p["y"])
        return pins

    def wire(self, a, b):
        self.items.append(["wire", ["pts", ["xy", a[0], a[1]], ["xy", b[0], b[1]]],
                           ["stroke", ["width", 0], ["type", "default"]], ["uuid", k.new_uuid()]])

    def label(self, name, pt, out_deg):
        angle = int(out_deg) % 360
        justify = {0: "left bottom", 90: "left bottom", 180: "right bottom", 270: "right bottom"}[angle]
        self.items.append(["label", q(name), at(pt[0], pt[1], angle), font_effects(justify=justify),
                           ["uuid", k.new_uuid()]])

    def power(self, net, pt, stub_deg):
        lib_id = POWER_NETS[net]
        pin = k.symbol_pins(self.lib_symbol(lib_id))["1"]
        rot = int(stub_deg - pin["angle"]) % 360
        value_at = None
        if stub_deg in (0, 180):
            # Sideways symbol: centre the net name just beyond the symbol body
            dx, _ = direction(stub_deg)
            value_at = (round(pt[0] + dx * (3.0 + 0.6 * len(net)), 2), pt[1])
        self.pwr_count += 1
        self.place(f"#PWR{self.pwr_count:02d}", lib_id, net, pt, rot=rot, hide_ref=True, value_at=value_at)

    def no_connect(self, pt):
        self.items.append(["no_connect", at(pt[0], pt[1])[:3], ["uuid", k.new_uuid()]])

    def junction(self, pt):
        self.items.append(["junction", at(pt[0], pt[1])[:3], ["diameter", 0], ["color", 0, 0, 0, 0],
                           ["uuid", k.new_uuid()]])

    def rect(self, x1, y1, x2, y2):
        self.items.append(["rectangle", ["start", x1, y1], ["end", x2, y2],
                           ["stroke", ["width", 0], ["type", "dash"]], ["fill", ["type", "none"]],
                           ["uuid", k.new_uuid()]])

    def text(self, s, pt, size=1.27, bold=False):
        self.items.append(["text", q(s), ["exclude_from_sim", "no"], at(pt[0], pt[1], 0),
                           font_effects(size=size, justify="left bottom", bold=bold), ["uuid", k.new_uuid()]])


def build(root_uuid):
    sh = Sheet(root_uuid)
    for title, ((ox, oy), (w, h)) in BLOCKS.items():
        sh.rect(ox * G, oy * G, (ox + w) * G, (oy + h) * G)
        sh.text(title, ((ox + 0.6) * G, (oy + 1.3) * G), size=2.0, bold=True)
    for blk, (dx, dy), s in NOTES:
        (ox, oy), _ = BLOCKS[blk]
        sh.text(s, ((ox + dx) * G, (oy + dy) * G), size=1.27)

    linked = defaultdict(int)
    for a, b in LINKS:
        linked[a] += 1
        linked[b] += 1

    for part in PARTS:
        (ox, oy), _ = BLOCKS[part["block"]]
        origin = ((ox + part["at"][0]) * G, (oy + part["at"][1]) * G)
        rot = part.get("rot", 0)
        pins = sh.place(part["ref"], part["lib"], part["value"], origin, rot=rot, dnp=part.get("dnp", False),
                        fields=part.get("fields"), desc=part.get("desc"),
                        hide_ref=part["ref"].startswith("#"), fp=part.get("fp"), lcsc=part.get("lcsc"))
        by_name = {p["name"]: num for num, p in pins.items()}
        for name, num in by_name.items():
            if name and name not in pins:
                sh.pin_points[(part["ref"], name)] = sh.pin_points[(part["ref"], num)]
        resolved = {}
        for key, net in part["nets"].items():
            num = key if key in pins else by_name.get(key)
            if num is None:
                raise SystemExit(f"{part['ref']}: no pin '{key}'")
            resolved[num] = net
        missing = set(pins) - set(resolved)
        if missing:
            raise SystemExit(f"{part['ref']}: pins without a net: {sorted(missing)}")
        for num, net in resolved.items():
            pt = sh.pin_points[(part["ref"], num)]
            if net != NC and not part["ref"].startswith("#FLG"):
                sh.expected[(part["ref"], num)] = net
            if net == NC:
                sh.no_connect(pt)
                continue
            pname = pins[num]["name"]
            keys = {(part["ref"], num), (part["ref"], pname)}
            if keys & set(linked) and not keys & KEEP_STUB:
                continue
            out_deg = (pins[num]["angle"] + 180 + rot) % 360
            dx, dy = direction(out_deg)
            stub = part.get("stub", {}).get(num, part.get("stub", {}).get(pname, 1)) * G
            end = (round(pt[0] + dx * stub, 4), round(pt[1] + dy * stub, 4))
            sh.wire(pt, end)
            if net in POWER_NETS:
                sh.power(net, end, out_deg)
            else:
                sh.label(net, end, out_deg)

    for a, b in LINKS:
        pa, pb = sh.pin_points[a], sh.pin_points[b]
        if pa[0] == pb[0] or pa[1] == pb[1]:
            sh.wire(pa, pb)
        else:  # L-shaped: vertical from a, then horizontal into b
            corner = (pa[0], pb[1])
            sh.wire(pa, corner)
            sh.wire(corner, pb)
    for pin, n in linked.items():
        if n + (pin in KEEP_STUB) > 1:
            sh.junction(sh.pin_points[pin])
    for (ref, pin), deg in LINK_LABELS.items():
        net = next(n for (r, p), n in sh.expected.items()
                   if r == ref and sh.pin_points[(r, p)] == sh.pin_points[(ref, pin)])
        sh.label(net, sh.pin_points[(ref, pin)], deg)
    return sh


# ---------------------------------------------------------------- output + checks
def write(sh, path):
    with open(path, encoding="utf-8") as f:
        old = k.parse(f.read())
    tree = ["kicad_sch", ["version", "20260306"], ["generator", q("eeschema")], ["generator_version", q("10.0")],
            ["uuid", QStr(sh.root_uuid)], ["paper", q("A4")],
            ["title_block", ["title", q("IVFlow")], ["date", q(datetime.date.today().isoformat())],
             ["rev", q("v1")], ["comment", 1, q("Battery-powered IV drip monitor - main board")]],
            ["lib_symbols"] + list(sh.lib_symbols.values())]
    tree += sh.items
    tree += [["sheet_instances", ["path", q("/"), ["page", q("1")]]], ["embedded_fonts", "no"]]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(k.dump(tree) + "\n")
    print(f"wrote: {path}")


def check_netlist(sh, path):
    xml_path = os.path.splitext(path)[0] + "_netlist.xml"
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", xml_path, path],
                   check=True, capture_output=True)
    actual = {}
    for net in ET.parse(xml_path).getroot().iter("net"):
        name = net.get("name").lstrip("/")
        for node in net.iter("node"):
            actual[(node.get("ref"), node.get("pin"))] = name
    os.remove(xml_path)
    bad = []
    for key, want in sh.expected.items():
        got = actual.get(key)
        if got != want:
            bad.append(f"  {key[0]}.{key[1]}: expected {want}, got {got}")
    # Also make sure no two intended nets were merged
    groups = defaultdict(set)
    for key, want in sh.expected.items():
        groups[actual.get(key)].add(want)
    merged = {n: w for n, w in groups.items() if len(w) > 1}
    for n, w in merged.items():
        bad.append(f"  KiCad net {n} merges intended nets {sorted(w)}")
    if bad:
        print("NETLIST CHECK FAILED:\n" + "\n".join(bad))
        return False
    print(f"netlist check: all {len(sh.expected)} pin connections match the design")
    return True


def check_footprints():
    """Every placed part has a footprint, and that footprint exists in its library."""
    bad = []
    for part in PARTS:
        if part["ref"].startswith("#"):
            continue
        fp = part.get("fp")
        if not fp:
            bad.append(f"  {part['ref']}: no footprint assigned")
            continue
        nick, name = fp.split(":")
        base = os.path.join(OUT, "ivflow_lib") if nick == "ivflow_lib" else os.path.join(k.KICAD_SHARE, "footprints")
        if not os.path.isfile(os.path.join(base, f"{nick}.pretty", f"{name}.kicad_mod")):
            bad.append(f"  {part['ref']}: {fp} not found")
    print("footprint check: " + ("all parts have an existing footprint" if not bad else "\n" + "\n".join(bad)))
    return not bad


def run_erc(path):
    rpt = os.path.splitext(path)[0] + "_erc.rpt"
    subprocess.run([KICAD_CLI, "sch", "erc", "--severity-all", "-o", rpt, path], capture_output=True)
    with open(rpt, encoding="utf-8") as f:
        text = f.read()
    print(text[text.find("**"):] if "**" in text else text)
    return rpt


if __name__ == "__main__":
    with open(SCH, encoding="utf-8") as f:
        existing = f.read()
    if "(lib_id" in existing and not FORCE:
        raise SystemExit(f"{SCH} already has symbols; refusing to regenerate (use --force)")
    root = str(k.find(k.parse(existing), "uuid")[1])
    sheet = build(root)
    write(sheet, SCH)
    ok = check_netlist(sheet, SCH)
    check_footprints()  # TP4056 footprint stays missing until the module is measured
    run_erc(SCH)
    sys.exit(0 if ok else 1)
