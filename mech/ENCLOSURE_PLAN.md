# IVFlow v1 — enclosure plan

Two parts (decided 2026-11-05): a **sensor clamp** that closes around the drip chamber, and a
**main box** that holds the PCB, battery, charger, OLED and controls and straps to the IV pole.
A 7-wire cable joins them (J2 LDR strip: 5 wires, J3 LED: 2 wires).

To be modelled in **Fusion 360** (CadQuery is blocked on this PC by Windows Application Control).
`mech/ivflow_pcb.step` is the finished PCB with all parts (exported from KiCad) to place inside
the model for fit checks.

Dimensions marked **(verify)** are published/typical values: check them on the real parts when
they arrive and change the parameter.

## 1. Parameters (Fusion "User Parameters")

| Name | Value | Source |
|---|---|---|
| `wall` | 2.0 mm | print wall thickness |
| `fit` | 0.3 mm | clearance for printed fits |
| `pcb_w` × `pcb_h` × `pcb_t` | 46.0 × 41.5 × 1.6 mm | KiCad board |
| `pcb_hole_inset` | 3.2 mm (M2 holes, 2.2 mm) | KiCad board |
| `above_pcb` | 22 mm free space above the PCB top | see 3 |
| `below_pcb` | 3.0 mm to battery (SMD 2.2 mm max, leads trimmed to ~1.5 mm) | KiCad 3D models |
| `bat_l` × `bat_w` × `bat_t` | 40 × 30 × 8 mm, +3 mm at the wire end | 803040 Li-Po **(verify)** |
| `chg_l` × `chg_w` | 28 × 17 mm, USB-C on one short edge | TP4056 module **(verify)** |
| `oled_board` | 27.3 × 27.8 mm, 4 × M2 holes 23.3 × 23.8 mm apart | 0.96" SSD1306 **(verify)** |
| `oled_view` | 22 × 11 mm visible area | **(verify)** |
| `buzzer_d` × `buzzer_h` | 12 × 9.5 mm | active buzzer **(verify)** |
| `button_hole` | 12 mm | panel push button **(verify)** |
| `switch_hole` | 6.2 mm | mini toggle MTS-102 **(verify)** |
| `chamber_d` | 20 mm outer diameter | **PLACEHOLDER: measure** |
| `chamber_l` | 70 mm | **PLACEHOLDER: measure** |
| `tip_depth` | 15 mm, chamber top to drip tip | **PLACEHOLDER: measure** |
| `ldr_d` | 5 mm (GL5528, 2 mm thick body) | datasheet |
| `led_d` | 5 mm LED | standard |
| `pole_strap` | 25 mm wide hook-and-loop strap | fits any IV pole |

## 2. Sensor clamp (on the drip chamber)

- **Clamshell**: two halves on a hinge (M2 screw as the hinge pin) and a snap latch on the
  other side. Open it, put the chamber in, close it.
- **Bore** `chamber_d + fit`, with two thin flexible ribs inside so small size differences
  between chamber brands still grip.
- **Height ~30 mm**. The beam sits **8–12 mm below the drip tip**, where every drop crosses it.
  A raised lip at the top locates the clamp against the chamber's top cap.
- **LED half**: one 5 mm green LED, pointing across the chamber through a 2 mm aperture.
- **Sensor half**: 4 LDRs in a 2 × 2 grid (10 × 10 mm), each behind a **1 mm horizontal slit**
  (DripOMeter's method against room light). Two heights let the firmware confirm a falling
  drop (upper pair first, then lower pair) and reject light flicker.
- **Light-tight**: matte black print, overlapping tongue-and-groove seam between the halves,
  no gaps except the slits.
- **Cable exit**: one strain-relief hole at the bottom of the sensor half; LED wires cross to
  it inside the hinge side.
- Small board inside the sensor half (perfboard) holds the 4 LDRs; 7-wire cable to the box.

## 3. Main box (on the IV pole)

**Stack-up, from the back:**

| Layer | Height |
|---|---|
| Back wall | 2.0 |
| Battery (lying flat) | 8.0 |
| Gap to PCB bottom | 3.0 |
| PCB | 1.6 |
| Above PCB: connectors 7 mm + plugs + wire bend; SuperMini on sockets ~12.7 mm; OLED jumper plugs ~23 mm | 22 |
| Front wall (lid) | 2.0 |
| **Total depth** | **~39 mm** |

**Footprint**: the PCB (46 × 41.5) plus a 20 mm strip at the bottom end for the TP4056
charger, whose USB-C port points out of the bottom wall.
Inner ~50 × 66 mm, **outer ~54 × 70 × 39 mm**.

- **PCB** on 4 printed standoffs with M2 screws (holes 3.2 mm from the corners).
- **Battery** under the PCB in a printed cradle; **TP4056** in a slot at the bottom wall,
  USB-C cutout with 0.5 mm clearance around the port.
- **Front lid**: OLED window (`oled_view` + 1 mm), the OLED module screwed to the lid's inside
  on 4 M2 posts; jumper wires to J4.
- **Side walls**: power switch (`switch_hole`), push button (`button_hole`), buzzer sound holes
  (buzzer glued in a ring on the inside wall), sensor-cable grommet hole at the top.
- **Back**: two slots for a 25 mm strap around the IV pole, plus a shallow V-groove so the box
  sits straight on poles from 19 to 32 mm.
- **Lid** held by 4 × M2 screws into heat-set inserts or printed bosses.
- **Programming**: remove the lid and lift the SuperMini off its sockets (the compact PCB has
  connectors under its USB-C port).

## 4. Build order in Fusion

1. Create the user parameters above.
2. Import `mech/ivflow_pcb.step` and simple boxes for the battery, TP4056, OLED, buzzer and
   drip chamber (placeholders, sized from the parameters).
3. Main box: shell, PCB standoffs, battery cradle, charger slot, cutouts, strap slots.
4. Lid: OLED window and posts, screw bosses.
5. Sensor clamp: two halves, hinge, latch, LED/LDR pockets, slits, cable exit.
6. Interference check (Inspect → Interference) with the PCB and placeholder parts.
7. Export STL per part for printing, STEP of the assembly, and renders.

## 5. Open items

- Measure the drip chamber (`chamber_d`, `chamber_l`, `tip_depth`) and update the parameters.
- Confirm the button and power-switch models (hole sizes above are for a 12 mm push button
  and an MTS-102 mini toggle).
- Check the battery, TP4056, OLED and buzzer sizes when they arrive.
