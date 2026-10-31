# IVFlow PCB — Progress

## Environment (checked 2026-10-31)
| Item | Found |
|---|---|
| KiCad | 10.0.8, `C:\Program Files\KiCad\10.0` |
| kicad-cli | `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe` (not on PATH; scripts use full path) |
| KiCad Python | `C:\Program Files\KiCad\10.0\bin\python.exe` — Python 3.11.5, `pcbnew` 10.0.8 |
| kiutils | 1.4.8, `pip --user` into KiCad's Python |
| git | 2.56.0, `C:\Program Files\Git\cmd\git.exe`; repo identity Balvinder123x <balvinder23166@iiitd.ac.in> |
| Java | Temurin 21.0.13 JRE, `C:\Program Files\Eclipse Adoptium\jre-21.0.13.9-hotspot\bin\java.exe` |
| Freerouting | not downloaded yet (Stage 5) |

### Tooling rules
kiutils 1.4.8 predates the KiCad 10 format and drops data when rewriting KiCad 10 files.
- Symbols: generated with kiutils, then normalised with `kicad-cli sym upgrade --force`.
- Footprints: generated with the `pcbnew` API (writes native KiCad 10 format directly).
- Never rewrite a file KiCad/the user has saved with kiutils.
- Previews: `kicad-cli sym/fp export svg`, rasterised with headless Edge for checking.

### Library availability (official KiCad 10 libs)
All needed parts exist **except** `Transistor_FET:DMG2305UX` → Q1 = **AO3401A**.

## Design changes vs. original spec
- 2026-10-31: off-board parts plug in through connectors.
  - J_OLED: 1×4 male header, fixed order GND, VCC, SCL, SDA (jumper wires to module) → no custom part.
  - LED: D2 replaced by **J_LED** (JST-XH 2-pin, pin 1 = anode/+, pin 2 = cathode/−). R20 stays on board.
  - J_LDR unchanged (JST-XH 5-pin).

## Stages
- [x] **0. Environment + skeleton** — approved, committed
- [ ] **1. Custom library** — partially done, 🛑 waiting for verification
  - `scripts/make_library.py` generates `ivflow/ivflow_lib/`
  - Symbol `ESP32-C3_SuperMini` ✔ (pin numbers depend on the pinout check below)
  - Footprint `ESP32-C3_SuperMini` — **UNVERIFIED DRAFT** from published values:
    module 22.52 × 18.0 mm, rows 15.24 mm apart, pins centred along the length,
    antenna keepout 6 mm at the end opposite USB (between the rows, both layers)
  - Symbol `TP4056_Module_USB-C` ✔ (pads 1 IN+, 2 IN−, 3 BAT+, 4 BAT−, 5 OUT+, 6 OUT−)
  - Footprint `TP4056_Module_USB-C` — **not made**, needs measurements
- [ ] 2. Schematic + ERC
- [ ] 3. Footprints + BOM
- [ ] 4. Outline, holes, placement
- [ ] 5. Routing + pours + DRC
- [ ] 6. Fab outputs

## Open questions
1. **SuperMini — verify the draft** (top view, USB-C at top):
   - Left row, top→bottom: 5V, GND, 3V3, GPIO4, GPIO3, GPIO2, GPIO1, GPIO0?
   - Right row, top→bottom: GPIO5, GPIO6, GPIO7, GPIO8, GPIO9, GPIO10, GPIO20, GPIO21?
   - Row spacing 15.24 mm (= 6 holes of 2.54 mm)? Module 22.52 × 18 mm?
   - Distance from USB-end edge to first pin centre (draft assumes ≈2.4 mm, i.e. centred).
   - Is the antenna at the end opposite USB?
2. **TP4056 module** (top view, USB-C at top): length × width; X/Y of each pad
   (IN+, IN−, BAT+, BAT−, OUT+, OUT−) from the bottom-left corner; pad type (holes + drill
   size, or edge castellations); how far USB-C sticks out past the module edge.
3. **SW1 power switch**: which part? KiCad's stock CK OS102011MS2Q is only 100 mA.
   Option: a 2-pin connector to a panel-mount switch, in line with the connector approach.
4. Buzzer (BZ1) and button (SW2): keep on the board, or also move them to connectors?
5. Push this repo to GitHub? (needs a repo created on github.com; nothing pushed yet)
