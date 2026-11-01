# Project: IVFlow main PCB in KiCad

You are helping me design a PCB for IVFlow, a battery-powered IV drip monitor.
I will watch progress in KiCad myself, so work in stages and STOP at every
checkpoint marked 🛑 so I can open the files in KiCad and approve before you continue.

Current status, tool paths and open questions live in `PROGRESS.md` — read it first.

## My setup
- KiCad version: 10.0 (10.0.8)
- OS: Windows
- Max main board size: as compact as possible, but everything must fit properly
- Fab house: JLCPCB, 2-layer, 1.6 mm, HASL. Hand-assembled by me, so prefer
  0805 passives, SOT-23 / SOT-23-5 parts, and through-hole connectors.

## Working rules
1. First check the environment: find kicad-cli, KiCad's bundled Python (pcbnew
   module), and confirm the KiCad version. Tell me what you found.
2. Create the project as `ivflow/ivflow.kicad_pro`, init git, and commit after
   every stage with a clear message.
3. Generate files reproducibly: write Python scripts in `scripts/` (prefer the
   `kiutils` library for .kicad_sch/.kicad_sym/.kicad_mod, and KiCad's `pcbnew`
   Python API for the board). Don't hand-edit giant S-expression files blindly.
   Once I approve a stage and start editing that file in KiCad myself, do NOT
   regenerate it from scratch — make targeted edits only.
   (Note: kiutils 1.4.8 loses data on KiCad 10 files — only use it to generate new
   parts, never to rewrite saved files. See PROGRESS.md.)
4. Use KiCad's official symbol/footprint libraries wherever possible. Put any
   custom symbols/footprints in a project-local library `ivflow_lib`.
5. Never guess physical dimensions or pin orders of modules. Where I must verify
   something, ask me and wait.
6. Never say a stage is done without running the checks: `kicad-cli sch erc`
   for schematics, `kicad-cli pcb drc` for the board. Show me the summary and
   fix every error; explain any warning you leave.
7. Keep `PROGRESS.md` updated: what's done, what's pending, open questions.
8. KiCad does not auto-reload changed files. At each checkpoint, remind me to
   close and reopen the file (or use File → Revert) before reviewing.
   I will close KiCad while you are writing files.

## Design specification

### Modules (need custom symbol + footprint)
- U1: ESP32-C3 SuperMini dev board, mounted on two 1×8 female 2.54 mm headers.
  ⚠ Ask me to confirm the pin order and the row spacing by measuring my board
  before making the footprint. Leave the SuperMini's 5V pin UNCONNECTED.
  The antenna end must overhang the board edge or sit over a copper keepout.
- U2: TP4056 charger module with protection (DW01 + 8205), USB-C version,
  pads IN+, IN−, BAT+, BAT−, OUT+, OUT−.
  ⚠ Ask me for the pad positions measured from my module. Mount it at a board
  edge so the USB-C port faces outward. Removable daughterboard (decided 2026-11-01):
  male pins in the module, female headers on the main board.
- Both module footprints are PROVISIONAL until I buy and measure the real modules
  (SuperMini first-pin offset; all TP4056 pad positions, pad type and USB overhang).
  Never invent pad positions. Do not finalize PCB placement or generate fab outputs
  before the footprints are verified.
- J_OLED: 1×4 2.54 mm male header; the OLED module is wired to it with jumper
  wires, so the board order is fixed (GND, VCC, SCL, SDA) and labelled on silk.
  No custom part needed (Connector_Generic:Conn_01x04).

Design principle (decided 2026-10-31): off-board parts (OLED, LDR strip, LED) plug
in through connectors so the assembled PCB only needs the parts attached.
Extended 2026-11-01: the power switch, buzzer and button are also off-board on
JST-XH 2-pin connectors (J6 POWER SW, J7 BUZZER, J8 BUTTON). D3 and C6 stay on the board.

### Nets and circuit

POWER
- U2 IN+ = VBUS. U2 IN− and U2 OUT− = GND (system ground).
  U2 BAT+/BAT− → J_BAT (JST-PH 2-pin, Li-Po 3.7 V). BAT− must NOT touch GND.
- U2 OUT+ = VBAT_P.
- Power path: D1 SS14 Schottky, anode VBUS → cathode VSYS.
  Q1 P-MOSFET (AO3401A or DMG2305UX, SOT-23): drain = VBAT_P,
  source = VSYS, gate = VBUS. R1 100k from Q1 gate to GND.
- J6 POWER SW (JST-XH 2-pin) to a panel-mount switch rated ≥1 A: pin 1 VSYS, pin 2 VSYS_SW.
- U3 AP2112K-3.3 (SOT-23-5): VIN = VSYS_SW, EN = VSYS_SW, OUT = +3V3.
  C1 10 µF on VIN, C2 10 µF + C3 100 nF on OUT, C4 22 µF bulk near U1's 3V3 pin.
- +3V3 → U1 3V3 pin. GND → U1 GND.

BATTERY SENSE (switched divider, keeps GPIO2 high at boot)
- R2 100k: VSYS_SW → BAT_SENSE. R3 100k: BAT_SENSE → Q2 drain.
- Q2 2N7002: source GND, gate = GPIO7 via R4 100 Ω, R5 100k gate → GND.
- C5 100 nF: BAT_SENSE → GND. BAT_SENSE → U1 GPIO2.

LDR SENSORS (off-board strip, 5-wire cable)
- J_LDR: JST-XH 5-pin. Pin 1 = +3V3, pins 2–5 = LDR1..LDR4.
- For each channel n = 1..4: R(10+n) 10k (placeholder value) LDRn → GND,
  C(10+n) 10 nF LDRn → GND.
- LDR1 → GPIO0, LDR2 → GPIO1, LDR3 → GPIO3, LDR4 → GPIO4.
- Place R/C for each channel close to U1's pins; keep these traces away from
  the buzzer and power path.

LED (illuminates the drip chamber) — off-board, on a cable
- J_LED: JST-XH 2-pin. GPIO5 → R20 82 Ω → J_LED pin 1 (LED anode, "+"),
  J_LED pin 2 (LED cathode, "−") → GND. R20 stays on the board.
- The 5 mm LED itself is mounted at the drip chamber; silk marks + / −.

BUZZER
- J7 BUZZER (JST-XH 2-pin) to an off-board 3–5 V active buzzer: pin 1 (+) VSYS_SW,
  pin 2 (−) Q3 drain.
- Q3 AO3400A: source GND, gate = GPIO6 via R21 100 Ω, R22 100k gate → GND.
- D3 1N4148W on the board across J7 (cathode to VSYS_SW).

OLED + BUTTON + EXPANSION
- J_OLED pins 1-4: GND, +3V3, SCL = GPIO9, SDA = GPIO8.
- R23, R24 4.7k pull-ups SDA/SCL → +3V3, marked DNP (most modules have them).
- J8 BUTTON (JST-XH 2-pin) to an off-board push button: pin 1 GPIO10, pin 2 GND.
  C6 100 nF across it, on the board.
- J_EXP 1×5 header: GND, VSYS_SW, +3V3, GPIO20, GPIO21 (future servo / spare).

### Layout rules
- 2 layers, GND pour on both, stitched with vias every ~5 mm.
- Tracks: 0.25 mm signals, 0.5 mm power (VBUS, VBAT_P, VSYS, VSYS_SW, +3V3).
  Vias 0.3 mm drill / 0.6 mm pad. Use JLCPCB 2-layer minimums as DRC rules.
- Silkscreen: label every connector pin and its function (POWER SW, BUZZER +/−,
  BUTTON, LED +/−), battery polarity, and "IVFlow v1".
- 4× M2 mounting holes in the corners unless I say otherwise.

## Stages
0. Environment check + project skeleton. 🛑
1. Custom library: SuperMini and TP4056 module symbols and footprints
   (after I give measurements). 🛑
2. Schematic on one A4 sheet, grouped into labeled blocks: Power, Battery
   sense, Sensors, LED, Buzzer, OLED/Button/Expansion. Run ERC. 🛑
3. Footprint assignment + BOM (CSV with LCSC part numbers where possible). 🛑
4. PCB: board outline, mounting holes, component placement only (no tracks).
   Send me a short placement rationale. 🛑
5. Routing: export to Specctra DSN and autoroute with Freerouting if available,
   otherwise route critical nets (power, analog) and tell me what's left for me.
   Add GND pours, run DRC to zero errors. 🛑
6. Fab outputs in `fab/`: Gerbers, drill files, BOM, pick-and-place, plus
   3D render screenshots (top and bottom) via kicad-cli. 🛑