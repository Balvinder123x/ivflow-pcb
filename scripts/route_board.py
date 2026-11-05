"""Stage 5: autoroute the IVFlow board with Freerouting, then add GND pours and stitching vias.

Steps: export Specctra DSN -> freerouting-cli -> import the session (.ses) -> GND zones on
F.Cu and B.Cu -> stitching vias on a ~5 mm grid where both pours are solid -> refill ->
DRC with schematic parity.

Run with KiCad's bundled Python, with KiCad closed:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts\\route_board.py [--out DIR] [--force]

Refuses to touch a board that already has tracks unless --force is given (once the board
is edited in KiCad, make targeted edits instead).
"""
import math
import os
import subprocess
import sys

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(ROOT, "ivflow")
PCB = os.path.join(OUT, "ivflow.kicad_pcb")
DSN = os.path.join(OUT, "ivflow.dsn")
SES = os.path.join(OUT, "ivflow.ses")
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
# Freerouting 2.5.0 (official release jar) needs Java 25: a portable Temurin 25 JRE lives in
# tools/ (git-ignored). The native freerouting-cli build of 2.5.0 crashes on this board.
FREEROUTING_JAR = os.path.join(ROOT, "tools", "freerouting", "freerouting-2.5.0.jar")
JAVA = os.path.join(ROOT, "tools", "jre25", "jdk-25.0.5+8-jre", "bin", "java.exe")
FORCE = "--force" in sys.argv

PASSES = 100                 # Freerouting max auto-routing passes
ZONE_CLEARANCE = 0.3         # mm, pour to other nets
ZONE_MIN_WIDTH = 0.25        # mm
THERMAL_GAP, THERMAL_SPOKE = 0.4, 0.5
STITCH_PITCH = 5.0           # mm, GND via grid
STITCH_SEARCH = 1.5          # mm, how far a stitching via may move off its grid point
VIA_D, VIA_DRILL = 0.6, 0.3  # mm
PAD_GAP = 0.25               # mm, stitching via copper to any pad
HOLE_GAP = 0.5               # mm, hole to hole (project rule)


def mm(v):
    return pcbnew.FromMM(v)


# ---------------------------------------------------------------- routing
def autoroute(board):
    if not pcbnew.ExportSpecctraDSN(board, DSN):
        raise SystemExit("DSN export failed")
    print(f"exported: {DSN}")
    if os.path.exists(SES):
        os.remove(SES)
    log = os.path.join(OUT, "freerouting.log")
    with open(log, "w", encoding="utf-8") as lf:
        subprocess.run([JAVA, "-jar", FREEROUTING_JAR, "--gui.enabled=false", "-de", DSN, "-do", SES,
                        f"--router.autorouter.max_passes={PASSES}"],
                       stdout=lf, stderr=subprocess.STDOUT, cwd=OUT, check=False, timeout=1800)
    with open(log, encoding="utf-8") as lf:
        done = [line.strip() for line in lf if "Auto-routing stage completed" in line]
    print(done[-1][done[-1].find("Auto-routing"):] if done else f"(no routing summary; see {log})")
    if not os.path.exists(SES):
        raise SystemExit(f"Freerouting produced no session file; see {log}")
    if not pcbnew.ImportSpecctraSES(board, SES):
        raise SystemExit("session import failed")
    print(f"imported: {SES} ({len(board.GetTracks())} tracks/vias)")


# ---------------------------------------------------------------- pours
def add_gnd_zones(board):
    gnd = board.FindNet("GND")
    box = board.GetBoardEdgesBoundingBox()
    zones = []
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetZoneName(f"GND_{board.GetLayerName(layer).replace('.', '_')}")
        o = z.Outline()
        o.NewOutline()
        for x, y in ((box.GetLeft(), box.GetTop()), (box.GetRight(), box.GetTop()),
                     (box.GetRight(), box.GetBottom()), (box.GetLeft(), box.GetBottom())):
            o.Append(x, y)
        z.SetLocalClearance(mm(ZONE_CLEARANCE))
        z.SetMinThickness(mm(ZONE_MIN_WIDTH))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(mm(THERMAL_GAP))
        z.SetThermalReliefSpokeWidth(mm(THERMAL_SPOKE))
        board.Add(z)
        zones.append(z)
    return zones


def fill(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


# ---------------------------------------------------------------- stitching
def stitch(board, zones):
    """GND vias on a grid, each fully inside the solid GND pour on both layers."""
    gnd = board.FindNet("GND")
    box = board.GetBoardEdgesBoundingBox()
    holes = []        # (x, y, radius) of every drilled hole
    pads = list(board.GetPads())
    for p in pads:
        if p.HasHole():
            holes.append((p.GetPosition().x, p.GetPosition().y, p.GetDrillSize().x / 2))
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            holes.append((t.GetPosition().x, t.GetPosition().y, t.GetDrillValue() / 2))

    r = mm(VIA_D / 2)
    ring = [(math.cos(a) * (r + mm(0.05)), math.sin(a) * (r + mm(0.05)))
            for a in [i * math.pi / 6 for i in range(12)]]

    def ok(x, y):
        for z in zones:
            for dx, dy in [(0, 0)] + ring:
                if not z.HitTestFilledArea(z.GetLayer(), pcbnew.VECTOR2I(int(x + dx), int(y + dy))):
                    return False
        for hx, hy, hr in holes:
            if math.hypot(hx - x, hy - y) < hr + mm(VIA_DRILL / 2 + HOLE_GAP):
                return False
        for p in pads:
            for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(layer) and p.GetEffectiveShape(layer).Collide(
                        pcbnew.VECTOR2I(int(x), int(y)), r + mm(PAD_GAP)):
                    return False
        return True

    offsets = sorted({(dx, dy) for dx in range(-6, 7) for dy in range(-6, 7)},
                     key=lambda d: d[0] ** 2 + d[1] ** 2)
    step = mm(STITCH_SEARCH / 6)
    added = 0
    nx = int(pcbnew.ToMM(box.GetWidth()) // STITCH_PITCH)
    ny = int(pcbnew.ToMM(box.GetHeight()) // STITCH_PITCH)
    x0 = box.GetLeft() + (box.GetWidth() - (nx - 1) * mm(STITCH_PITCH)) // 2
    y0 = box.GetTop() + (box.GetHeight() - (ny - 1) * mm(STITCH_PITCH)) // 2
    for i in range(nx):
        for j in range(ny):
            gx, gy = x0 + i * mm(STITCH_PITCH), y0 + j * mm(STITCH_PITCH)
            for dx, dy in offsets:
                x, y = gx + dx * step, gy + dy * step
                if ok(x, y):
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
                    v.SetWidth(mm(VIA_D))
                    v.SetDrill(mm(VIA_DRILL))
                    v.SetNet(gnd)
                    board.Add(v)
                    holes.append((x, y, mm(VIA_DRILL / 2)))
                    added += 1
                    break
    return added


# ---------------------------------------------------------------- checks
def run_drc():
    rpt = os.path.join(OUT, "ivflow_drc.rpt")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--schematic-parity", "--severity-all", "-o", rpt, PCB],
                   capture_output=True)
    with open(rpt, encoding="utf-8") as f:
        text = f.read()
    print("\n".join(line for line in text.splitlines() if line.startswith("** Found")))
    print(f"full report: {rpt}")
    return rpt


if __name__ == "__main__":
    board = pcbnew.LoadBoard(PCB)
    if len(board.GetTracks()) and not FORCE:
        raise SystemExit(f"{PCB} already has tracks; refusing to reroute (use --force)")
    # Delete (not Remove): Remove leaves orphaned objects that break pcbnew's SWIG types
    for t in list(board.GetTracks()):
        board.Delete(t)
    for z in list(board.Zones()):
        if not z.GetIsRuleArea():
            board.Delete(z)
    autoroute(board)
    zones = add_gnd_zones(board)
    fill(board)
    n = stitch(board, zones)
    fill(board)
    print(f"GND pours on F.Cu/B.Cu, {n} stitching vias")
    pcbnew.SaveBoard(PCB, board, True)
    print(f"wrote: {PCB}")
    run_drc()
