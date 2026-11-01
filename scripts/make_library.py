"""Stage 1: generate the project-local library ivflow_lib.

Symbols are built with kiutils, then normalised to the current KiCad format with
`kicad-cli sym upgrade`. Footprints are built with KiCad's pcbnew API, which writes
the native format directly (kiutils 1.4.8 cannot round-trip KiCad 10 files).

Run with KiCad's bundled Python:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts\\make_library.py

All physical dimensions live in the PARAMETERS section. Anything marked
verified=False is a published/typical value awaiting the user's measurement.
"""
import os
import subprocess
import sys

import pcbnew
from kiutils.items.common import Effects, Fill, Font, Justify, Position, Property, Stroke
from kiutils.items.syitems import SyRect
from kiutils.symbol import Symbol, SymbolLib, SymbolPin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = "ivflow_lib"
# `--out DIR` writes the library to DIR/ivflow_lib instead (for dry runs)
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(ROOT, "ivflow")
LIB_DIR = os.path.join(OUT, LIB)
SYM_FILE = os.path.join(LIB_DIR, f"{LIB}.kicad_sym")
FP_DIR = os.path.join(LIB_DIR, f"{LIB}.pretty")
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"

# ---------------------------------------------------------------- PARAMETERS
# ESP32-C3 SuperMini, viewed from the TOP (components up), USB-C end at the top.
# Pads 1-8 = left row from the USB end, pads 9-16 = right row from the USB end.
SUPERMINI = dict(
    # Pin order confirmed by the user from their board's pinout diagram (2026-10-31).
    # Row spacing confirmed by the user: 5 empty breadboard holes between the rows (2026-11-01).
    # Size from published data (user decision 2026-11-01: design from published dimensions,
    # check the real board on arrival). No source gives the first-pin offset: pins assumed centred.
    verified=False,
    length=22.52,          # mm, USB end to antenna end (published)
    width=18.0,            # mm (published)
    row_spacing=15.24,     # mm, pin centre to pin centre: (5 empty holes + 1) x 2.54
    first_pin_offset=None,  # mm, USB-end board edge to first pin centre; None = pins centred
    usb_overhang=2.0,      # mm the USB-C shell sticks out past the USB end (user, approximate)
    antenna_len=6.0,       # mm of the antenna end kept free of copper/tracks (typical)
    left_row=["GPIO5", "GPIO6", "GPIO7", "GPIO8", "GPIO9", "GPIO10", "GPIO20", "GPIO21"],
    right_row=["5V", "GND", "3V3", "GPIO4", "GPIO3", "GPIO2", "GPIO1", "GPIO0"],
)
PITCH = 2.54
HDR_PAD = 1.7    # same as KiCad's PinSocket_1x08_P2.54mm_Vertical
HDR_DRILL = 1.0

# TP4056 USB-C module with DW01+8205 protection. It is off-board (pad layouts differ
# between sellers) and wired to the 6-pin connector J9, so it has a symbol but no footprint.
TP4056_PINS = [("1", "IN+"), ("2", "IN-"), ("3", "BAT+"), ("4", "BAT-"), ("5", "OUT+"), ("6", "OUT-")]

# ---------------------------------------------------------------- symbols
TXT = Effects(font=Font(height=1.27, width=1.27))


def sym_pin(etype, name, number, x, y, angle):
    return SymbolPin(electricalType=etype, graphicalStyle="line",
                     position=Position(X=x, Y=y, angle=angle), length=2.54,
                     name=name, number=number,
                     nameEffects=TXT, numberEffects=TXT)


def new_symbol(name, ref, value, footprint, description, keywords, half_w, half_h):
    s = Symbol.create_new(id=name, reference=ref, value=value, footprint=footprint)
    s.properties[0].position = Position(X=-half_w, Y=half_h + 1.27, angle=0)
    s.properties[0].effects = Effects(font=Font(height=1.27, width=1.27), justify=Justify(horizontally="left"))
    s.properties[1].position = Position(X=-half_w, Y=-half_h - 1.27, angle=0)
    s.properties[1].effects = Effects(font=Font(height=1.27, width=1.27), justify=Justify(horizontally="left"))
    hidden = Effects(font=Font(height=1.27, width=1.27), justify=Justify(horizontally="left"), hide=True)
    s.properties += [
        Property(key="Description", value=description, id=4),
        Property(key="ki_keywords", value=keywords, id=5),
    ]
    # Stack hidden fields under the Value so they don't clutter the body in the editor
    for i, prop in enumerate(s.properties[2:]):
        prop.position = Position(X=-half_w, Y=-half_h - 3.81 - i * 2.54, angle=0)
        prop.effects = hidden
    body = Symbol()
    body.libId = f"{name}_0_1"
    body.graphicItems.append(SyRect(start=Position(X=-half_w, Y=half_h), end=Position(X=half_w, Y=-half_h),
                                    stroke=Stroke(width=0.254, type="default"), fill=Fill(type="background")))
    pins = Symbol()
    pins.libId = f"{name}_1_1"
    s.units = [body, pins]
    return s, pins


def supermini_symbol():
    p = SUPERMINI
    pad_of = {n: str(i + 1) for i, n in enumerate(p["left_row"])}
    pad_of.update({n: str(i + 9) for i, n in enumerate(p["right_row"])})
    s, u = new_symbol(
        "ESP32-C3_SuperMini", "U", "ESP32-C3_SuperMini", f"{LIB}:ESP32-C3_SuperMini",
        "ESP32-C3 SuperMini dev board on two 1x8 2.54 mm sockets. 5V pin is the board's USB VBUS.",
        "ESP32 ESP32-C3 SuperMini module", 10.16, 17.78)
    # Left: power. 5V is passive so it can carry a no-connect flag without ERC noise.
    u.pins.append(sym_pin("passive", "5V", pad_of["5V"], -12.7, 15.24, 0))
    u.pins.append(sym_pin("power_in", "3V3", pad_of["3V3"], -12.7, 12.7, 0))
    u.pins.append(sym_pin("power_in", "GND", pad_of["GND"], -12.7, -15.24, 0))
    # Right: GPIOs in numeric order.
    gpios = sorted((n for n in pad_of if n.startswith("GPIO")), key=lambda n: int(n[4:]))
    for i, n in enumerate(gpios):
        u.pins.append(sym_pin("bidirectional", n, pad_of[n], 12.7, 15.24 - i * 2.54, 180))
    return s


def tp4056_symbol():
    s, u = new_symbol(
        "TP4056_Module_USB-C", "U", "TP4056_Module_USB-C", "",
        "TP4056 Li-ion charger module, USB-C, DW01+8205 protection. IN- and OUT- are common; BAT- is separate. "
        "Off-board: wired to the main board through a connector.",
        "TP4056 charger lithium module USB-C", 7.62, 7.62)
    num = {n: k for k, n in TP4056_PINS}
    u.pins += [
        # IN+/IN- source VBUS and GND from the USB-C port; OUT+ sources the protected battery.
        sym_pin("power_out", "IN+", num["IN+"], -10.16, 5.08, 0),
        sym_pin("power_out", "IN-", num["IN-"], -10.16, -5.08, 0),
        sym_pin("power_out", "OUT+", num["OUT+"], 10.16, 5.08, 180),
        sym_pin("passive", "OUT-", num["OUT-"], 10.16, 2.54, 180),
        sym_pin("passive", "BAT+", num["BAT+"], 10.16, -2.54, 180),
        sym_pin("passive", "BAT-", num["BAT-"], 10.16, -5.08, 180),
    ]
    return s


def make_symbols():
    lib = SymbolLib(version="20211014", generator="ivflow_scripts")
    lib.symbols = [supermini_symbol(), tp4056_symbol()]
    os.makedirs(LIB_DIR, exist_ok=True)
    lib.to_file(SYM_FILE)
    subprocess.run([KICAD_CLI, "sym", "upgrade", "--force", SYM_FILE], check=True)
    print(f"wrote: {os.path.relpath(SYM_FILE, ROOT)}")


# ---------------------------------------------------------------- footprints
mm = pcbnew.FromMM


def v(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def add_rect(fp, x1, y1, x2, y2, layer, width):
    r = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_RECTANGLE)
    r.SetStart(v(x1, y1))
    r.SetEnd(v(x2, y2))
    r.SetLayer(layer)
    r.SetWidth(mm(width))
    fp.Add(r)


def add_line(fp, x1, y1, x2, y2, layer, width):
    s = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(v(x1, y1))
    s.SetEnd(v(x2, y2))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    fp.Add(s)


def add_text(fp, text, x, y, layer, size=1.0, thick=0.15, halign=pcbnew.GR_TEXT_H_ALIGN_CENTER):
    t = pcbnew.PCB_TEXT(fp)
    t.SetText(text)
    t.SetPosition(v(x, y))
    t.SetLayer(layer)
    t.SetTextSize(v(size, size))
    t.SetTextThickness(mm(thick))
    t.SetHorizJustify(halign)
    fp.Add(t)


def add_tht_pad(fp, number, x, y, square):
    p = pcbnew.PAD(fp)
    p.SetNumber(number)
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetLayerSet(pcbnew.PAD.PTHMask())
    p.SetShape(pcbnew.PAD_SHAPE_RECT if square else pcbnew.PAD_SHAPE_CIRCLE)
    p.SetSize(v(HDR_PAD, HDR_PAD))
    p.SetDrillSize(v(HDR_DRILL, HDR_DRILL))
    p.SetPosition(v(x, y))
    fp.Add(p)


def add_keepout(fp, pts):
    z = pcbnew.ZONE(fp)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(mm(x), mm(y))
    fp.Add(z)


def new_footprint(name, ref, description, tags):
    fp = pcbnew.FOOTPRINT(pcbnew.BOARD())
    fp.SetFPID(pcbnew.LIB_ID(LIB, name))
    fp.SetLibDescription(description)
    fp.SetKeywords(tags)
    fp.SetAttributes(pcbnew.FP_THROUGH_HOLE)
    fp.Reference().SetText(ref)
    fp.Value().SetText(name)
    return fp


def save_footprint(fp, name):
    io = pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    io.FootprintSave(FP_DIR, fp)
    print(f"wrote: {os.path.relpath(os.path.join(FP_DIR, name + '.kicad_mod'), ROOT)}")


def supermini_footprint():
    p = SUPERMINI
    L, W, S = p["length"], p["width"], p["row_spacing"]
    top = -L / 2  # USB end
    y0 = top + p["first_pin_offset"] if p["first_pin_offset"] is not None else -3.5 * PITCH
    status = "VERIFIED" if p["verified"] else "published dimensions, pins assumed centred, check on arrival"
    fp = new_footprint(
        "ESP32-C3_SuperMini", "U**",
        f"ESP32-C3 SuperMini on two 1x08 2.54 mm sockets, row spacing {S} mm, module {L}x{W} mm ({status})",
        "ESP32-C3 SuperMini socket")

    for i, name in enumerate(p["left_row"] + p["right_row"]):
        row, k = divmod(i, 8)
        x = -S / 2 if row == 0 else S / 2
        y = y0 + k * PITCH
        add_tht_pad(fp, str(i + 1), x, y, square=(i == 0))
        # Pin names between the rows so they stay readable once the module is lifted off
        label = name.replace("GPIO", "")
        if row == 0:
            add_text(fp, label, x + 1.25, y, pcbnew.F_SilkS, 0.8, 0.12, pcbnew.GR_TEXT_H_ALIGN_LEFT)
        else:
            add_text(fp, label, x - 1.25, y, pcbnew.F_SilkS, 0.8, 0.12, pcbnew.GR_TEXT_H_ALIGN_RIGHT)

    # Module outline (silk + fab) and courtyard; the courtyard includes the USB-C overhang
    usb = p["usb_overhang"] or 0
    add_rect(fp, -W / 2, top, W / 2, -top, pcbnew.F_SilkS, 0.12)
    add_rect(fp, -W / 2, top, W / 2, -top, pcbnew.F_Fab, 0.1)
    add_rect(fp, -W / 2 - 0.25, top - usb - 0.25, W / 2 + 0.25, -top + 0.25, pcbnew.F_CrtYd, 0.05)
    if usb:
        add_line(fp, -W / 4, top - usb, W / 4, top - usb, pcbnew.F_Fab, 0.1)
        add_text(fp, f"USB-C ~{usb:g} mm overhang", 0, top - usb - 1.0, pcbnew.F_Fab, 0.8, 0.12)
    add_text(fp, "USB", 0, top + 1.5, pcbnew.F_SilkS, size=1.0)
    add_text(fp, "ANT", 0, -top - 1.5, pcbnew.F_SilkS, size=1.0)
    if not p["verified"]:
        add_text(fp, "PUBLISHED DIMS", 0, -2.0, pcbnew.F_Fab, 1.0, 0.15)
        add_text(fp, "pins assumed centred", 0, 2.0, pcbnew.F_Fab, 0.8, 0.12)
        add_text(fp, "check on arrival", 0, 3.2, pcbnew.F_Fab, 0.8, 0.12)

    # Antenna end: no tracks, vias or pour on either layer between the socket rows
    inner = S / 2 - HDR_PAD / 2 - 0.3
    ant_top = -top - p["antenna_len"]
    add_keepout(fp, [(-inner, ant_top), (inner, ant_top), (inner, -top), (-inner, -top)])
    add_line(fp, -inner, ant_top, inner, ant_top, pcbnew.F_Fab, 0.1)

    fp.Reference().SetPosition(v(0, -top + 1.5))
    fp.Reference().SetLayer(pcbnew.F_SilkS)
    fp.Value().SetPosition(v(0, 0))
    fp.Value().SetLayer(pcbnew.F_Fab)
    fp.Value().SetTextSize(v(0.8, 0.8))
    fp.Value().SetTextThickness(mm(0.12))
    save_footprint(fp, "ESP32-C3_SuperMini")


def make_footprints():
    os.makedirs(FP_DIR, exist_ok=True)
    supermini_footprint()


if __name__ == "__main__":
    make_symbols()
    make_footprints()
