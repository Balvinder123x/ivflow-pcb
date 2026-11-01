"""Silkscreen labels for the IVFlow connectors (used by the Stage 4 board script).

Each connector gets a title naming what plugs into it and a label at every pin. The
texts are added to the footprint itself, so they move with the connector when it is
dragged in KiCad. Labels sit just outside the courtyard: silk under a connector body
is hidden once the part is soldered.

Call add_labels() right after loading a footprint, before positioning or rotating it
(it uses the footprint's own coordinates).
"""
import pcbnew

# ref: (title, labels in pin order; "" = no label for that pin)
CONNECTOR_LABELS = {
    "J1": ("BATTERY 3.7V", ["+", "-"]),
    "J2": ("LDR STRIP", ["+", "L1", "L2", "L3", "L4"]),     # "+" = 3V3 supply to the strip
    "J3": ("LED", ["+", "-"]),
    "J4": ("OLED", ["GND", "VCC", "SCL", "SDA"]),
    "J5": ("EXPANSION", ["GND", "VSYS", "3V3", "IO20", "IO21"]),
    "J6": ("POWER SWITCH", ["", ""]),
    "J7": ("BUZZER", ["+", "-"]),
    "J8": ("BUTTON", ["", ""]),
    "J9": ("CHARGER TP4056", ["IN+", "IN-", "B+", "B-", "OUT+", "OUT-"]),
}

# mm: text height, stroke width. JLCPCB minimum is 1.0 mm high, 0.15 mm stroke.
TITLE_H, TITLE_W = 1.2, 0.2
PIN_H, PIN_W = 1.0, 0.16
SIGN_H, SIGN_W = 1.4, 0.25    # "+" / "-" are drawn bigger so polarity is easy to see
GAP = 0.4


def _mm(v):
    return pcbnew.FromMM(v)


def _width(s, h):
    """Rough width of a KiCad stroke-font string (mm)."""
    return len(s) * 1.0 * h


def _text(fp, s, x, y, h, w, hjust=pcbnew.GR_TEXT_H_ALIGN_CENTER, angle=0):
    t = pcbnew.PCB_TEXT(fp)
    t.SetText(s)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(_mm(h), _mm(h)))
    t.SetTextThickness(_mm(w))
    t.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
    t.SetHorizJustify(hjust)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    if hasattr(t, "SetKeepUpright"):
        t.SetKeepUpright(True)
    t.SetPosition(pcbnew.VECTOR2I(_mm(x), _mm(y)))
    fp.Add(t)
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


def add_labels(fp, ref):
    """Add the title and pin labels for connector `ref` to footprint `fp` (at origin, unrotated)."""
    title, pin_labels = CONNECTOR_LABELS[ref]
    pads = sorted(((int(p.GetNumber()), pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
                   for p in fp.Pads()))
    if len(pads) != len(pin_labels):
        raise ValueError(f"{ref}: {len(pads)} pads but {len(pin_labels)} labels")
    left, top, right, bottom = _courtyard(fp)
    xs, ys = [p[1] for p in pads], [p[2] for p in pads]
    row_along_x = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    if row_along_x:
        # Pin labels in a line just below the body, title below them. Labels wider than the
        # pin pitch are turned 90 degrees and read downward from the body.
        y = bottom + GAP
        pitch = (max(xs) - min(xs)) / (len(pads) - 1)
        if any(len(s) > 1 and _width(s, PIN_H) > 0.9 * pitch for s in pin_labels):
            for (_, px, _), s in zip(pads, pin_labels):
                if s:
                    _text(fp, s, px, y, PIN_H, PIN_W, pcbnew.GR_TEXT_H_ALIGN_RIGHT, angle=90)
            y += max(_width(s, PIN_H) for s in pin_labels) + GAP
        elif any(pin_labels):
            row_h = max(SIGN_H if s in "+-" else PIN_H for s in pin_labels if s)
            for (_, px, _), s in zip(pads, pin_labels):
                if s:
                    sign = s in "+-"
                    _text(fp, s, px, y + row_h / 2, SIGN_H if sign else PIN_H, SIGN_W if sign else PIN_W)
            y += row_h + GAP
        _text(fp, title, (min(xs) + max(xs)) / 2, y + TITLE_H / 2, TITLE_H, TITLE_W)
    else:
        # Column of pins: labels to the left of each pin, title below the column
        for (_, _, py), s in zip(pads, pin_labels):
            if s:
                _text(fp, s, left - GAP, py, PIN_H, PIN_W, pcbnew.GR_TEXT_H_ALIGN_RIGHT)
        _text(fp, title, (min(xs) + max(xs)) / 2, bottom + GAP + TITLE_H / 2, TITLE_H, TITLE_W)
