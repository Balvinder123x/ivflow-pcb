"""Silkscreen labels for the IVFlow connectors (used by scripts/make_board.py).

Each connector gets one short, easy-to-recognise name plus a mark at every pin, e.g.
"BAT + -" or "LDR + 1 2 3 4". The reference designator (J1...) is moved to the fab
layer, so it still appears on the assembly drawing but not on the silkscreen.

The texts are added to the footprint itself, so they move with the connector when it is
dragged in KiCad. add_labels() works in board coordinates: call it after the footprint
has been placed and rotated.
"""
import pcbnew

# ref: (name, marks in pin order; "" = no mark for that pin)
CONNECTOR_LABELS = {
    "J1": ("BAT", ["+", "-"]),                                  # Li-Po battery
    "J2": ("LDR", ["+", "1", "2", "3", "4"]),                   # LDR strip: + = 3V3, 1-4 = LDR1-4
    "J3": ("LED", ["+", "-"]),
    "J4": ("OLED", ["G", "V", "C", "D"]),                       # GND, VCC, SCL (clock), SDA (data)
    "J5": ("EXP", ["G", "VS", "3V", "20", "21"]),               # GND, VSYS, 3V3, GPIO20, GPIO21
    "J6": ("SW", ["", ""]),                                     # power switch
    "J7": ("BZ", ["+", "-"]),                                   # buzzer
    "J8": ("BTN", ["", ""]),                                    # push button
    "J9": ("CHG", ["I+", "I-", "B+", "B-", "O+", "O-"]),        # TP4056 charger: IN, BAT, OUT
}

# mm: text height, stroke width. JLCPCB minimum is 1.0 mm high, 0.15 mm stroke.
NAME_H, NAME_W = 1.2, 0.2
PIN_H, PIN_W = 1.0, 0.16
SIGN_H, SIGN_W = 1.4, 0.25    # "+" / "-" are drawn bigger so polarity is easy to see
GAP = 0.4
L, R, C = pcbnew.GR_TEXT_H_ALIGN_LEFT, pcbnew.GR_TEXT_H_ALIGN_RIGHT, pcbnew.GR_TEXT_H_ALIGN_CENTER


def _mm(v):
    return pcbnew.FromMM(v)


def _width(s, h):
    """Rough width of a KiCad stroke-font string (mm)."""
    return len(s) * 1.0 * h


def _size(s):
    """(height, stroke) for a pin mark."""
    return (SIGN_H, SIGN_W) if s in ("+", "-") else (PIN_H, PIN_W)


def _text(fp, s, x, y, h, w, hjust=C, angle=0):
    t = pcbnew.PCB_TEXT(fp)
    t.SetText(s)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(_mm(h), _mm(h)))
    t.SetTextThickness(_mm(w))
    t.SetHorizJustify(hjust)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    if hasattr(t, "SetKeepUpright"):
        t.SetKeepUpright(True)
    fp.Add(t)
    t.SetPosition(pcbnew.VECTOR2I(_mm(x), _mm(y)))
    t.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
    return t


def _courtyard(fp):
    box = None
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            if box is None:
                box = g.GetBoundingBox()
            else:
                box.Merge(g.GetBoundingBox())
    return [pcbnew.ToMM(v) for v in (box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom())]


def add_labels(fp, ref, side=None):
    """Add the name and pin marks for connector `ref` to the placed footprint `fp`.

    side: "below"/"above" for a horizontal pin row (one text line next to the body; add
    "-right" to put the name after the marks instead of before them), "left"/"right" for a
    vertical row (marks beside the pins, name turned 90 degrees beyond them).
    """
    name, marks = CONNECTOR_LABELS[ref]
    pads = {}
    for p in fp.Pads():
        pads[int(p.GetNumber())] = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
    pads = [pads[n] for n in sorted(pads)]
    if len(pads) != len(marks):
        raise ValueError(f"{ref}: {len(pads)} pads but {len(marks)} marks")
    left, top, right, bottom = _courtyard(fp)
    xs, ys = [p[0] for p in pads], [p[1] for p in pads]
    marked = [(p, s) for p, s in zip(pads, marks) if s]

    # The J-number stays on the assembly drawing only
    fp.Reference().SetLayer(pcbnew.F_Fab)

    if (max(xs) - min(xs)) >= (max(ys) - min(ys)):
        side = side or "below"
        name_after = side.endswith("-right")
        line_h = max([NAME_H] + [_size(s)[0] for _, s in marked])
        y = bottom + GAP + line_h / 2 if side.startswith("below") else top - GAP - line_h / 2
        for (px, _), s in marked:
            _text(fp, s, px, y, *_size(s))
        if not marked:
            _text(fp, name, (min(xs) + max(xs)) / 2, y, NAME_H, NAME_W)
        elif name_after:
            (px, _), s = marked[-1]
            _text(fp, name, px + _width(s, _size(s)[0]) / 2 + GAP, y, NAME_H, NAME_W, L)
        else:
            (px, _), s = marked[0]
            _text(fp, name, px - _width(s, _size(s)[0]) / 2 - GAP, y, NAME_H, NAME_W, R)
    else:
        side = side or "left"
        sgn, x = (-1, left - GAP) if side == "left" else (1, right + GAP)
        for (_, py), s in marked:
            _text(fp, s, x, py, *_size(s), hjust=R if sgn < 0 else L)
        if marked:
            x += sgn * (max(_width(s, _size(s)[0]) for _, s in marked) + GAP)
        _text(fp, name, x + sgn * NAME_H / 2, (min(ys) + max(ys)) / 2, NAME_H, NAME_W, angle=90)
