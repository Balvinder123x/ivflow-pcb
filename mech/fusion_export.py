"""Export the printable parts of "IVFlow enclosure v2" as STL (mm) and the whole assembly as
STEP into mech/export/. Run: python scripts/fusion_mcp.py script mech/fusion_export.py"""
import os
import traceback

import adsk.core
import adsk.fusion

OUT = r"C:\Users\bk823\Documents\IVFlow-PCB\mech\export"
PARTS = {  # component name prefix -> file name
    "Chassis": "ivflow_chassis_pearl_white.stl",
    "Back shell": "ivflow_back_shell_pearl_white.stl",
    "Door": "ivflow_door_pearl_white_PETG.stl",
    "Sensor insert": "ivflow_sensor_insert_black.stl",
}


def run(_context):
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        em = design.exportManager
        done = []
        for occ in design.rootComponent.allOccurrences:
            name = occ.component.name
            for prefix, fn in PARTS.items():
                if name.startswith(prefix):
                    body = occ.component.bRepBodies.item(0)   # component space = device coords (Z up)
                    opt = em.createSTLExportOptions(body, os.path.join(OUT, fn))
                    opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
                    opt.isBinaryFormat = True
                    em.execute(opt)
                    done.append(fn)
        step = em.createSTEPExportOptions(os.path.join(OUT, "ivflow_enclosure_v2_assembly.step"), design.rootComponent)
        em.execute(step)
        done.append("ivflow_enclosure_v2_assembly.step")
        print("exported:", ", ".join(done))
    except Exception:
        print("FAILED:\n" + traceback.format_exc())
