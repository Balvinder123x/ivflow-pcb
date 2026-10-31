# IVFlow PCB — Progress

## Environment (checked 2026-10-31)
| Item | Found |
|---|---|
| KiCad | 10.0.8, `C:\Program Files\KiCad\10.0` |
| kicad-cli | `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe` (not on PATH; scripts use full path) |
| KiCad Python | `C:\Program Files\KiCad\10.0\bin\python.exe` — Python 3.11.5, `pcbnew` 10.0.8 imports OK |
| kiutils | 1.4.8, installed with `pip --user` into KiCad's Python |
| git | 2.56.0, `C:\Program Files\Git\cmd\git.exe` (installed via winget) |
| Java (for Freerouting) | Temurin 21 JRE — winget install started, awaiting UAC approval |

### kiutils caveat
kiutils 1.4.8 predates the KiCad 10 file format. Rewriting a KiCad 10 file with it drops
data (`hide` flags, property text effects/fonts, `embedded_fonts`, `exclude_from_sim`, …).
Rule for this project:
- kiutils is used **only to generate new** custom symbols/footprints, which are then normalised
  with `kicad-cli sym upgrade` / `kicad-cli fp upgrade`.
- It is **never** used to rewrite a file that KiCad (or the user) has saved.
- The schematic and board are generated/edited with KiCad-native tooling (`pcbnew` API, or a
  small S-expression writer emitting the current format).

### Library availability (official KiCad 10 libs)
All needed symbols/footprints exist **except** `Transistor_FET:DMG2305UX` → use **AO3401A** for Q1.

## Stages
- [x] **0. Environment + skeleton** — approved, committed
  - `ivflow/ivflow.kicad_pro` (+ empty `.kicad_sch`, `.kicad_pcb`: 2 layers, 1.6 mm)
  - Project-local library `ivflow/ivflow_lib/` registered in `sym-lib-table` / `fp-lib-table`
  - `scripts/make_skeleton.py` (never overwrites existing files)
  - Checks: ERC 0 violations. DRC 1 expected violation (no board outline yet, added in Stage 4).
- [ ] **1. Custom library (SuperMini, TP4056 module, OLED header)** — blocked on measurements (open question 3)
- [ ] 2. Schematic + ERC
- [ ] 3. Footprints + BOM
- [ ] 4. Outline, holes, placement
- [ ] 5. Routing + pours + DRC
- [ ] 6. Fab outputs

## Open questions
1. ~~Install git~~ — done.
2. ~~Install Java 21~~ — approved; confirm install finished. Freerouting jar to be fetched in Stage 5.
3. Stage 1 measurements, see the list in the chat / below:
   - SuperMini: pin order of both rows (as viewed from the top, USB at top), row-to-row spacing, board outline size, antenna end.
   - TP4056 module: outline size, and the X/Y of each pad (IN+, IN−, BAT+, BAT−, OUT+, OUT−), plus whether pads are through-holes (and the hole size) or edge castellations.
   - OLED: pin order printed on your module.
4. SW1 slide switch: which part do you have? KiCad's stock CK OS102011MS2Q is only rated 100 mA, which doesn't meet the ≥1 A requirement.
5. ~~Save spec to CLAUDE.md~~ — done.
