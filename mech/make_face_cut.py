"""Laser-cut outline of the IVFlow front face (2 mm black smoked acrylic) as DXF and SVG,
from the same numbers as mech/fusion_enclosure_v2.py (glass_shape with 0.15 mm clearance).

    python mech/make_face_cut.py   ->  mech/export/ivflow_face_2mm_smoked_acrylic.dxf / .svg
"""
import math
import os

W, H, R, Hf = 54.0, 146.0, 12.0, 137.0
NOTCH_W, GLASS_INSET, CLEAR = 18.0, 3.5, 0.15

gi = GLASS_INSET + CLEAR                 # 3.65 mm inside the body outline
x0, x1, y0, y1 = -W / 2 + gi, W / 2 - gi, gi, H - gi
r = R - gi                               # outer corner radius 8.35
nh = NOTCH_W / 2 + gi                    # notch half width 12.65
off = nh - NOTCH_W / 2
floor, rc = Hf - off, 3.0 + off          # notch floor 133.35, corner radius 6.65

# outline as (kind, data): ("L", (xa, ya, xb, yb)) or ("A", (cx, cy, r, a_start, a_end)) CCW degrees
seg = [
    ("L", (x0 + r, y0, x1 - r, y0)),
    ("A", (x1 - r, y0 + r, r, 270, 360)),
    ("L", (x1, y0 + r, x1, y1 - r)),
    ("A", (x1 - r, y1 - r, r, 0, 90)),
    ("L", (x1 - r, y1, nh, y1)),
    ("L", (nh, y1, nh, floor + rc)),
    ("A", (nh - rc, floor + rc, rc, 270, 360)),     # drawn CCW = notch corner (concave)
    ("L", (nh - rc, floor, -nh + rc, floor)),
    ("A", (-nh + rc, floor + rc, rc, 180, 270)),
    ("L", (-nh, floor + rc, -nh, y1)),
    ("L", (-nh, y1, x0 + r, y1)),
    ("A", (x0 + r, y1 - r, r, 90, 180)),
    ("L", (x0, y1 - r, x0, y0 + r)),
    ("A", (x0 + r, y0 + r, r, 180, 270)),
]
SHIFT = W / 2                            # put the drawing at x >= 0


def dxf(path):
    out = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
           "0", "SECTION", "2", "ENTITIES"]
    for kind, d in seg:
        if kind == "L":
            xa, ya, xb, yb = d
            out += ["0", "LINE", "8", "CUT", "10", f"{xa + SHIFT:.4f}", "20", f"{ya:.4f}", "30", "0",
                    "11", f"{xb + SHIFT:.4f}", "21", f"{yb:.4f}", "31", "0"]
        else:
            cx, cy, rr, a0, a1 = d
            out += ["0", "ARC", "8", "CUT", "10", f"{cx + SHIFT:.4f}", "20", f"{cy:.4f}", "30", "0",
                    "40", f"{rr:.4f}", "50", f"{a0:.4f}", "51", f"{a1:.4f}"]
    out += ["0", "ENDSEC", "0", "EOF"]
    open(path, "w").write("\n".join(out) + "\n")


def svg(path):
    """Same outline as one closed SVG path. Walking order = list order; a segment whose start
    does not meet the current point is walked backwards (the concave notch corners)."""
    def p(x, y):
        return f"{x + SHIFT:.3f},{H - y:.3f}"     # SVG y points down
    segs = []
    for kind, d in seg:
        if kind == "L":
            segs.append(((d[0], d[1]), (d[2], d[3]), None))
        else:
            cx, cy, rr, a0, a1 = d
            segs.append(((cx + rr * math.cos(math.radians(a0)), cy + rr * math.sin(math.radians(a0))),
                         (cx + rr * math.cos(math.radians(a1)), cy + rr * math.sin(math.radians(a1))), rr))
    cur = segs[0][0]
    d_attr = [f"M {p(*cur)}"]
    for s0, e0, rr in segs:
        ccw = True
        if math.dist(cur, s0) > 1e-3:          # stored reversed: walk it clockwise
            s0, e0, ccw = e0, s0, False
        assert math.dist(cur, s0) < 1e-3, "outline is not continuous"
        if rr is None:
            d_attr.append(f"L {p(*e0)}")
        else:            # y is flipped in both coords and display, so math-CCW stays CCW: sweep 0
            d_attr.append(f"A {rr:.3f},{rr:.3f} 0 0,{0 if ccw else 1} {p(*e0)}")
        cur = e0
    d_attr.append("Z")
    open(path, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n'
        f'<!-- IVFlow front face: 2 mm black smoked acrylic. Red hairline = cut. -->\n'
        f'<path d="{" ".join(d_attr)}" fill="none" stroke="#ff0000" stroke-width="0.05"/>\n</svg>\n')


if __name__ == "__main__":
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export")
    os.makedirs(here, exist_ok=True)
    dxf(os.path.join(here, "ivflow_face_2mm_smoked_acrylic.dxf"))
    svg(os.path.join(here, "ivflow_face_2mm_smoked_acrylic.svg"))
    print(f"face {x1 - x0:.2f} x {y1 - y0:.2f} mm, corner R{r:.2f}, notch {2 * nh:.2f} wide, "
          f"floor {y1 - floor:.2f} below the top")
