"""IVFlow v1 enclosure: Fusion 360 API script (run through the Fusion MCP server with
scripts/fusion_mcp.py, or from Fusion's Scripts and Add-Ins dialog).

One unit that hangs on the drip chamber (see mech/ENCLOSURE_PLAN.md):
  front  : OLED window; the sensor head sticks out behind the thinner lower body so the
           IV tube hangs free past it (Dripo-like silhouette)
  back   : black sensor block with a V-channel, top fork and bottom tube slot, closed by a
           hinged black door with magnet pockets; LED on one side wall, LDR row behind a slit
           on the other
  inside : PCB standing upright (components towards the back), battery + TP4056 at the
           bottom (USB-C out of the bottom face), button and power switch on the sides,
           buzzer behind the back cover

Coordinates (mm): X = width (+X is the right side seen from the front), Y = depth
(front face at Y = 0, back at +Y), Z = height (bottom at Z = 0). Every size is in P below:
edit a value and run the script again; it rebuilds the document "IVFlow enclosure v1".
"""
import math
import traceback

import adsk.core
import adsk.fusion

DOC_NAME = "IVFlow enclosure v1"
PCB_STEP = r"C:\Users\bk823\Documents\IVFlow-PCB\mech\ivflow_pcb.step"

P = dict(
    W=56.0, H=135.0, wall=2.0,
    D_low=38.0,                       # lower body depth (PCB + cable plugs + back cover)
    D_top=58.0,                       # sensor head depth: sticks out behind the lower body so
                                      # the IV tube hangs free past the lower body's back face
    # drip chamber (measured by the user) and holder
    chamber_d=17.5, chamber_l=49.5, holder_above_chamber=3.0,
    foam_t=4.0,                       # foam lining on the V and the door (not modelled)
    spike_slot=10.0,                  # top fork opening for the spike neck (verify)
    tube_slot=7.0,                    # bottom opening for the IV tube
    v_apex_y=24.0,                    # V-channel apex (90 deg); chamber axis = apex + 18
    channel_half=13.0,                # straight side walls of the channel at x = +-13
    block_half=15.5,                  # sensor block outer half-width
    block_y0=22.0, block_z0=77.0,     # sensor block front face / bottom
    beam_from_top=13.5,               # beam centre below the holder top (user prototype)
    led_hole=5.1, led_tube_len=8.5,
    ldr_pocket_w=18.2, ldr_pocket_h=5.2, slit_h=1.2, slit_depth=3.0,
    door_t=4.0, magnet_d=6.2, magnet_h=3.2, magnet_z=95.0,
    # electronics
    pcb_w=46.0, pcb_h=41.5, pcb_t=1.6, pcb_y=8.0, pcb_z0=34.0,
    oled_view=(22.0, 11.0), oled_z=110.0,
    button_hole=12.0, switch_hole=6.2,
)
P["axis_y"] = P["v_apex_y"] + 18.0
P["chamber_top"] = P["H"] - P["holder_above_chamber"]
P["beam_z"] = P["H"] - P["beam_from_top"]
HINGE = (-20.0, P["D_top"] + 2.6)     # hinge pin axis (x, y); knuckles clear the back face

app = adsk.core.Application.get()
tb = adsk.fusion.TemporaryBRepManager.get()
UNION = adsk.fusion.BooleanTypes.UnionBooleanType
DIFF = adsk.fusion.BooleanTypes.DifferenceBooleanType


def cm(v):
    return v / 10.0


def pt(x, y, z):
    return adsk.core.Point3D.create(cm(x), cm(y), cm(z))


def box(x0, y0, z0, x1, y1, z1, ux=(1, 0, 0), uy=(0, 1, 0)):
    c = pt((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    obb = adsk.core.OrientedBoundingBox3D.create(
        c, adsk.core.Vector3D.create(*ux), adsk.core.Vector3D.create(*uy),
        cm(abs(x1 - x0)), cm(abs(y1 - y0)), cm(abs(z1 - z0)))
    return tb.createBox(obb)


def rbox(cx, cy, z0, z1, length, width, angle_deg):
    """Box rotated about Z: `length` along the angle direction, `width` across it."""
    a = math.radians(angle_deg)
    obb = adsk.core.OrientedBoundingBox3D.create(
        pt(cx, cy, (z0 + z1) / 2), adsk.core.Vector3D.create(math.cos(a), math.sin(a), 0),
        adsk.core.Vector3D.create(-math.sin(a), math.cos(a), 0), cm(length), cm(width), cm(z1 - z0))
    return tb.createBox(obb)


def cyl(p0, p1, r):
    return tb.createCylinderOrCone(pt(*p0), cm(r), pt(*p1), cm(r))


def add(a, *bs):
    for b in bs:
        tb.booleanOperation(a, b, UNION)
    return a


def sub(a, *bs):
    for b in bs:
        tb.booleanOperation(a, b, DIFF)
    return a


def slot_xy(x_half, y0, y1, z0, z1, round_end_y):
    """Slot open towards +Y with a round end at round_end_y."""
    return add(box(-x_half, round_end_y, z0, x_half, y1, z1),
               cyl((0, round_end_y, z0), (0, round_end_y, z1), x_half))


# ---------------------------------------------------------------- parts
def body_part():
    W2, H, w = P["W"] / 2, P["H"], P["wall"]
    Dl, Dt = P["D_low"], P["D_top"]
    bh, by0, bz0 = P["block_half"], P["block_y0"], P["block_z0"]
    b = add(box(-W2, 0, 0, W2, Dl, bz0), box(-W2, 0, bz0, W2, Dt, H))
    sub(b,
        box(-W2 + w, w, w, W2 - w, Dl - w, bz0),                     # lower compartment
        box(-W2 + w, w, bz0 - 0.1, W2 - w, by0, H - w),              # front zone (OLED)
        box(-W2 + w, by0, bz0 + w, -bh, Dt - w, H - w),              # left wiring bay (LED)
        box(bh, by0, bz0 + w, W2 - w, Dt - w, H - w),                # right wiring bay (LDRs)
        box(-W2 + w, by0, bz0 - 0.1, -bh, Dl - w, bz0 + w + 0.1),    # bay openings down
        box(bh, by0, bz0 - 0.1, W2 - w, Dl - w, bz0 + w + 0.1),      #   to the PCB
        box(-bh, by0, bz0, bh, Dt + 0.1, H + 0.1),                   # sensor block seat
        box(-W2 + 4, Dl - w - 0.1, 4, W2 - 4, Dl + 0.1, bz0 - 2))    # back opening (cover)
    # magnet boss in the right bay, pocket opening at the back face
    mz = P["magnet_z"]
    add(b, box(bh + 1.0, Dt - 6.0, mz - 5, W2 - w, Dt, mz + 5))
    sub(b, cyl((19.75, Dt + 0.1, mz), (19.75, Dt - P["magnet_h"], mz), P["magnet_d"] / 2))
    # hinge knuckle (middle segment) on the left back corner
    kx, ky = HINGE
    add(b, box(kx - 2.5, Dt - 0.5, 95.5, kx + 2.5, ky, 116.5), cyl((kx, ky, 95.5), (kx, ky, 116.5), 2.5))
    sub(b, cyl((kx, ky, 93), (kx, ky, 119), 1.1))
    # cover screw bosses (M2) in the lower compartment
    for bx in (-W2 + 6.0, W2 - 6.0):
        for bz in (7.0, bz0 - 5.0):
            add(b, cyl((bx, Dl - 10, bz), (bx, Dl - w, bz), 3.0))
            sub(b, cyl((bx, Dl - 10.1, bz), (bx, Dl - w + 0.1, bz), 0.8))
    # PCB standoffs (M2) from the front wall
    hx, hz = P["pcb_w"] / 2 - 3.2, P["pcb_h"] / 2 - 3.2
    zc = P["pcb_z0"] + P["pcb_h"] / 2
    for sx in (-hx, hx):
        for sz in (zc - hz, zc + hz):
            add(b, cyl((sx, w - 0.1, sz), (sx, P["pcb_y"], sz), 2.5))
            sub(b, cyl((sx, w + 1.0, sz), (sx, P["pcb_y"] + 0.1, sz), 0.8))
    # OLED window
    vw, vh = P["oled_view"]
    sub(b, box(-vw / 2 - 0.5, -0.1, P["oled_z"] - vh / 2 - 0.5, vw / 2 + 0.5, w + 0.1, P["oled_z"] + vh / 2 + 0.5))
    # side holes: push button (left), power switch (right)
    sub(b, cyl((-W2 - 0.1, 22, 17), (-W2 + w + 0.1, 22, 17), P["button_hole"] / 2))
    sub(b, cyl((W2 + 0.1, 32, 17), (W2 - w - 0.1, 32, 17), P["switch_hole"] / 2))
    # USB-C cutout in the bottom face (TP4056 standing at x 19..23)
    sub(b, box(19.6, 13.6, -0.1, 23.7, 23.4, w + 0.1))
    return b


def sensor_block_part():
    bh, by0, bz0, H, Dt = P["block_half"], P["block_y0"], P["block_z0"], P["H"], P["D_top"]
    ch, ay, apex = P["channel_half"], P["axis_y"], P["v_apex_y"]
    top_t, floor_t = H - P["chamber_top"] - 0.5, 2.0
    b = box(-bh, by0, bz0, bh, Dt, H)
    z0, z1 = bz0 + floor_t, H - top_t
    # V-channel: square turned 45 deg with its corner at the apex, plus the straight part
    side = ch * math.sqrt(2)
    sub(b, rbox(0, apex + ch, z0, z1, side, side, 45), box(-ch, apex + ch, z0, ch, Dt + 0.1, z1))
    # top fork (spike neck) and bottom tube slot, both open to the back
    sub(b, slot_xy(P["spike_slot"] / 2, ay, Dt + 0.1, z1 - 0.1, H + 0.1, ay))
    sub(b, slot_xy(P["tube_slot"] / 2, ay, Dt + 0.1, bz0 - 0.1, z0 + 0.1, ay))
    # LED: tube boss into the left bay, 5.1 mm hole through to the channel
    bz = P["beam_z"]
    add(b, cyl((-bh - (P["led_tube_len"] - (bh - ch)), ay, bz), (-bh, ay, bz), 4.5))
    sub(b, cyl((-bh - P["led_tube_len"], ay, bz), (-ch + 0.1, ay, bz), P["led_hole"] / 2))
    # LDR row: boss into the right bay, slit 1.2 mm high and 3 mm deep, pocket 18.2 x 5.2
    pw, ph, sh, sd = P["ldr_pocket_w"], P["ldr_pocket_h"], P["slit_h"], P["slit_depth"]
    y0 = apex + ch + 0.2                       # straight wall starts here
    y1 = y0 + pw
    add(b, box(bh, y0 - 1.0, bz - ph / 2 - 2.0, bh + 5.5, min(y1 + 1.0, Dt - P["wall"]), bz + ph / 2 + 2.0))
    sub(b, box(ch - 0.1, y0, bz - sh / 2, ch + sd, y1, bz + sh / 2))
    sub(b, box(ch + sd, y0, bz - ph / 2, bh + 5.6, y1, bz + ph / 2))
    return b


def door_part():
    Dt, H, bz0, t = P["D_top"], P["H"], P["block_z0"], P["door_t"]
    ch = P["channel_half"]
    d = box(-18.0, Dt, bz0, 24.0, Dt + t, H)
    # tongue into the channel: light seal + backing for the foam pad
    add(d, box(-ch + 0.3, Dt - 2.0, bz0 + 2.3, ch - 0.3, Dt, H - 2.8))
    # hinge: door knuckles top and bottom, clearance around the body knuckle
    kx, ky = HINGE
    sub(d, box(-23.0, Dt - 0.1, 95.0, -16.5, Dt + t + 0.1, 117.0))
    for z0, z1 in ((bz0, 95.0), (117.0, H)):
        add(d, cyl((kx, ky, z0), (kx, ky, z1), 2.5))
    sub(d, cyl((kx, ky, bz0 - 1), (kx, ky, H + 1), 1.1))
    # magnet pocket facing the body's magnet
    mz = P["magnet_z"]
    sub(d, cyl((19.75, Dt - 0.1, mz), (19.75, Dt + P["magnet_h"], mz), P["magnet_d"] / 2))
    return d


def cover_part():
    W2, Dl, w, bz0 = P["W"] / 2, P["D_low"], P["wall"], P["block_z0"]
    c = box(-W2 + 4.1, Dl - w, 4.1, W2 - 4.1, Dl, bz0 - 2.1)
    for bx in (-W2 + 6.0, W2 - 6.0):
        for bz in (7.0, bz0 - 5.0):
            sub(c, cyl((bx, Dl - w - 0.1, bz), (bx, Dl + 0.1, bz), 1.1))
    # buzzer sound holes (buzzer glued behind them)
    for i in range(-1, 2):
        for j in range(-1, 2):
            sub(c, cyl((-6 + 3 * i, Dl - w - 0.1, 17 + 3 * j), (-6 + 3 * i, Dl + 0.1, 17 + 3 * j), 0.8))
    return c


def placeholders():
    """Stand-in parts (not printed): chamber with spike and tube, battery, TP4056, OLED,
    SuperMini on its sockets, buzzer, button, switch."""
    ay, r, Dl, w = P["axis_y"], P["chamber_d"] / 2, P["D_low"], P["wall"]
    top, bot = P["chamber_top"], P["chamber_top"] - P["chamber_l"]
    parts = {
        "Drip chamber (17.5 x 49.5)": cyl((0, ay, bot), (0, ay, top), r),
        "Spike + cap": add(cyl((0, ay, top), (0, ay, P["H"] + 0.5), 4.0),          # neck through the fork
                           cyl((0, ay, P["H"] + 0.5), (0, ay, P["H"] + 6.5), 6.5),
                           cyl((0, ay, P["H"] + 6.5), (0, ay, P["H"] + 30), 3.5)),
        "IV tube": cyl((0, ay, -20), (0, ay, bot), 2.0),
        "Battery 40x30x8": box(-24, 3.5, 2.2, 16, 11.5, 32.2),
        "TP4056 module": add(box(19, 10, 2.5, 20, 27, 30.5), box(20, 14.03, 2.0, 23.26, 22.97, 9.35)),
        "OLED module": add(box(-13.65, 3.5, P["oled_z"] - 2 - 13.9, 13.65, 5.0, P["oled_z"] - 2 + 13.9),
                           box(-13.35, 2.0, P["oled_z"] - 9.65 + 0.3, 13.35, 3.5, P["oled_z"] + 9.65 + 0.3)),
        "Buzzer 12 mm": cyl((-6, Dl - w - 9.5, 17), (-6, Dl - w, 17), 6.0),
        "Push button": cyl((-P["W"] / 2, 22, 17), (-P["W"] / 2 + 15, 22, 17), 6.0),
        "Power switch": box(P["W"] / 2 - 12, 28, 12, P["W"] / 2 - 2, 35.9, 22),
    }
    # SuperMini on its two female headers (U1 centre = PCB centre, 11.56 mm below the top edge)
    zt = P["pcb_z0"] + P["pcb_h"]
    uz, yb = zt - 11.56, P["pcb_y"] + P["pcb_t"]
    sm = box(-9.0, yb + 8.5, uz - 11.26, 9.0, yb + 9.5, uz + 11.26)
    for hx in (-7.62, 7.62):
        add(sm, box(hx - 1.27, yb, uz - 10.16, hx + 1.27, yb + 8.5, uz + 10.16))
    parts["SuperMini on sockets"] = sm
    return parts


# ---------------------------------------------------------------- Fusion document
def appearance(design, keywords, fallback_rgb, name):
    lib = app.materialLibraries.itemByName("Fusion Appearance Library")
    found = None
    if lib:
        for i in range(lib.appearances.count):
            a = lib.appearances.item(i)
            if all(k.lower() in a.name.lower() for k in keywords):
                found = a
                break
    if found is None:
        return None
    existing = design.appearances.itemByName(name)
    if existing:
        return existing
    ap = design.appearances.addByCopy(found, name)
    for i in range(ap.appearanceProperties.count):
        prop = ap.appearanceProperties.item(i)
        if isinstance(prop, adsk.core.ColorProperty) and prop.name.lower() in ("color", "colour", "base color"):
            prop.value = adsk.core.Color.create(*fallback_rgb, 255)
    return ap


def new_component(root, name, body, ap=None, opacity=1.0):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = name
    base = comp.features.baseFeatures.add()
    base.startEdit()
    b = comp.bRepBodies.add(body, base)
    base.finishEdit()
    for i in range(comp.bRepBodies.count):
        bb = comp.bRepBodies.item(i)
        bb.name = name
        if ap:
            bb.appearance = ap
    occ.opacity = opacity
    return occ


def import_pcb(design, root, up_matrix):
    """Import the KiCad PCB STEP, stand it up (components towards the back, antenna at the top)
    and put the board where the standoffs are."""
    im = app.importManager
    opts = im.createSTEPImportOptions(PCB_STEP)
    before = root.occurrences.count
    im.importToTarget(opts, root)
    occ = root.occurrences.item(root.occurrences.count - 1) if root.occurrences.count > before else None
    if occ is None:
        print("PCB STEP import: nothing imported")
        return None
    occ.component.name = "PCB (from KiCad)"
    # STEP (x, y, z) -> device (-x, z, y): proper rotation, board plane becomes XZ
    m = adsk.core.Matrix3D.create()
    m.setWithArray([-1, 0, 0, 0,
                    0, 0, 1, 0,
                    0, 1, 0, 0,
                    0, 0, 0, 1])
    occ.transform2 = m
    # find the board body (thinnest large body) to align it
    board = None
    for i in range(occ.bRepBodies.count):
        bb = occ.bRepBodies.item(i)
        bx = bb.boundingBox
        dims = sorted([bx.maxPoint.x - bx.minPoint.x, bx.maxPoint.y - bx.minPoint.y, bx.maxPoint.z - bx.minPoint.z])
        if abs(dims[0] - cm(P["pcb_t"])) < 0.02 and dims[2] > cm(40):
            board = bb
    def all_bodies(o):
        out = [o.bRepBodies.item(i) for i in range(o.bRepBodies.count)]
        for i in range(o.childOccurrences.count):
            out += all_bodies(o.childOccurrences.item(i))
        return out
    if board is None:
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
    m.transformBy(up_matrix)          # same up-axis turn as the rest of the assembly
    occ.transform2 = m
    print("PCB imported, board body found:", board is not None)
    return occ


def run(_context: str):
    try:
        # reuse or create the document
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
        # Everything is built Z-up; if Fusion models Y-up, stand the assembly up:
        # device (x, y, z) -> Fusion (x, z, -y), so the front faces +Z (Fusion "front" view)
        up = app.preferences.generalPreferences.defaultModelingOrientation
        m = adsk.core.Matrix3D.create()
        if up == adsk.core.DefaultModelingOrientations.YUpModelingOrientation:
            m.setWithArray([1, 0, 0, 0,
                            0, 0, 1, 0,
                            0, -1, 0, 0,
                            0, 0, 0, 1])
        asm = top.occurrences.addNewComponent(m)
        asm.component.name = "IVFlow v1 assembly"
        root = asm.component

        white = appearance(design, ["plastic", "white"], (240, 240, 240), "IVFlow white")
        black = appearance(design, ["plastic", "black"], (25, 25, 25), "IVFlow matte black")
        grey = appearance(design, ["plastic", "grey"], (150, 150, 150), "IVFlow placeholder")

        new_component(root, "Body (white)", body_part(), white)
        new_component(root, "Sensor block (black)", sensor_block_part(), black)
        new_component(root, "Door (black)", door_part(), black)
        new_component(root, "Back cover (white)", cover_part(), white)
        for name, body in placeholders().items():
            new_component(root, "[placeholder] " + name, body, grey, 0.6 if "chamber" in name.lower() else 1.0)
        try:
            import_pcb(design, top, m)     # top level: Fusion only moves root-level occurrences
        except Exception:
            print("PCB import failed:\n" + traceback.format_exc())
        app.activeViewport.fit()
        try:
            doc.saveAs(DOC_NAME, app.data.activeProject.rootFolder, "IVFlow enclosure, generated by mech/fusion_enclosure.py", "")
        except Exception:
            print("(document not saved automatically: save it from Fusion)")
        print("built:", ", ".join(root.occurrences.item(i).component.name for i in range(root.occurrences.count)))
    except Exception:
        print("FAILED:\n" + traceback.format_exc())
