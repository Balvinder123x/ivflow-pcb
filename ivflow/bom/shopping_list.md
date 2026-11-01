# IVFlow v1 — shopping list

Everything needed to build one IVFlow. LCSC numbers were checked on lcsc.com (2026-11-01).
"Board qty" is what one board uses. "Buy" adds spares: small SMD parts are easy to lose
and cost very little.

⚠ **Order the PCB last.** The module footprints are provisional until you measure the real
modules, so buy and measure the modules (section 1) first.

## 1. Modules (buy first, then measure)

| Part | Board qty | Buy | Notes |
|---|---|---|---|
| ESP32-C3 SuperMini | 1 | 2 | Usually comes with loose male pin headers |
| TP4056 charger module, **USB-C**, **with protection** (DW01A + 8205A) | 1 | 2 | Must have 6 pads: IN+, IN−, B+, B−, OUT+, OUT−. The 4-pad version has no protection. |

## 2. Parts soldered on the PCB

All resistors and capacitors are 0805.

| Ref | Part | Board qty | Buy | LCSC |
|---|---|---|---|---|
| R1, R2, R3, R5, R22 | Resistor 100 kΩ 1% | 5 | 10 | C149504 |
| R11–R14 | Resistor 10 kΩ 1% (placeholder: tune for your LDRs) | 4 | 10 | C17414 |
| R4, R21 | Resistor 100 Ω 1% | 2 | 10 | C17408 |
| R20 | Resistor 82 Ω 1% | 1 | 10 | C17841 |
| R23, R24 | Resistor 4.7 kΩ 1%, **optional** (only if your OLED has no pull-ups) | 0–2 | 10 | C17673 |
| C1, C2 | Capacitor 10 µF 25 V | 2 | 10 | C15850 |
| C4 | Capacitor 22 µF 25 V | 1 | 5 | C45783 |
| C3, C5, C6 | Capacitor 100 nF 50 V | 3 | 10 | C49678 |
| C11–C14 | Capacitor 10 nF 50 V | 4 | 10 | C1710 |
| D1 | SS14 Schottky diode (SMA) | 1 | 5 | C2480 |
| D3 | 1N4148W diode (SOD-123) | 1 | 5 | C81598 |
| Q1 | AO3401A P-MOSFET (SOT-23) | 1 | 5 | C15127 |
| Q3 | AO3400A N-MOSFET (SOT-23) | 1 | 5 | C20917 |
| Q2 | 2N7002 N-MOSFET (SOT-23) | 1 | 5 | C8545 |
| U3 | AP2112K-3.3 regulator (SOT-23-5) | 1 | 3 | C51118 |
| J1 | JST-PH 2-pin header, vertical (B2B-PH-K-S) | 1 | 3 | C131337 |
| J2 | JST-XH 5-pin header, vertical (B5B-XH-A) | 1 | 3 | C157991 |
| J3, J6, J7, J8 | JST-XH 2-pin header, vertical (B2B-XH-A) | 4 | 6 | C158012 |
| J4, J5 | Male pin header, 2.54 mm (cut 1×4 and 1×5 from a 1×40 strip) | 9 pins | 1 strip | any brand |
| U1 socket | Female header 1×8, 2.54 mm | 2 | 4 | any brand |
| U2 socket | Female headers + male pins for the TP4056, 2.54 mm | TBD | 1×40 strip of each | Count after measuring the module |

## 3. Parts that plug into the connectors

| For | Part | Qty | Notes |
|---|---|---|---|
| J1 | Li-Po battery 3.7 V, 1 cell, with a **JST-PH 2.0 mm** plug | 1 | Check the plug really is PH 2.0 and that **red = pin 1 (+)**. Capacity is your choice (e.g. 1000–2000 mAh). |
| J2 | LDR (e.g. GL5528) | 4 | Buy 6–10; they vary a lot between batches |
| J2 | Small perfboard for the LDR strip | 1 | |
| J3 | 5 mm LED, **green or red** (standard, not high-brightness) | 1 | Buy 5. See note A. |
| J4 | 0.96" I2C OLED, SSD1306, 4-pin | 1 | Check its pin order (GND/VCC may be swapped) |
| J4 | Female-to-female jumper wires | 4 | |
| J6 | Panel-mount power switch, rated ≥ 1 A (toggle or rocker, e.g. KCD1 / MTS-102) | 1 | |
| J7 | Active buzzer 3–5 V, 12 mm | 1 | Must be **active** (beeps on DC) |
| J8 | Momentary panel-mount push button (12 or 16 mm) | 1 | |

## 4. Cables for the JST connectors

| Option | Part | Qty |
|---|---|---|
| **Easiest** | Pre-crimped JST-XH 2.5 mm cable, 2-pin | 4 (buy 6) |
| | Pre-crimped JST-XH 2.5 mm cable, 5-pin | 1 (buy 2) |
| Or crimp your own | XHP-2 housing ×4, XHP-5 housing ×1, SXH-001T-P0.6 crimp contacts ×13 (buy 20) | needs a JST-style crimp tool |

## 5. PCB and hardware

| Part | Qty | Notes |
|---|---|---|
| PCB from JLCPCB: 2-layer, 1.6 mm, HASL | 5 (JLC minimum) | **Order only after the footprints are verified** |
| M2 screws + M2 standoffs | 4 each | Length depends on your case |
| Hook-up wire 22–24 AWG + heat-shrink tubing | some | For the switch, button, buzzer and LED leads |

## 6. Tools and consumables (if you don't already have them)

Fine-tip soldering iron, solder 0.5–0.8 mm, flux pen, tweezers, solder wick, a multimeter,
and calipers for measuring the modules.

## Notes

**A. LED colour.** R20 (82 Ω) from the 3.3 V GPIO gives roughly 12–15 mA through a green or red
LED, which is good. A white or blue LED needs about 3 V, so it would be dim and unreliable at 3.3 V.
LDRs are also most sensitive to green light.

**B. Check before you solder.** Battery plug polarity (red = +), OLED pin order, and that the
TP4056 module has the protection chips (two extra small ICs next to the battery pads).
