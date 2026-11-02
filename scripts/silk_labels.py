"""Silkscreen labels for the IVFlow connectors (used by scripts/make_board.py).

Each connector gets a title naming what plugs into it and a label at every pin. The
texts are added to the footprint itself, so they move with the connector when it is
dragged in KiCad. Labels sit just outside the courtyard: silk under a connector body
is hidden once the part is soldered.

add_labels() works in board coordinates, so call it after the footprint has been
placed and rotated.
"""
import pcbnew

# ref: (title, labels in pin order; "" = no label for that pin)
CONNECTOR_LABELS = {
    "J1": ("BATTERY", ["+", "-"]),
    "J2": ("LDR STRIP", ["+", "L1", "L2", "L3", "L4"]),     # "+" = 3V3 supply to the strip
    "J3": ("LED", ["+", "-"]),
    "J4": ("OLED", ["GND", "VCC", "SCL", "SDA"]),
    "J5": ("EXPANSION", ["GND", "VSYS", "3V3", "IO20", "IO21"]),
    "J6": ("POWER SW", ["", ""]),
    "J7": ("BUZZER", ["+", "-"]),
    "J8": ("BUTTON", ["", ""]),
    "J9": ("CHARGER", ["IN+", "IN-", "B+", "B-", "OUT+", "OUT-"]),
}

# mm: text height, stroke width. JLCPCB minimum is 1.0 mm high, 0.15 mm stroke.
TITLE_H, TITLE_W = 1.2, 0.2
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
    """(height, stroke) for a pin label."""
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


def _ref_after_title(fp, title, x, y, angle):
    """Move the footprint's reference text to just after the title, same direction."""
    ref = fp.Reference()
    ref.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    ref.SetHorizJustify(L)
    ref.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
    offset = _width(title, TITLE_H) / 2 + GAP + 0.2
    if angle == 90:     # reads upward: "after" is above
        ref.SetPosition(pcbnew.VECTOR2I(_mm(x), _mm(y - offset)))
    else:
        ref.SetPosition(pcbnew.VECTOR2I(_mm(x + offset), _mm(y)))


def add_labels(fp, ref, side=None):
    """Add the title and pin labels for connector `ref` to the placed footprint `fp`.

    side: where the labels go. "below" (default) or "above" for a horizontal pin row,
    "left" (default) or "right" for a vertical one. A horizontal row gets its title
    under/over the pin labels; a vertical row gets it turned 90 degrees beside them.
    The reference designator (J1...) is moved to just after the title.
    """
    title, pin_labels = CONNECTOR_LABELS[ref]
    pads = {}
    for p in fp.Pads():
        pads[int(p.GetNumber())] = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
    pads = [pads[n] for n in sorted(pads)]
    if len(pads) != len(pin_labels):
        raise ValueError(f"{ref}: {len(pads)} pads but {len(pin_labels)} labels")
    left, top, right, bottom = _courtyard(fp)
    xs, ys = [p[0] for p in pads], [p[1] for p in pads]
    labelled = [(p, s) for p, s in zip(pads, pin_labels) if s]

    if (max(xs) - min(xs)) >= (max(ys) - min(ys)):
        # Horizontal row: pin labels in a line next to the body, title beyond them.
        # Labels wider than the pin pitch are turned 90 degrees.
        side = side or "below"
        sgn, y = (1, bottom + GAP) if side == "below" else (-1, top - GAP)
        pitch = (max(xs) - min(xs)) / (len(pads) - 1)
        if any(len(s) > 1 and _width(s, PIN_H) > 0.9 * pitch for _, s in labelled):
            for (px, _), s in labelled:
                _text(fp, s, px, y, PIN_H, PIN_W, R if sgn > 0 else L, angle=90)
            y += sgn * (max(_width(s, PIN_H) for _, s in labelled) + GAP)
        elif labelled:
            row_h = max(_size(s)[0] for _, s in labelled)
            for (px, _), s in labelled:
                _text(fp, s, px, y + sgn * row_h / 2, *_size(s))
            y += sgn * (row_h + GAP)
        tx, ty = (min(xs) + max(xs)) / 2, y + sgn * TITLE_H / 2
        _text(fp, title, tx, ty, TITLE_H, TITLE_W)
        _ref_after_title(fp, title, tx, ty, 0)
    else:
        # Vertical row: pin labels beside each pin, title turned 90 degrees beyond them
        side = side or "left"
        sgn, x = (-1, left - GAP) if side == "left" else (1, right + GAP)
        for (_, py), s in labelled:
            _text(fp, s, x, py, *_size(s), hjust=R if sgn < 0 else L)
        if labelled:
            x += sgn * (max(_width(s, _size(s)[0]) for _, s in labelled) + GAP)
        tx, ty = x + sgn * TITLE_H / 2, (min(ys) + max(ys)) / 2
        _text(fp, title, tx, ty, TITLE_H, TITLE_W, angle=90)
        _ref_after_title(fp, title, tx, ty, 90)
