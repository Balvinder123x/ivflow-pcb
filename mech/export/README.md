# IVFlow enclosure v2: files to make

Made by `mech/fusion_export.py` (STL, STEP) and `mech/make_face_cut.py` (DXF, SVG).
All sizes in millimetres. STL files are in their assembled orientation (Z up), so rotate
them in the slicer as described below.

| File | What it is | Material | Approx. plastic |
|---|---|---|---|
| `ivflow_chassis_pearl_white.stl` | Front frame + head shell (OLED, PCB, battery mount here) | Matte pearl white PLA | 47 g |
| `ivflow_back_shell_pearl_white.stl` | Lower back cover (TP4056, button, switch, buzzer) | Matte pearl white PLA | 14 g |
| `ivflow_door_pearl_white_PETG.stl` | Hinged door with the snap latch | Pearl / white **PETG** (the latch must flex) | 11 g |
| `ivflow_sensor_insert_black.stl` | Black sensor insert (channel, LED hole, slit, LDR pocket) | **Matte black PLA** | 31 g |
| `ivflow_face_2mm_smoked_acrylic.dxf` / `.svg` | Front face cut line (46.7 × 138.7 mm) | **2 mm black smoked (tinted) acrylic**, laser cut | — |
| `ivflow_enclosure_v2_assembly.step` | Whole assembly incl. PCB and stand-in parts | for viewing / sharing | — |

Weights are at about 60 % effective fill; ask the print shop for a quote from the files.

## Print settings (FDM)

| Part | Orientation on the bed | Settings |
|---|---|---|
| Chassis | front face down (the acrylic recess on the bed) | 0.2 mm layers, 4 walls, 25 % gyroid, supports "touching build plate" only if the slicer asks |
| Back shell | back face down | 0.2 mm, 3 walls, 20 % |
| Door | on its right edge (the latch arm's outer face on the bed), with a brim, so the layers run along the arm | PETG, 0.2 mm, 4 walls, 40 %. **Not** flat: the arm would snap along the layer lines |
| Sensor insert | standing on its bottom face | **0.12–0.16 mm layers** (the 1.2 mm slit must stay clean), 4 walls, 30 %, no supports |

After printing: clean the 1.2 mm slit with a 1 mm drill bit / blade, test-fit the insert
(it slides in from the back), drill the hinge holes through with a 2.2 mm bit.

## Hardware for the enclosure

| Item | Qty | Use |
|---|---|---|
| M2 × 30 screws | 4 | back shell → through the PCB holes → chassis standoffs |
| M2 × 8 screws | 2 | sensor insert, from below |
| 2 mm steel rod (or M2 threaded rod) 60 mm | 1 | hinge pin |
| Neodymium magnet 6 × 3 mm | 2 | door catch (glue in, check the poles attract) |
| Black foam sheet 3–4 mm, self-adhesive | 1 small sheet | channel lining + door inside; cut holes at the LED and the slit |
| Black flocking tape (optional, best) | small piece | channel walls |
| Black hot glue sticks | few | seal the LED/LDR lead spaces in the insert |
| 3M VHB / double-sided tape, thin | small piece | holds the acrylic face in its recess |
