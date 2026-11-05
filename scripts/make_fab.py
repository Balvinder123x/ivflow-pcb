"""Stage 6: manufacturing outputs for JLCPCB in fab/.

Runs ERC and DRC first and stops if either has errors. Then writes:
  fab/gerbers/                  Gerbers (Protel extensions, no X2), Excellon drill (PTH/NPTH), drill map
  fab/ivflow_gerbers_jlcpcb.zip the gerbers/ folder zipped, ready to upload
  fab/ivflow_bom_jlcpcb.csv     JLCPCB BOM: Comment, Designator, Footprint, LCSC Part # (on-board, no DNP)
  fab/ivflow_bom_full.csv       every schematic part incl. DNP and the off-board TP4056
  fab/ivflow_cpl_jlcpcb.csv     pick-and-place: Designator, Mid X, Mid Y, Layer, Rotation (no DNP)
  fab/ivflow_render_top.png / ivflow_render_bottom.png   3D renders
  fab/ivflow_schematic.pdf      schematic
  fab/ivflow_assembly_top_1to1.pdf  assembly drawing at 1:1 (pad outlines, holes, references,
                                values): for hand soldering, and printed at 100 % to check the
                                real SuperMini against its footprint before ordering

Run with KiCad's bundled Python:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts\\make_fab.py
"""
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRJ = os.path.join(ROOT, "ivflow")
PCB = os.path.join(PRJ, "ivflow.kicad_pcb")
SCH = os.path.join(PRJ, "ivflow.kicad_sch")
FAB = os.path.join(ROOT, "fab")
GERBERS = os.path.join(FAB, "gerbers")
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
GERBER_LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"


def cli(*args):
    r = subprocess.run([KICAD_CLI, *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"kicad-cli {' '.join(args[:3])} failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout


# ---------------------------------------------------------------- checks
def checks(tmp):
    erc = os.path.join(tmp, "erc.rpt")
    subprocess.run([KICAD_CLI, "sch", "erc", "--severity-all", "-o", erc, SCH], capture_output=True)
    m = re.search(r"ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)", open(erc, encoding="utf-8").read())
    drc = os.path.join(tmp, "drc.rpt")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--schematic-parity", "--severity-all", "-o", drc, PCB],
                   capture_output=True)
    text = open(drc, encoding="utf-8").read()
    found = dict((k, int(n)) for n, k in re.findall(r"\*\* Found (\d+) ([A-Za-z ]+?) \*\*", text))
    print(f"ERC: {m.group(2)} errors, {m.group(3)} warnings")
    print(f"DRC: {found.get('DRC violations')} violations, {found.get('unconnected pads')} unconnected pads, "
          f"{found.get('Footprint errors')} footprint errors")
    if int(m.group(2)) or int(m.group(3)) or any(found.values()):
        raise SystemExit("checks not clean: fix them before generating fab outputs")


# ---------------------------------------------------------------- outputs
def gerbers():
    os.makedirs(GERBERS)
    cli("pcb", "export", "gerbers", "-o", GERBERS, "--layers", GERBER_LAYERS, "--subtract-soldermask",
        "--no-x2", "--exclude-value", "--check-zones", PCB)
    cli("pcb", "export", "drill", "-o", GERBERS, "--format", "excellon", "--drill-origin", "absolute",
        "--excellon-units", "mm", "--excellon-zeros-format", "decimal", "--excellon-oval-format", "alternate",
        "--excellon-separate-th", "--generate-map", "--map-format", "gerberx2", PCB)
    files = sorted(os.listdir(GERBERS))
    zpath = os.path.join(FAB, "ivflow_gerbers_jlcpcb.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(GERBERS, f), f)
    print(f"gerbers + drill: {len(files)} files -> {os.path.relpath(zpath, ROOT)}")
    for f in files:
        print(f"    {f}")


def boms(tmp):
    raw = os.path.join(tmp, "bom.csv")
    cli("sch", "export", "bom", "-o", raw, "--fields", "Value,Reference,Footprint,LCSC,${QUANTITY},${DNP}",
        "--labels", "Value,Designator,Footprint,LCSC,Qty,DNP", "--group-by", "Value,Footprint,LCSC,${DNP}",
        "--ref-range-delimiter", "", SCH)
    rows = list(csv.DictReader(open(raw, encoding="utf-8")))
    shutil.copy(raw, os.path.join(FAB, "ivflow_bom_full.csv"))
    jlc = [r for r in rows if r["Footprint"] and not r["DNP"]]
    with open(os.path.join(FAB, "ivflow_bom_jlcpcb.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for r in jlc:
            w.writerow([r["Value"], r["Designator"], r["Footprint"].split(":")[-1], r["LCSC"]])
    print(f"BOM: {len(jlc)} lines for JLCPCB (on-board, DNP excluded), {len(rows)} lines in the full BOM")


def cpl(tmp):
    raw = os.path.join(tmp, "pos.csv")
    cli("pcb", "export", "pos", "-o", raw, "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", PCB)
    rows = list(csv.DictReader(open(raw, encoding="utf-8")))
    with open(os.path.join(FAB, "ivflow_cpl_jlcpcb.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            w.writerow([r["Ref"], f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm",
                        "Top" if r["Side"] == "top" else "Bottom", f"{float(r['Rot']):g}"])
    print(f"pick-and-place: {len(rows)} parts")


def documents():
    cli("sch", "export", "pdf", "-o", os.path.join(FAB, "ivflow_schematic.pdf"), SCH)
    # Copper is left out on purpose: the GND pour would turn the print solid black
    cli("pcb", "export", "pdf", "--mode-single", "-o", os.path.join(FAB, "ivflow_assembly_top_1to1.pdf"),
        "--layers", "F.Fab,F.Silkscreen,Edge.Cuts", "--include-border-title", "--sketch-pads-on-fab-layers",
        "--crossout-DNP-footprints-on-fab-layers", "--black-and-white", "--scale", "1",
        "--drill-shape-opt", "2", PCB)
    for side in ("top", "bottom"):
        cli("pcb", "render", "--side", side, "--quality", "high", "--background", "opaque",
            "-o", os.path.join(FAB, f"ivflow_render_{side}.png"), PCB)
    print("documents: schematic PDF, 1:1 assembly drawing, 3D renders top/bottom")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        checks(tmp)
        # Clear old outputs but keep the hand-written README
        os.makedirs(FAB, exist_ok=True)
        for name in os.listdir(FAB):
            path = os.path.join(FAB, name)
            if name != "README.md":
                shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
        gerbers()
        boms(tmp)
        cpl(tmp)
        documents()
    print(f"done: {FAB}")
