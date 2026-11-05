"""IVFlow enclosure v2: Fusion 360 API script (run with `python scripts/fusion_mcp.py script
mech/fusion_enclosure_v2.py`, or from Fusion's Scripts and Add-Ins dialog).

Style (user's inspiration, 2026-11-05): tall, slim, soft rounded shape; the whole front is
one smoked (dark see-through) acrylic face with the OLED glowing behind it; a short U-notch
at the top where the spike cap sits; the sensing zone itself is fully enclosed (light-tight).

Parts (everything mounts into the black chassis, the white back shell closes it):
  Chassis (black)   front frame + sensor head in one print: OLED frame, PCB standoffs,
                    battery cradle; head with the chamber channel, top fork, tube slot, LED
                    and LDR pockets that are filled FROM THE OUTSIDE (side recesses), wire
                    holes from the recesses down into the electronics space
  LED cover, LDR cover (black)  flush plates over the side recesses, 1 x M2 each
  Door (black)      hinged on the left (seen from the back), magnetic catch
  Back shell (white)  lower back; 4 x M2 screws through the PCB holes into the chassis
                    standoffs; TP4056 holder + USB-C hole, button, switch, buzzer
  Face (smoked acrylic, 2 mm, laser cut)  glued into the front recess

Coordinates (mm): X = width (+X right seen from the front), Y = depth (front face Y = 0),
Z = height (bottom Z = 0). Edit P and run again; it rebuilds "IVFlow enclosure v2".
"""
import math
import traceback

import adsk.core
import adsk.fusion

DOC_NAME = "IVFlow enclosure v2"
PCB_STEP = r"C:\Users\bk823\Documents\IVFlow-PCB\mech\ivflow_pcb.step"

P = dict(
    W=54.0, wall=2.0,
    R=12.0,                    # front-view corner radius
    r=3.0,                     # edge rounding of the front and back faces
    Hf=137.0,                  # holder top = notch floor (chamber top + 3)
    notch_d=9.0, notch_w=18.0,  # U-notch for the spike cap
    front_wall=4.0,            # front wall incl. the acrylic recess
    glass_t=2.0, glass_inset=3.5,
    split_y=13.0,              # chassis / back shell split (lower part)
    D_low=38.0, D_top=58.0, bz0=79.0,   # lower depth, head depth, head bottom
    # drip chamber (measured by the user) and holder
    chamber_d=17.5, chamber_l=49.5, holder_above_chamber=3.0, foam_t=4.0,
    axis_y=42.0,               # chamber axis: behind the lower body so the tube hangs free
    channel_half=13.0, chamfer=3.5,
    spike_slot=10.0, tube_slot=7.0,
    beam_from_top=13.5,
    led_hole=5.1, led_flange_d=6.2, led_tip_x=14.0,
    ldr_pocket_w=18.2, ldr_pocket_h=5.2, slit_h=1.2, slit_depth=3.0,
    recess_d=3.4, cover_t=1.6,
    door_t=4.0, door_tongue=3.25, magnet_d=6.2, magnet_h=3.2, magnet_z=97.0,
    # electronics
    pcb_w=46.0, pcb_h=41.5, pcb_t=1.6, pcb_y=8.0, pcb_z0=36.0,
    oled_board=(27.3, 27.8), oled_view=(22.0, 11.0), oled_z=110.0,
    button_hole=12.0, switch_hole=6.2,
)
P["H"] = P["Hf"] + P["notch_d"]
P["chamber_top"] = P["Hf"] - P["holder_above_chamber"]
P["beam_z"] = P["Hf"] - P["beam_from_top"]
P["yf"] = P["axis_y"] - P["channel_half"]          # channel front (foam on it)
HINGE = (-20.0, P["D_top"] + 2.6)

app = adsk.core.Application.get()
tb = adsk.fusion.TemporaryBRepManager.get()
UNION = adsk.fusion.BooleanTypes.UnionBooleanType
DIFF = adsk.fusion.BooleanTypes.DifferenceBooleanType
INTER = adsk.fusion.BooleanTypes.IntersectionBooleanType
SCRATCH = {}


def cm(v):
    return v / 10.0


def pt(x, y, z):
    return adsk.core.Point3D.create(cm(x), cm(y), cm(z))


def box(x0, y0, z0, x1, y1, z1):
    c = pt((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    obb = adsk.core.OrientedBoundingBox3D.create(
        c, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
        cm(abs(x1 - x0)), cm(abs(y1 - y0)), cm(abs(z1 - z0)))
    return tb.createBox(obb)


def rbox(cx, cy, z0, z1, length, width, angle_deg):
    a = math.radians(angle_deg)
    obb = adsk.core.OrientedBoundingBox3D.create(
        pt(cx, cy, (z0 + z1) / 2), adsk.core.Vector3D.create(math.cos(a), math.sin(a), 0),
        adsk.core.Vector3D.create(-math.sin(a), math.cos(a), 0), cm(length), cm(width), cm(z1 - z0))
    return tb.createBox(obb)


def cyl(p0, p1, r):
    return tb.createCylinderOrCone(pt(*p0), cm(r), pt(*p1), cm(r))


def sphere(c, r):
    return tb.createSphere(pt(*c), cm(r))


def add(a, *bs):
    for b in bs:
        tb.booleanOperation(a, b, UNION)
    return a


def sub(a, *bs):
    for b in bs:
        tb.booleanOperation(a, b, DIFF)
    return a


def inter(a, b):
    tb.booleanOperation(a, b, INTER)
    return a


def cp(b):
    return tb.copy(b)


def slot_xy(x_half, y0, y1, z0, z1, round_end_y):
    return add(box(-x_half, round_end_y, z0, x_half, y1, z1),
               cyl((0, round_end_y, z0), (0, round_end_y, z1), x_half))


def rrect_y(x0, x1, z0, z1, y0, y1, R):
    """Prism along Y whose front view is a rectangle with corner radius R."""
    b = add(box(x0 + R, y0, z0, x1 - R, y1, z1), box(x0, y0, z0 + R, x1, y1, z1 - R))
    for cx in (x0 + R, x1 - R):
        for cz in (z0 + R, z1 - R):
            add(b, cyl((cx, y0, cz), (cx, y1, cz), R))
    return b


def notch_cut(half):
    """Notch from the top through the whole depth: flat floor (the spike cap rests above it)
    with 3 mm rounded corners. half = notch_w / 2 puts the floor at Hf; a bigger half is the
    same outline offset outwards (used for the acrylic recess)."""
    off = half - P["notch_w"] / 2
    floor, rc = P["Hf"] - off, 3.0 + off
    b = add(box(-half + rc, -5, floor, half - rc, 80, P["H"] + 5),
            box(-half, -5, floor + rc, half, 80, P["H"] + 5))
    for sx in (-1, 1):
        add(b, cyl((sx * (half - rc), -5, floor + rc), (sx * (half - rc), 80, floor + rc), rc))
    return b


def rounded_solid(x0, x1, y0, y1, z0, z1, R, r):
    """rrect prism with its front and back face edges filleted (radius r), made with a real
    Fusion fillet in a scratch component, returned as a temporary body."""
    root = SCRATCH["root"]
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    base = comp.features.baseFeatures.add()
    base.startEdit()
    comp.bRepBodies.add(rrect_y(x0, x1, z0, z1, y0, y1, R), base)
    base.finishEdit()
    body = comp.bRepBodies.item(0)

    def is_cap(face):
        pl = adsk.core.Plane.cast(face.geometry)
        return pl is not None and abs(abs(pl.normal.y) - 1) < 1e-6

    edges = adsk.core.ObjectCollection.create()
    for i in range(body.edges.count):
        e = body.edges.item(i)
        caps = sum(1 for j in range(e.faces.count) if is_cap(e.faces.item(j)))
        if caps == 1:
            edges.add(e)
    fil = comp.features.filletFeatures
    fi = fil.createInput()
    val = adsk.core.ValueInput.createByReal(cm(r))
    try:
        fi.edgeSetInputs.addConstantRadiusEdgeSet(edges, val, True)
    except AttributeError:
        fi.addConstantRadiusEdgeSet(edges, val, True)
    fil.add(fi)
    out = tb.copy(comp.bRepBodies.item(0))
    occ.deleteMe()
    return out


# ---------------------------------------------------------------- shared shapes
def outer_shape():
    W2, R, r, bz0, H = P["W"] / 2, P["R"], P["r"], P["bz0"], P["H"]
    Dl, Dt = P["D_low"], P["D_top"]
    low = rounded_solid(-W2, W2, 0, Dl, 0, bz0 + 20, R, r)
    head = rounded_solid(-W2, W2, 0, Dt, bz0 - 20, H, R, r)
    sub(head, box(-W2 - 1, Dl, bz0 - 21, W2 + 1, Dt + 1, bz0 + r))   # underside of the head
    a = W2 - r                                                      # ...rounded again
    under = add(box(-a, Dl, bz0, a, Dt - r, bz0 + r),
                cyl((-a, Dl, bz0 + r), (-a, Dt - r, bz0 + r), r),
                cyl((a, Dl, bz0 + r), (a, Dt - r, bz0 + r), r),
                cyl((-a, Dt - r, bz0 + r), (a, Dt - r, bz0 + r), r),
                sphere((-a, Dt - r, bz0 + r), r), sphere((a, Dt - r, bz0 + r), r))
    sub(under, box(-W2 - 1, Dl - 5, bz0 + r, W2 + 1, Dt + 5, bz0 + 2 * r + 1))
    add(head, under)
    o = add(low, head)
    sub(o, notch_cut(P["notch_w"] / 2))
    return o


def interior():
    W2, w, bz0 = P["W"] / 2, P["wall"], P["bz0"]
    fw, Dl, R = P["front_wall"], P["D_low"], P["R"] - w
    lower = inter(rrect_y(-W2 + w, W2 - w, w, bz0 + 15, fw, Dl - w, R), box(-W2, 0, 0, W2, Dl, bz0))
    front_cav = rrect_y(-W2 + w, W2 - w, w, P["Hf"] - w, fw, P["yf"] - w, R)
    return add(lower, front_cav)


def glass_shape(clear, y0=0.0):
    """Acrylic face outline (clear = 0: the recess in the chassis)."""
    W2, gi, H, R = P["W"] / 2, P["glass_inset"] + clear, P["H"], P["R"]
    g = rrect_y(-W2 + gi, W2 - gi, gi, H - gi, y0, P["glass_t"], R - gi)
    sub(g, notch_cut(P["notch_w"] / 2 + gi))
    return g


def pcb_holes():
    hx, hz = P["pcb_w"] / 2 - 3.2, P["pcb_h"] / 2 - 3.2
    zc = P["pcb_z0"] + P["pcb_h"] / 2
    return [(sx, sz) for sx in (-hx, hx) for sz in (zc - hz, zc + hz)]


def side_recess(side):
    """(x0, x1, y0, y1, z0, z1) of the LED (-1, left) or LDR (+1, right) cover recess."""
    W2, bz = P["W"] / 2, P["beam_z"]
    y1 = 50.0 if side < 0 else 54.0
    xa, xb = W2 - P["recess_d"], W2 + 0.1
    return (-xb, -xa, 31.0, y1, bz - 8, bz + 8) if side < 0 else (xa, xb, 31.0, y1, bz - 8, bz + 8)


# ---------------------------------------------------------------- parts
def chassis_part(outer):
    W2, w, bz0, Hf, Dt = P["W"] / 2, P["wall"], P["bz0"], P["Hf"], P["D_top"]
    fw, sy = P["front_wall"], P["split_y"]
    c = inter(cp(outer), add(box(-W2 - 1, -1, -1, W2 + 1, sy, P["H"] + 1),
                             box(-W2 - 1, -1, bz0, W2 + 1, Dt + 5, P["H"] + 1)))
    sub(c, interior())
    sub(c, glass_shape(0.0, -1.0))                                        # acrylic face recess
    vw, vh = P["oled_view"]                                         # OLED window
    sub(c, box(-vw / 2 - 0.5, P["glass_t"] - 0.1, P["oled_z"] - vh / 2 - 0.5,
               vw / 2 + 0.5, fw + 0.1, P["oled_z"] + vh / 2 + 0.5))
    # OLED frame (module drops in from the back, held with a dab of glue / hot glue)
    ow, oh = P["oled_board"]
    oz = P["oled_z"] - 2
    frame = box(-ow / 2 - 1.4, fw - 0.1, oz - oh / 2 - 1.4, ow / 2 + 1.4, fw + 3.0, oz + oh / 2 + 1.4)
    sub(frame, box(-ow / 2 - 0.2, fw - 0.2, oz - oh / 2 - 0.2, ow / 2 + 0.2, fw + 3.1, oz + oh / 2 + 0.2))
    add(c, frame)
    # battery cradle: side ribs, top rib, bottom rest (battery 40 x 30 x 8 against the front wall)
    add(c, box(-21.5, fw - 0.1, 4, -20.3, 10, 34.2), box(20.3, fw - 0.1, 4, 21.5, 10, 34.2),
        box(-20, fw - 0.1, 34.4, 20, 10, 35.4), box(-14, fw - 0.1, w - 0.1, 14, 10, 4.1))
    # PCB standoffs (M2 pilot holes; the screws come from the back through the back shell)
    for sx, sz in pcb_holes():
        add(c, cyl((sx, fw - 0.1, sz), (sx, P["pcb_y"], sz), 2.5))
        sub(c, cyl((sx, fw + 0.8, sz), (sx, P["pcb_y"] + 0.1, sz), 0.8))
    # ---- sensor head
    ch, cf, ay, yf = P["channel_half"], P["chamfer"], P["axis_y"], P["yf"]
    z0, z1 = bz0 + 2.0, P["chamber_top"] + 0.5
    cut = box(-ch, yf, z0, ch, Dt + 0.1, z1)
    sub(cut, rbox(-ch, yf, z0 - 1, z1 + 1, cf * math.sqrt(2), cf * math.sqrt(2), 45),
        rbox(ch, yf, z0 - 1, z1 + 1, cf * math.sqrt(2), cf * math.sqrt(2), 45))
    sub(c, cut)
    sub(c, slot_xy(P["spike_slot"] / 2, ay, Dt + 0.1, z1 - 0.1, Hf + 0.1, ay))     # top fork
    sub(c, slot_xy(P["tube_slot"] / 2, ay, Dt + 0.1, bz0 - 1, z0 + 0.1, ay))       # tube slot
    bz = P["beam_z"]
    # side recesses for the covers + wire holes down to the electronics
    for s in (-1, 1):
        x0, x1, ry0, ry1, rz0, rz1 = side_recess(s)
        sub(c, box(x0, ry0, rz0, x1, ry1, rz1))
        gx0, gx1 = (-24.8, -21.8) if s < 0 else (21.8, 24.8)
        sub(c, box(gx0, 31.0, bz0 - 1, gx1, 34.0, rz0 + 0.1))
        # cover screw pilot hole
        sx = W2 - P["recess_d"]
        sub(c, cyl((s * (sx + 0.1), ry1 - 2.5, bz + 5.5), (s * (sx - 4.5), ry1 - 2.5, bz + 5.5), 0.8))
    # LED: 5.1 mm hole from the left recess to the channel, flange counterbore
    xr = W2 - P["recess_d"]
    sub(c, cyl((-xr - 0.1, ay, bz), (-ch + 0.1, ay, bz), P["led_hole"] / 2),
        cyl((-xr - 0.1, ay, bz), (-xr + 1.0, ay, bz), P["led_flange_d"] / 2))
    # LDR row: slit (1.2 x 18.2, 3 deep) from the channel, pocket 18.2 x 5.2 out to the recess
    pw, ph, sh, sd = P["ldr_pocket_w"], P["ldr_pocket_h"], P["slit_h"], P["slit_depth"]
    sub(c, box(ch - 0.1, ay - pw / 2, bz - sh / 2, ch + sd, ay + pw / 2, bz + sh / 2),
        box(ch + sd, ay - pw / 2, bz - ph / 2, xr + 0.1, ay + pw / 2, bz + ph / 2))
    # door hardware: magnet pocket (right), middle hinge knuckle (left)
    mz = P["magnet_z"]
    sub(c, cyl((19.75, Dt + 0.1, mz), (19.75, Dt - P["magnet_h"], mz), P["magnet_d"] / 2))
    kx, ky = HINGE
    add(c, box(kx - 2.5, Dt - 0.5, bz0 + 18.5, kx + 2.5, ky, bz0 + 39.5),
        cyl((kx, ky, bz0 + 18.5), (kx, ky, bz0 + 39.5), 2.5))
    sub(c, cyl((kx, ky, bz0 + 16), (kx, ky, bz0 + 42), 1.1))
    return c


def cover_part(side):
    x0, x1, ry0, ry1, rz0, rz1 = side_recess(side)
    W2, t, k = P["W"] / 2, P["cover_t"], 0.15
    xa, xb = (-W2, -W2 + t) if side < 0 else (W2 - t, W2)
    c = box(xa, ry0 + k, rz0 + k, xb, ry1 - k, rz1 - k)
    bz, sx = P["beam_z"], W2 - P["recess_d"]
    sub(c, cyl((side * (W2 + 0.1), ry1 - 2.5, bz + 5.5), (side * (W2 - t - 0.1), ry1 - 2.5, bz + 5.5), 1.1))
    return c


def back_shell_part(outer):
    W2, w, bz0, Dl, sy = P["W"] / 2, P["wall"], P["bz0"], P["D_low"], P["split_y"]
    b = inter(cp(outer), box(-W2 - 1, sy, -1, W2 + 1, Dl + 1, bz0))
    sub(b, interior())
    # screw columns through the PCB holes (M2 x 30 from the back into the chassis standoffs)
    yb = P["pcb_y"] + P["pcb_t"] + 0.2
    for sx, sz in pcb_holes():
        add(b, cyl((sx, yb, sz), (sx, Dl - w + 0.1, sz), 2.5))
        sub(b, cyl((sx, yb - 0.1, sz), (sx, Dl + 0.1, sz), 1.1),
            cyl((sx, Dl - 1.6, sz), (sx, Dl + 0.1, sz), 2.0))
    # TP4056 holder: two slotted clips for the board edges, USB-C hole in the bottom
    for s in (-1, 1):
        clip = box(s * 7.8, sy, w - 0.1, s * 10.0, 17.0, 12.0)
        sub(clip, box(s * 7.7, 13.85, w - 0.2, s * 8.6, 15.15, 12.1))
        add(b, clip)
    sub(b, box(-4.9, 14.6, -0.1, 4.9, 18.7, w + 0.1))
    # push button (left) and power switch (right)
    sub(b, cyl((-W2 - 0.1, 22, 17), (-W2 + w + 0.1, 22, 17), P["button_hole"] / 2))
    sub(b, cyl((W2 + 0.1, 32, 17), (W2 - w - 0.1, 32, 17), P["switch_hole"] / 2))
    # buzzer sound holes
    for i in range(-1, 2):
        for j in range(-1, 2):
            sub(b, cyl((-6 + 3 * i, Dl - w - 0.1, 17 + 3 * j), (-6 + 3 * i, Dl + 0.1, 17 + 3 * j), 0.8))
    return b


def door_part():
    Dt, Hf, bz0, t = P["D_top"], P["Hf"], P["bz0"], P["door_t"]
    ch = P["channel_half"]
    d = add(box(-18.0, Dt, bz0 + 3, 24.0, Dt + t, Hf),
            box(-15.0, Dt, bz0, 21.0, Dt + t, bz0 + 3.1),
            cyl((-15.0, Dt, bz0 + 3), (-15.0, Dt + t, bz0 + 3), 3.0),
            cyl((21.0, Dt, bz0 + 3), (21.0, Dt + t, bz0 + 3), 3.0))
    add(d, box(-ch + 0.3, Dt - P["door_tongue"], bz0 + 2.3, ch - 0.3, Dt, P["chamber_top"] + 0.2))
    kx, ky = HINGE
    sub(d, box(-23.0, Dt - 0.1, bz0 + 18.0, -16.5, Dt + t + 0.1, bz0 + 40.0))
    for z0, z1 in ((bz0, bz0 + 18.0), (bz0 + 40.0, Hf)):
        add(d, cyl((kx, ky, z0), (kx, ky, z1), 2.5))
    sub(d, cyl((kx, ky, bz0 - 1), (kx, ky, Hf + 1), 1.1))
    mz = P["magnet_z"]
    sub(d, cyl((19.75, Dt - 0.1, mz), (19.75, Dt + P["magnet_h"], mz), P["magnet_d"] / 2))
    return d


def placeholders():
    ay, r, Dl, w = P["axis_y"], P["chamber_d"] / 2, P["D_low"], P["wall"]
    top, bot, Hf = P["chamber_top"], P["chamber_top"] - P["chamber_l"], P["Hf"]
    fw, bz, W2 = P["front_wall"], P["beam_z"], P["W"] / 2
    oz = P["oled_z"] - 2
    parts = {
        "Drip chamber (17.5 x 49.5)": cyl((0, ay, bot), (0, ay, top), r),
        "Spike + cap": add(cyl((0, ay, top), (0, ay, Hf + 0.5), 4.0),
                           cyl((0, ay, Hf + 0.5), (0, ay, Hf + 6.5), 6.5),
                           cyl((0, ay, Hf + 6.5), (0, ay, Hf + 30), 3.5)),
        "IV tube": cyl((0, ay, -20), (0, ay, bot), 2.0),
        "Battery 40x30x8": box(-20, fw + 0.1, 4.2, 20, fw + 8.1, 34.2),
        "TP4056 module": add(box(-8.5, 14.0, 2.5, 8.5, 15.0, 30.5), box(-4.47, 15.0, 2.0, 4.47, 18.26, 9.35)),
        "OLED module": add(box(-13.65, fw + 1.5, oz - 13.9, 13.65, fw + 3.0, oz + 13.9),
                           box(-13.35, fw, P["oled_z"] - 9.35, 13.35, fw + 1.5, P["oled_z"] + 9.9)),
        "Buzzer 12 mm": cyl((-6, Dl - w - 9.5, 17), (-6, Dl - w, 17), 6.0),
        "Push button": cyl((-W2, 22, 17), (-W2 + 15, 22, 17), 6.0),
        "Power switch": box(W2 - 12, 28, 12, W2 - 2, 35.9, 22),
        "LED 5 mm": add(cyl((-(W2 - P["recess_d"]), ay, bz), (-(W2 - P["recess_d"]) + 1.0, ay, bz), 2.9),
                        cyl((-(W2 - P["recess_d"]) + 1.0, ay, bz), (-P["led_tip_x"], ay, bz), 2.5)),
    }
    x0 = P["channel_half"] + P["slit_depth"]
    ldr = None
    for i in range(4):
        y0 = ay - 9.1 + i * 4.55 + 0.1
        b = box(x0, y0, bz - 2.5, x0 + 2.2, y0 + 4.35, bz + 2.5)
        ldr = b if ldr is None else add(ldr, b)
    parts["4 LDRs"] = ldr
    zt = P["pcb_z0"] + P["pcb_h"]
    uz, yb = zt - 11.56, P["pcb_y"] + P["pcb_t"]
    sm = box(-9.0, yb + 8.5, uz - 11.26, 9.0, yb + 9.5, uz + 11.26)
    for hx in (-7.62, 7.62):
        add(sm, box(hx - 1.27, yb, uz - 10.16, hx + 1.27, yb + 8.5, uz + 10.16))
    parts["SuperMini on sockets"] = sm
    return parts


# ---------------------------------------------------------------- Fusion document
def appearance(design, keyword_sets, rgb, name, opacity=None):
    ap = design.appearances.itemByName(name)
    if ap is None:
        ap = _copy_from_library(design, keyword_sets, name)
    if ap is None:
        return None
    for i in range(ap.appearanceProperties.count):
        prop = ap.appearanceProperties.item(i)
        if isinstance(prop, adsk.core.ColorProperty) and prop.name.lower() in ("color", "colour", "base color"):
            try:
                prop.value = adsk.core.Color.create(*rgb, 255)
            except Exception:
                pass
    return ap


def _copy_from_library(design, keyword_sets, name):
    lib = app.materialLibraries.itemByName("Fusion Appearance Library")
    found = None
    if lib:
        for keywords in keyword_sets:
            for i in range(lib.appearances.count):
                a = lib.appearances.item(i)
                if all(k.lower() in a.name.lower() for k in keywords):
                    found = a
                    break
            if found:
                break
    if found is None:
        return None
    return design.appearances.addByCopy(found, name)


def new_component(root, name, body, ap=None, opacity=1.0):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = name
    base = comp.features.baseFeatures.add()
    base.startEdit()
    comp.bRepBodies.add(body, base)
    base.finishEdit()
    for i in range(comp.bRepBodies.count):
        bb = comp.bRepBodies.item(i)
        bb.name = name
        if ap:
            bb.appearance = ap
    occ.opacity = opacity
    return occ


def import_pcb(root, up_matrix):
    im = app.importManager
    opts = im.createSTEPImportOptions(PCB_STEP)
    before = root.occurrences.count
    im.importToTarget(opts, root)
    if root.occurrences.count <= before:
        print("PCB STEP import: nothing imported")
        return None
    occ = root.occurrences.item(root.occurrences.count - 1)
    occ.component.name = "PCB (from KiCad)"
    m = adsk.core.Matrix3D.create()
    m.setWithArray([-1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1])
    occ.transform2 = m

    def all_bodies(o):
        out = [o.bRepBodies.item(i) for i in range(o.bRepBodies.count)]
        for i in range(o.childOccurrences.count):
            out += all_bodies(o.childOccurrences.item(i))
        return out
    board = None
    for bb in all_bodies(occ):
        bx = bb.boundingBox
        dims = sorted([bx.maxPoint.x - bx.minPoint.x, bx.maxPoint.y - bx.minPoint.y, bx.maxPoint.z - bx.minPoint.z])
        if abs(dims[0] - cm(P["pcb_t"])) < 0.02 and dims[2] > cm(40):
            board = bb
    bx = board.boundingBox if board else occ.boundingBox
    cx = (bx.minPoint.x + bx.maxPoint.x) / 2
    cz = (bx.minPoint.z + bx.maxPoint.z) / 2
    m.translation = adsk.core.Vector3D.create(
        -cx, cm(P["pcb_y"]) - bx.minPoint.y, cm(P["pcb_z0"] + P["pcb_h"] / 2) - cz)
    m.transformBy(up_matrix)
    occ.transform2 = m
    print("PCB imported, board body found:", board is not None)
    return occ


def run(_context: str):
    try:
        doc = None
        for i in range(app.documents.count):
            if app.documents.item(i).name.startswith(DOC_NAME):
                doc = app.documents.item(i)
        if doc is None:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.activate()
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        top = design.rootComponent
        while top.occurrences.count:
            top.occurrences.item(0).deleteMe()
        up = app.preferences.generalPreferences.defaultModelingOrientation
        m = adsk.core.Matrix3D.create()
        if up == adsk.core.DefaultModelingOrientations.YUpModelingOrientation:
            m.setWithArray([1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1])
        asm = top.occurrences.addNewComponent(m)
        asm.component.name = "IVFlow v2 assembly"
        root = asm.component
        SCRATCH["root"] = top

        white = appearance(design, [["plastic", "white"]], (240, 240, 240), "IVFlow white")
        black = appearance(design, [["plastic", "black"]], (58, 58, 62), "IVFlow matte black")
        grey = appearance(design, [["plastic", "grey"]], (150, 150, 150), "IVFlow placeholder")
        smoke = appearance(design, [["glass", "smoke"], ["glass", "tint"], ["acrylic"], ["glass"]],
                           (35, 35, 45), "IVFlow smoked acrylic")

        outer = outer_shape()
        new_component(root, "Chassis (black)", chassis_part(outer), black)
        new_component(root, "Back shell (white)", back_shell_part(outer), white)
        new_component(root, "Door (black)", door_part(), black)
        new_component(root, "LED cover (black)", cover_part(-1), black)
        new_component(root, "LDR cover (black)", cover_part(1), black)
        new_component(root, "Face (smoked acrylic 2 mm)", glass_shape(0.15), smoke or black, 0.85)
        for name, body in placeholders().items():
            new_component(root, "[placeholder] " + name, body, grey, 0.6 if "chamber" in name.lower() else 1.0)
        try:
            import_pcb(top, m)
        except Exception:
            print("PCB import failed:\n" + traceback.format_exc())
        app.activeViewport.fit()
        print("smoked appearance:", smoke.name if smoke else None)
        print("built:", ", ".join(root.occurrences.item(i).component.name for i in range(root.occurrences.count)))
    except Exception:
        print("FAILED:\n" + traceback.format_exc())
