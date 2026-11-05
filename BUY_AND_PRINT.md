# IVFlow v1: what to buy, what it costs, where to get it made

Prices are in ₹ incl. GST, checked online on 2026-11-05 where a link is given; others are
typical market prices (marked *est.*). Prices change: treat this as a budget, not a quote.
The full part-by-part list with LCSC numbers is in [ivflow/bom/shopping_list.md](ivflow/bom/shopping_list.md).

## 1. Files to hand over

| To | Send | File(s) |
|---|---|---|
| PCB maker (JLCPCB) | Gerber zip | `fab/ivflow_gerbers_jlcpcb.zip` (2 layers, 1.6 mm, HASL, 46 × 41.5 mm) |
| 3D print shop | 4 STL files + print notes | `mech/export/*.stl` + `mech/export/README.md` |
| Laser cutter | face outline | `mech/export/ivflow_face_2mm_smoked_acrylic.dxf` (or `.svg`) |
| Anyone (preview) | 3D model | `mech/export/ivflow_enclosure_v2_assembly.step` |

Everything is also in one zip: `release/IVFlow_v1_files.zip`.

## 2. Electronics (one device, with spares)

| Item | Buy | Approx. ₹ | Where (online) |
|---|---|---|---|
| ESP32-C3 SuperMini (2 × 8 pins, not "Plus") | 2 | 480–500 | Robosap ~₹238, Probots ~₹242, Techtonics ~₹250 each |
| TP4056 **USB-C** charger **with protection** (6 pads) | 2 | 45–100 | Robu ~₹21, Probots ~₹49 each |
| 0.96" OLED SSD1306, I2C, 4-pin | 1 | 210 | Probots ~₹209 |
| Li-Po 3.7 V **803040** (40 × 30 × 8 mm), JST-PH 2.0 plug | 1 | 230–500 | Makerbazar ~₹229 (1200 mAh), Atomlab ~₹497 |
| LDR GL5528, 5 mm | 6–10 | 60–310 | Sunrom ~₹31 each; Lajpat Rai packs are much cheaper |
| 5 mm LED, **green**, standard | 5 | 10 | *est.* |
| Active buzzer 5 V, 12 mm | 1 | 15–30 | *est.* |
| Push button, panel mount 12 mm | 1 | 20–40 | *est.* |
| Mini toggle switch MTS-102 (6 mm hole) | 1 | 20–35 | *est.* |
| SMD resistors/capacitors/diodes/MOSFETs/regulator (BOM §2) | set | 300–600 | add to the JLCPCB order via LCSC, or local |
| JST-XH headers 2/5/6-pin + JST-PH 2-pin header | set | 60–100 | *est.* |
| Pre-crimped JST-XH cables (2-pin × 6, 5-pin × 2, 6-pin × 2) | set | 150–250 | *est.* |
| Female header 1×8 (× 4) + male pin strip | set | 40–60 | *est.* |
| Hook-up wire 26 AWG + heat-shrink | some | 100–150 | *est.* |
| **PCB, 5 pcs, JLCPCB** incl. shipping + customs | 5 | 850–1,500 | ~$2 boards + shipping; customs vary |

**Electronics subtotal ≈ ₹2,600 – 4,300** (incl. spares and the 5 PCBs).

## 3. Enclosure

| Item | Qty | Approx. ₹ | Notes |
|---|---|---|---|
| 3D printing, 4 parts, ~105 g (pearl white PLA, black PLA, PETG door) | 1 set | 600–2,500 | shops quote ₹5–25 per gram + setup fee; send the STLs for a quote |
| 2 mm black smoked acrylic, laser cut 46.7 × 138.7 mm | 1 (cut 2) | 150–400 | *est.*; small job, often a minimum charge |
| Neodymium magnets 6 × 3 mm | 2 (buy 10) | 80–150 | *est.* |
| M2 screws (4 × 30 mm, 2 × 8 mm) + 2 mm steel rod 60 mm | set | 80–150 | *est.* |
| Black self-adhesive foam sheet 3–4 mm (EVA) | 1 | 80–150 | *est.* |
| Black flocking tape (optional, best light absorber) | small | 300–600 | *est.*, online (telescope flocking) |
| Black hot glue sticks + thin VHB tape | — | 100–200 | *est.* |

**Enclosure subtotal ≈ ₹1,400 – 4,200**

**Total for the first device ≈ ₹4,000 – 8,500** (later devices are much cheaper: the PCB
order gives 5 boards and the spares are already bought).

## 4. Tools (only if you don't have them)

| Tool | Approx. ₹ |
|---|---|
| Temperature-controlled soldering iron (fine tip) | 600–1,500 |
| Solder 0.6–0.8 mm, flux pen, solder wick | 300–500 |
| Multimeter | 400–800 |
| Digital vernier caliper (to check the modules) | 400–900 |
| Hot glue gun | 200–350 |
| Tweezers, flush cutters, small screwdriver set | 300–600 |

## 5. Where to go near Govind Puri metro (Violet Line)

Govind Puri is two stops from **Nehru Place** and one stop from **Harkesh Nagar Okhla**
(Okhla Industrial Area). Directory listings go out of date: **call before you travel**.

| Need | Place | Address / contact (from listings) | Metro |
|---|---|---|---|
| 3D printing | Paradise 3D (FDM / SLA / SLS) | Nehru Place service page: [paradise-3d.com](https://paradise-3d.com/3d-printing-service-in-nehru-place/) | Nehru Place, 2 stops |
| 3D printing / filament | WOL3D Delhi | Nehru Place ([Facebook page](https://www.facebook.com/WOL3Ddelhi/)) | Nehru Place, 2 stops |
| 3D printing (online, delivered) | Dwart Industries | ships to Delhi NCR in ~2 working days: [dwartindustries.com](https://dwartindustries.com/3d-printing-service-in-delhi/) | — |
| More 3D print shops | listings | [Sulekha: Nehru Place 3D printing](https://www.sulekha.com/3d-printing-services/nehru-place-delhi) | — |
| Laser cutting | Adtek Print & Media | B-44, Okhla Industrial Area Phase 1, New Delhi 110020 (laser cutting ~₹400/hour; ask about acrylic) | Harkesh Nagar Okhla / Okhla NSIC |
| Laser cutting | Shri Balaji Laser Cut & Fabrication | DSIDC Shed No. 190, near Union Bank, Okhla Industrial Area Phase 1, Delhi 110020 | Harkesh Nagar Okhla |
| Acrylic / signage | Mak Graphicz | Abul Fazal Enclave Part 2, Jamia Nagar, New Delhi 110025 (acrylic cutting, signage) | Jasola / Okhla Vihar |
| Tools, cables, general electronics | **Nehru Place** market | computer and electronics hub | Nehru Place, 2 stops |
| Electronic components (LDR, LED, buzzer, switch, headers, wire) | **Lajpat Rai Market**, Chandni Chowk | the main component market in Delhi (e.g. Raj Laxmi Traders, 314 New Lajpat Rai Market) | Chandni Chowk (Yellow Line) |

**Tip:** acrylic sign shops and laser cutters often have smoked/tinted acrylic offcuts;
take the DXF on a USB stick. For the 3D prints, send all four STL files and the print
notes table and ask for one combined quote with the colours named (matte pearl white,
matte black, PETG white).

## Sources

- SuperMini: [Robosap](https://robosap.in/product/esp32-c3-super-mini-usb-c-type-development-board/), [Probots](https://probots.co.in/esp32-c3-supermini-development-board-risc-v-wifi-bt-type-c.html), [Techtonics](https://techtonics.in/product/esp32-c3-super-mini-development-board-soldered-headers/)
- TP4056 USB-C: [Robu](https://stg.robu.in/product/tp4056-1a-li-ion-battery-charging-board-micro-usb-with-current-protection-type-c-connector), [Probots](https://probots.co.in/tp4056-1a-li-ion-lithium-battery-charging-module-with-current-protection-type-c.html), [Robocraze](https://robocraze.com/products/tp4056-battery-charger-c-type-module-with-protection-1)
- OLED: Probots listing "0.96 inch 128x64 OLED Display Module, I2C 4-pin, SSD1306" at ₹209 (search result on [probots.co.in](https://probots.co.in/))
- Battery 803040: [Makerbazar](https://makerbazar.in/products/generic-3-7v-1200mah-lithium-polymer-battery), [Atomlab](https://atomlabindia.com/product/kp-original-803040-3-7v-1200mah-rechargeable-battery)
- LDR GL5528: [Sunrom](https://sunrom.com/p/ldr-photosensitive-resistor-waterproof-gl5528)
- 3D print prices: [TechEnclave](https://techenclave.com/t/3d-printing-service-pan-india/385629), [IndiaMART Make3D](https://m.indiamart.com/make3d-dotin/3d-printing-service.html), [iamrapid](https://iamrapid.com/knowledge-hub/3d-printing-cost-guide/)
- JLCPCB to India: [Zbotic cost guide](https://zbotic.in/how-to-order-pcb-from-jlcpcb-and-pcbway-india-cost-guide/), [JLCPCB customs help](https://jlcpcb.com/help/article/Customs,-Duties-and-Taxes)
- Laser cutting Okhla: [IndiaMART (Adtek)](https://www.indiamart.com/proddetail/laser-cutting-services-12753468412.html), [Justdial (Shri Balaji)](https://www.justdial.com/Delhi/Shri-Balaji-Laser-Cut-Fabrication-Near-By-Union-Bank-Okhla-Industrial-Area-Phase-1/011PXX11-XX11-230428143611-C6K1_BZDET), [IndiaMART acrylic cutting Delhi](https://dir.indiamart.com/delhi/acrylic-cutting-service.html)
- Lajpat Rai Market: [Tata Nexarc (Raj Laxmi Traders)](https://www.tatanexarc.com/company/raj-laxmi-traders-utn8954raj15vtq/)
