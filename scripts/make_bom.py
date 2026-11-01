"""Stage 3: export the IVFlow BOM from the schematic, plus the list of off-board parts.

The board BOM comes straight from the schematic (Reference, Value, Footprint, LCSC
fields) via kicad-cli, so it stays correct after the schematic is edited in KiCad.
Off-board parts (things plugged into the connectors, cable housings, hardware) are
not schematic symbols and are listed separately.

Run with KiCad's bundled Python:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts\\make_bom.py [--out DIR]
"""
import csv
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(ROOT, "ivflow")
SCH = os.path.join(OUT, "ivflow.kicad_sch")
BOM_DIR = os.path.join(OUT, "bom")
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"

# Off-board / mechanical parts: (qty, item, used with, note). LCSC left blank where no
# specific part has been checked; these are generic and easy to buy locally.
OFFBOARD = [
    (2, "Female header 1x8, 2.54 mm, straight", "U1", "Socket for the ESP32-C3 SuperMini"),
    (1, "JST-XH 6-pin cable, pre-crimped (22-24 AWG)", "J9 / U2", "Solder to TP4056: 1 IN+, 2 IN-, 3 B+, 4 B-, 5 OUT+, 6 OUT-"),
    (1, "Li-Po battery 3.7 V with JST-PH 2.0 plug", "J1", "Check red wire = pin 1 (BATT+)"),
    (1, "LDR strip (4x LDR, e.g. GL5528) on a 5-wire cable", "J2", "Cable order: +3V3, LDR1..LDR4"),
    (1, "5 mm LED, green or red (standard brightness)", "J3", "Pin 1 = anode (+, long leg); white/blue too dim at 3.3 V"),
    (1, "0.96in I2C OLED module (SSD1306) + 4 female-female jumper wires", "J4", "Wire GND, VCC, SCL, SDA"),
    (1, "Panel-mount power switch, rated >= 1 A (toggle or rocker)", "J6", "Wired across J6; closed = ON"),
    (1, "Active buzzer 3-5 V, 12 mm", "J7", "Pin 1 = +, pin 2 = -"),
    (1, "Momentary push button, panel-mount", "J8", "Wired across J8"),
    (4, "JST-XH 2-pin housing (XHP-2)", "J3, J6, J7, J8", "Or pre-crimped XH 2-pin cables"),
    (1, "JST-XH 5-pin housing (XHP-5)", "J2", "Or a pre-crimped XH 5-pin cable"),
    (1, "JST-XH 6-pin housing (XHP-6)", "J9", "Or the pre-crimped 6-pin cable above"),
    (19, "JST-XH crimp contact (SXH-001T-P0.6)", "J2, J3, J6, J7, J8, J9", "Not needed with pre-crimped cables"),
    (4, "M2 screw + standoff", "mounting holes", ""),
]


def main():
    os.makedirs(BOM_DIR, exist_ok=True)
    board = os.path.join(BOM_DIR, "ivflow_bom.csv")
    subprocess.run([KICAD_CLI, "sch", "export", "bom", "-o", board,
                    "--fields", "Reference,Value,Footprint,LCSC,${QUANTITY},${DNP}",
                    "--labels", "Designator,Value,Footprint,LCSC,Qty,DNP",
                    "--group-by", "Value,Footprint,LCSC,${DNP}", "--ref-range-delimiter", "",
                    SCH], check=True, capture_output=True)
    print(f"wrote: {board}")

    offboard = os.path.join(BOM_DIR, "ivflow_offboard.csv")
    with open(offboard, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Qty", "Item", "Used with", "Note"])
        w.writerows(OFFBOARD)
    print(f"wrote: {offboard}")

    with open(board, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    missing = [r["Designator"] for r in rows if not r["LCSC"]]
    total = sum(int(r["Qty"]) for r in rows)
    print(f"board BOM: {len(rows)} lines, {total} parts; without LCSC number: {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    main()
