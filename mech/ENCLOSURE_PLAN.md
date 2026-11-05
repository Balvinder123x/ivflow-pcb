# IVFlow v1 — enclosure plan

**One unit that hangs on the drip chamber** (decided 2026-11-05, after the user's sketches;
replaces the earlier clamp + box idea). Front: OLED. Back, top: a closed, light-tight chamber
holder. Inside: the PCB standing upright, battery and charger at the bottom (USB-C on the
bottom edge, like Dripo).

To be modelled in **Fusion 360** via the Fusion MCP connection. `mech/ivflow_pcb.step` is the
finished PCB (exported from KiCad) for fit checks.

Values marked **(verify)** are published/typical: check them on the real parts and change the
parameter.

## 1. Chamber holding mechanism

1. **V-channel** down the back of the body (90°). Any chamber diameter self-centres on the same
   axis, so the LED and LDRs always look straight across it.
2. **Hinged door** closes over the channel. Hinge on the left (seen from the back), M2 screw as
   the pin; **magnetic catch** (2 × 6 × 3 mm neodymium magnets, glued into pockets).
3. **Black foam lining** (EPDM/neoprene, 3–5 mm) on the V and the door: grips chambers from
   about 14 to 22 mm diameter and blocks light.
4. **Top fork** clips under the spike cap's ledge: every chamber is referenced from the drip
   tip, whatever its length. The sensor window is a fixed `beam_below_fork` under the fork.
5. **Bottom**: open slot for the tube only, so longer chambers also fit.
6. **Light-tight**: overlapping lip on the door seam, foam collars at the top and bottom
   openings, each LDR behind a 1 mm slit, the LED behind a 2 mm aperture.

## 2. Sensors in the holder (from the user's working prototype, 2026-11-05)

- **Beam height**: centre **13.5 mm below the top edge** of the holder (prototype: 13–14 mm).
- **One LED**, 5.1 mm diameter hole, on one side of the V (the prototype had 3 LEDs; now 1).
  The LED sits in a 6 mm deep black tube so its light goes straight across the chamber.
- **LDRs**: the 4 LDRs in a horizontal row in a pocket **18.20 × 5.20 mm** on the opposite
  side, centred on the beam.
- **Slit** in front of the LDR faces: **18.2 × 1.2 mm, 3 mm deep** (a short tunnel), centred on
  the beam. Why: a drop is 3–6 mm tall, so a 1.2 mm slit is fully blocked by each drop
  (big, clear dip), while the 3 mm depth stops light that comes in at an angle (room light).
  Narrower than 1.0 mm would starve the LDRs of light and slow them; wider than 2 mm would
  make the dip shallower. The slit is a parameter (`slit_h`) to tune on the real prototype.
- LDRs wired on a small strip behind the pocket; short wires to J2 (LDR) and J3 (LED) on the PCB.

## 3. Colours

- **Matte black**: the sensor block (V-channel, door, sensor windows). Absorbs stray light, no
  reflections inside the tunnel. Thin white plastic lets light through, so never white here.
- **White / light grey**: the outer body and front. Clean, medical look, stays cool.
- Printed as separate parts screwed together: no multi-colour printer needed.

## 4. Layout

| Zone | Front | Back |
|---|---|---|
| Top | OLED window | V-channel + door, LED and 4 LDRs |
| Middle | push button | PCB upright, connectors facing the channel |
| Bottom | — | battery (40 × 30 × 8), TP4056 with USB-C out of the bottom edge, power switch on the side, buzzer sound holes |

Estimated outer size **~55 W × 115 H × 42 D mm**, ~80–100 g with battery (close to Dripo).

## 5. Parameters (Fusion "User Parameters")

| Name | Value | Source |
|---|---|---|
| `wall` | 2.0 mm | print wall (≥ 2 mm wherever light must be blocked) |
| `fit` | 0.3 mm | printed-fit clearance |
| `pcb_w` × `pcb_h` × `pcb_t` | 46.0 × 41.5 × 1.6 mm, M2 holes 3.2 mm from corners | KiCad board |
| `above_pcb` | 22 mm (connectors 7 mm + plugs + wire bend; SuperMini on sockets ~12.7 mm) | KiCad 3D models |
| `below_pcb` | 3.0 mm (SMD ≤ 2.2 mm, leads trimmed) | KiCad 3D models |
| `chamber_d` | **17.5 mm** (radius 8.75) | measured by user |
| `chamber_l` | **49.5 mm** | measured by user |
| `chamber_range` | 14–22 mm diameter (foam) | design target |
| `tip_depth` | 15 mm, cap ledge to drip tip | **(verify)** |
| `beam_below_fork` | `tip_depth` + 10 mm | drops cross here |
| `foam_t` | 4 mm | **(verify sheet)** |
| `magnet` | 6 × 3 mm disc | **(verify)** |
| `bat` | 40 × 30 × 8 mm (+3 mm wire end) | 803040 **(verify)** |
| `chg` | 28 × 17 mm, USB-C on a short edge | TP4056 **(verify)** |
| `oled_board` | 27.3 × 27.8 mm, M2 holes 23.3 × 23.8 apart | 0.96" SSD1306 **(verify)** |
| `oled_view` | 22 × 11 mm | **(verify)** |
| `buzzer` | 12 Ø × 9.5 mm | **(verify)** |
| `button_hole` | 12 mm | **(verify)** |
| `switch_hole` | 6.2 mm (MTS-102 mini toggle) | **(verify)** |
| `beam_from_top` | 13.5 mm | user's prototype |
| `led_hole` | 5.1 mm, 6 mm deep tube | user measured |
| `ldr_pocket` | 18.20 × 5.20 mm | user measured |
| `slit_w` × `slit_h` × `slit_depth` | 18.2 × 1.2 × 3.0 mm | user's prototype + recommendation |

## 6. Build order in Fusion

1. User parameters.
2. Placeholders: imported PCB STEP, chamber cylinder (17.5 × 49.5 mm + spike cap), battery,
   TP4056, OLED, buzzer.
3. Sensor block (black): V-channel, fork, LED/LDR pockets and slits, hinge knuckles, magnet
   pockets, door with lip.
4. Body (white): front with OLED window, PCB standoffs, battery cradle, charger slot with
   USB-C cutout, button/switch holes, buzzer holes, bottom tube slot.
5. Back cover / screws joining body and sensor block.
6. Interference check, then STL per part, STEP assembly, renders.

## 7. Open items

- Measure the cap-ledge-to-drip-tip distance (`tip_depth`).
- Button and switch models (holes above assume a 12 mm push button and an MTS-102 toggle).
- Check the battery, TP4056, OLED, buzzer and foam sizes when they arrive.
- Fusion MCP connection to Claude Code (see the session notes).
