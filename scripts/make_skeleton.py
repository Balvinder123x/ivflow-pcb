"""Stage 0: create the empty IVFlow KiCad project skeleton.

Run with KiCad's bundled Python (needs pcbnew):
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts\\make_skeleton.py

Never overwrites an existing file (pass --force to regenerate deliberately).
"""
import json
import os
import sys
import uuid

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ_DIR = os.path.join(ROOT, "ivflow")
NAME = "ivflow"
LIB = "ivflow_lib"
KICAD_SHARE = r"C:\Program Files\KiCad\10.0\share\kicad"
FORCE = "--force" in sys.argv


def write_new(path, text):
    if os.path.exists(path) and not FORCE:
        print(f"skip (exists): {os.path.relpath(path, ROOT)}")
        return
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote: {os.path.relpath(path, ROOT)}")


def make_project():
    with open(os.path.join(KICAD_SHARE, "template", "kicad.kicad_pro"), encoding="utf-8") as f:
        pro = json.load(f)
    pro["meta"]["filename"] = f"{NAME}.kicad_pro"
    write_new(os.path.join(PROJ_DIR, f"{NAME}.kicad_pro"), json.dumps(pro, indent=2) + "\n")


def make_schematic():
    # Minimal valid schematic; KiCad upgrades the format version on first save.
    sch = f"""(kicad_sch
\t(version 20250114)
\t(generator "ivflow_scripts")
\t(uuid "{uuid.uuid4()}")
\t(paper "A4")
\t(title_block
\t\t(title "IVFlow")
\t\t(rev "v1")
\t)
\t(lib_symbols)
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
)
"""
    write_new(os.path.join(PROJ_DIR, f"{NAME}.kicad_sch"), sch)


def make_board():
    path = os.path.join(PROJ_DIR, f"{NAME}.kicad_pcb")
    if os.path.exists(path) and not FORCE:
        print(f"skip (exists): {os.path.relpath(path, ROOT)}")
        return
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.6))
    tb = board.GetTitleBlock()
    tb.SetTitle("IVFlow")
    tb.SetRevision("v1")
    pcbnew.SaveBoard(path, board)
    print(f"wrote: {os.path.relpath(path, ROOT)}")


def make_libs():
    lib_dir = os.path.join(PROJ_DIR, LIB)
    os.makedirs(os.path.join(lib_dir, f"{LIB}.pretty"), exist_ok=True)
    write_new(
        os.path.join(lib_dir, f"{LIB}.kicad_sym"),
        '(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "ivflow_scripts")\n)\n',
    )
    write_new(
        os.path.join(PROJ_DIR, "sym-lib-table"),
        "(sym_lib_table\n\t(version 7)\n"
        f'\t(lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}/{LIB}.kicad_sym")'
        '(options "")(descr "IVFlow custom symbols"))\n)\n',
    )
    write_new(
        os.path.join(PROJ_DIR, "fp-lib-table"),
        "(fp_lib_table\n\t(version 7)\n"
        f'\t(lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}/{LIB}.pretty")'
        '(options "")(descr "IVFlow custom footprints"))\n)\n',
    )


if __name__ == "__main__":
    os.makedirs(PROJ_DIR, exist_ok=True)
    make_project()
    make_schematic()
    make_board()
    make_libs()
