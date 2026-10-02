# Arcade Remote

A retro-style arcade controller for robots — a 4-way arcade joystick, five arcade buttons and an ESP32-C6, in a 3D-printed cabinet that fits in your hands.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Platform: ESP32-C6](https://img.shields.io/badge/platform-ESP32--C6-black.svg)](https://www.espressif.com/en/products/socs/esp32-c6)
[![Website](https://img.shields.io/badge/web-rookidroid.com-ff7f2a.svg)](https://rookidroid.com/)
[![Build Guide](https://img.shields.io/badge/guide-build%20the%20arcade%20remote-9c27b0.svg)](https://rookidroid.com/build-the-arcade-remote/)

<img src="./images/arcade_top.jpg" alt="arcade_top" width="400"/> <img src="./images/arcade_back.jpg" alt="arcade_back" width="400"/>

**Jump to:** [Bill of Materials](#bill-of-materials) · [3D-Printed Parts](#3d-printed-parts) · [Assembly](#assembly) · [Firmware](#firmware) · [Controls](#controls) · [UDP Protocol](#udp-protocol) · [Troubleshooting](#troubleshooting)

<details>
<summary><b>Table of Contents</b></summary>

- [Introduction](#introduction)
  - [Specifications](#specifications)
- [Bill of Materials](#bill-of-materials)
  - [Electronics](#electronics)
  - [Connection Diagram](#connection-diagram)
  - [Pin Map](#pin-map)
  - [Other Parts](#other-parts)
- [3D-Printed Parts](#3d-printed-parts)
- [Assembly](#assembly)
- [Firmware](#firmware)
  - [Prerequisites](#prerequisites)
  - [Upload](#upload)
  - [Configuration](#configuration)
  - [Status LED](#status-led)
- [Controls](#controls)
- [UDP Protocol](#udp-protocol)
- [Troubleshooting](#troubleshooting)
- [Related Projects](#related-projects)
- [License](#license)
- [Support](#support)

</details>

## Introduction

This remote turns real arcade hardware into a WiFi controller for the [RookiDroid hexapod](https://github.com/rookidroid/hexapod) — **all three of them**, Nougat, Mochi and Macaroon — and any other robot that speaks the same binary UDP protocol. Only the `ssid` line in the sketch changes between robots; see [Configuration](#configuration).

Prefer a step-by-step walkthrough with photos? The same build is documented as the [Build the Arcade Remote](https://rookidroid.com/build-the-arcade-remote/) guide on rookidroid.com.

- **Real arcade feel** — a microswitch joystick and five snap-in arcade buttons, no analog sticks and no deadzone
- **All-digital inputs** — nine switches on `INPUT_PULLUP` GPIOs, scanned every 5 ms; a command must hold for 30 ms before it is sent, which filters switch bounce and half-pressed button combos
- **WiFi direct to the robot** — the remote joins the robot's own access point, so no router is involved, with WiFi power saving off for low latency
- **Instant send + 20 Hz heartbeat** — a new command goes out as soon as it settles, and the current one is repeated every 50 ms, so releasing a control stops the robot right away
- **Adjustable speed** — five speed levels from 20 % to 100 % of the robot's gait speed, stepped with special + joystick and remembered across power cycles
- **RGB status LED** — shows the link state, what the remote is sending and the speed level, visible through the window in the top panel
- **Battery powered** — a single 9 V battery in a magnetically-latched bay in the back
- **Fully 3D-printed cabinet** — one Bambu Studio project prints the whole enclosure

### Specifications

| Item | Value |
| ---- | ----- |
| **Controller** | ESP32-C6 SuperMini on the RookiDroid remote carrier board |
| **Inputs** | 4-way microswitch joystick + 5 arcade push buttons |
| **Feedback** | 1 × WS2812 (NeoPixel) RGB status LED on `GP8` |
| **Power** | 9 V battery → on-board Mini360 buck converter → 5 V, with a slide switch on the board |
| **Connectivity** | 2.4 GHz WiFi — the remote joins the robot's access point as a station |
| **Control** | 7-byte binary UDP packets to `192.168.4.1:1234`, carrying the command and the speed level |
| **Update rate** | Sent on change (30 ms settle), plus a 20 Hz heartbeat that runs continuously, including standby |
| **Enclosure** | 3D-printed body, cover, bottom plate and magnetic battery cover |

## Bill of Materials

### Electronics

| Name | Thumbnail | Required # | Specifications | Note |
| ---- | --------- | ---------- | -------------- | ---- |
| Controller board | <img src="./images/arcade_controller.jpg" alt="controller_board" width="300"/> | 1 | ESP32-C6 SuperMini on a carrier board with a Mini360 buck converter, power switch, 2-pin battery terminal, a 5-pin joystick header (`GP0`–`GP3`) and a 2×7 button header | [Purchase](https://rookidroid.com/product/arcade-controller-board/) — or use a bare ESP32-C6 SuperMini, wiring the switches straight to the GPIOs in the [pin map](#pin-map) and feeding it 5 V |
| Arcade joystick | <img src="./images/joystick.jpg" alt="joystick" width="300"/> | 1 | Microswitch joystick, 97 × 65 mm mounting plate, ~119 mm overall height, 5-pin harness | Ball top; the harness plugs into the joystick header |
| Arcade push button | <img src="./images/push_button.jpg" alt="push_button" width="300"/> | 5 | 30 mm snap-in button with a microswitch (2 terminals) | Any five colors — four for the direction cluster, one for the special/modifier button |
| 9 V battery connector | <img src="./images/battery_connector.jpg" alt="battery_connector" width="300"/> | 1 | Snap connector with flying leads | Screws into the 2-pin terminal block — mind the polarity |
| 9 V battery | <img src="./images/9v_battery.jpg" alt="9v_battery" width="300"/> | 1 | Alkaline or rechargeable | Sits in the bay behind the magnetic cover |
| Jumper wires | — | ~11 | 2.8 mm spade or Dupont, 150–200 mm | One per button terminal; the joystick comes with its own harness |

### Connection Diagram

![diagram](./images/diagram.svg)

Every input is a plain switch to ground: the firmware enables the internal pull-ups, so one terminal goes to its signal pin and the other to any `GND` pin.

### Pin Map

| Input | Signal | GPIO | Where it lands on the board |
| ----- | ------ | ---- | --------------------------- |
| Joystick up | `JS_UP` | `GP3` | 5-pin joystick header |
| Joystick down | `JS_DOWN` | `GP2` | 5-pin joystick header |
| Joystick left | `JS_LEFT` | `GP0` | 5-pin joystick header |
| Joystick right | `JS_RIGHT` | `GP1` | 5-pin joystick header |
| Button — up | `BT_UP` | `GP14` | 2×7 button header |
| Button — down | `BT_DOWN` | `GP15` | 2×7 button header |
| Button — left | `BT_LEFT` | `GP18` | 2×7 button header |
| Button — right | `BT_RIGHT` | `GP19` | 2×7 button header |
| Button — special | `BT_SPECIAL` | `GP20` | 2×7 button header |
| Status LED | `PIN_RGB` | `GP8` | On-board WS2812 of the SuperMini |

The four direction buttons are the cluster outlined on the top panel; the button sitting on its own is the special (modifier) button.

### Other Parts

| Name | Spec | Required # | Installation |
| ---- | ---- | ---------- | ------------ |
| Screw | M3 10 mm | 8 | Cover to body |
| Nut | M3 | 8 | Cover to body |
| Screw | M4 10 mm | 4 | Joystick mounting plate |
| Nut | M4 | 4 | Joystick mounting plate |
| Screw | M2 4 mm | 4 | Controller board to body |
| Magnet | 6 mm dia. × 2 mm | 4 | Hold the battery cover |

## 3D-Printed Parts

The whole cabinet is one Bambu Studio project: [`3d model/arcade.3mf`](./3d%20model/arcade.3mf), also a [free download](https://rookidroid.com/product/arcade-controller/) from the RookiDroid shop. The Fusion 360 source is [`3d model/arcade.f3d`](./3d%20model/arcade.f3d).

| Part | Required # | Note |
| ---- | ---------- | ---- |
| arcade body | 1 | Holds the controller board and the battery bay |
| arcade cover | 1 | Top panel with the joystick, button and LED cut-outs; multi-material, so the logo and outlines print in a second color |
| bottom | 1 | Closes the underside |
| battery cover | 1 | Magnetic latch, no screws |

**Print settings** (as saved in the project):

- Printer profile: Bambu Lab H2S, 0.4 mm nozzle
- Layer height: 0.2 mm
- Material: PLA
- Multi-color: the cover uses extra filaments for the logo and the button outlines — print it in a single color if you don't have an AMS

## Assembly

1. **Print the parts** and clean up the cut-outs — the buttons and the joystick shaft need a snug snap fit.
2. **Mount the inputs in the cover.** Snap the five buttons in, then bolt the joystick plate down with the M4 hardware.

   <img src="./images/arcade_front.jpg" alt="arcade_front" width="450"/>

3. **Mount the controller board** in the body on the M2 standoffs, with the USB-C port reachable for flashing.
4. **Wire it up.** Plug the joystick harness into the 5-pin header, then run one wire from each button to its GPIO on the 2×7 header and one to a `GND` pin — see the [connection diagram](#connection-diagram).
5. **Battery.** Screw the 9 V connector leads into the terminal block, minding polarity, and press the four magnets into the battery bay and its cover.
6. **Close it up** with the M3 screws and nuts, flash the [firmware](#firmware), and power it on.

## Firmware

The sketch lives in [`software/arcade/arcade.ino`](./software/arcade/arcade.ino).

### Prerequisites

- [Arduino IDE](https://www.arduino.cc/en/software) 2.x
- **esp32** board package 3.x or newer (Espressif Systems) — required for ESP32-C6 support
- **Adafruit NeoPixel** library

### Upload

1. Open `software/arcade/arcade.ino`.
2. Select **ESP32C6 Dev Module** as the board, and the port that appears when you plug in the USB-C cable.
3. Upload. If the port never enumerates, hold **BOOT**, tap **RESET**, release **BOOT**, and try again.
4. Open the Serial Monitor at **115200 baud** to watch the WiFi connection.

### Configuration

Edit these near the top of the sketch to match your robot:

| Setting | Default | Meaning |
| ------- | ------- | ------- |
| `ssid` | `hexapod_nougat` | The access point the robot hosts |
| `password` | `hexapod_1234` | Its passphrase |
| `udpAddress` | `192.168.4.1` | The robot's IP as the AP |
| `udpPort` | `1234` | UDP port the robot listens on |

The remote connects in the background and keeps retrying, so the robot and the remote can be powered up in either order. If the robot drops out, the remote reconnects on its own when it comes back.

The same remote drives every RookiDroid hexapod — each one hosts its own access point at `192.168.4.1` and listens on port `1234`, so only `ssid` changes:

| Robot | `ssid` | `password` | Build guide |
| ----- | ------ | ---------- | ----------- |
| Hexapod Nougat | `hexapod_nougat` | `hexapod_1234` | [Build Nougat](https://rookidroid.com/build-your-own-nougat/) |
| Hexapod Mochi | `hexapod` | `hexapod_1234` | [Build Mochi](https://rookidroid.com/build-your-own-mochi/) |
| Hexapod Macaroon | `hexapod_macaroon` | `hexapod_1234` | [Build Macaroon](https://rookidroid.com/build-your-own-macaroon/) |

If you changed the credentials in your robot's own `config.h`, match them here.

### Status LED

| Color | Meaning |
| ----- | ------- |
| Off | No power |
| Blinking blue | Connecting to the robot for the first time |
| Blinking red | WiFi lost; the remote keeps retrying and recovers when the robot comes back |
| Green | Connected, standing by |
| Cyan | Connected, walking or turning |
| Yellow | Connected, turbo (fast forward/backward) |
| Magenta | Connected, body motion (pitch, roll, yaw or twist) |
| White flash | Speed level changed |

While connected, the LED **brightness** shows the speed level: dimmest at 20 %, brightest at 100 %.

## Controls

The firmware reads all nine switches every 5 ms and maps them to exactly one command. Once a new command has held for 30 ms, it is sent right away. The current command is also resent every 50 ms as a heartbeat. Nothing pressed sends `CMD_STANDBY`, so the robot stops as soon as you let go.

The 30 ms settle time means you don't have to press combos such as **special + up** perfectly together: the command the robot gets is the finished combo, not whichever button closed first.

**Joystick** (takes priority over the direction buttons; special + joystick changes the speed instead, see below):

| Joystick | Command | Action |
| -------- | ------- | ------ |
| Up | `CMD_WALK_0` | Walk forward |
| Down | `CMD_WALK_180` | Walk backward |
| Left | `CMD_WALK_L90` | Sidestep left |
| Right | `CMD_WALK_R90` | Sidestep right |
| Up + Left | `CMD_WALK_L45` | Walk forward-left |
| Up + Right | `CMD_WALK_R45` | Walk forward-right |
| Down + Left | `CMD_WALK_L135` | Walk backward-left |
| Down + Right | `CMD_WALK_R135` | Walk backward-right |

**Buttons** (when the joystick is centered):

| Button | Command | Action |
| ------ | ------- | ------ |
| Up | `CMD_WALK_0` | Walk forward |
| Down | `CMD_WALK_180` | Walk backward |
| Left | `CMD_TURN_LEFT` | Turn left in place |
| Right | `CMD_TURN_RIGHT` | Turn right in place |
| Special + Up | `CMD_ROTATE_X` | Body pitch |
| Special + Left | `CMD_ROTATE_Y` | Body roll |
| Special + Right | `CMD_ROTATE_Z` | Body yaw |
| Special + Down | `CMD_TWIST` | Body twist |

**Turbo:** hold the **up** button while pushing the joystick up for `CMD_FAST_FORWARD`, or the **down** button while pulling the joystick down for `CMD_FAST_BACKWARD`.

**Speed:** hold **special** and flick the joystick **up** to speed up one level, or **down** to slow down one level. The robot holds still while special and the joystick are both pressed. There are five levels — 20, 40, 60, 80 and 100 % of the robot's gait speed — starting at 60 %. Each flick steps one level (holding does not repeat), the LED flashes white, and its brightness then shows the new level. The level is saved in the remote's flash and restored at power-on, and it is sent with every packet, so the robot always follows the remote.

## UDP Protocol

Each packet is 7 bytes, little-endian and unpadded, sent to `192.168.4.1:1234`:

| Offset | Field | Type | Value |
| ------ | ----- | ---- | ----- |
| 0 | `magic` | `uint8` | `0xA5` — motion command |
| 1 | `cmd` | `uint8` | Command ID from the table below |
| 2–5 | `seq_num` | `uint32` | Increments on every packet |
| 6 | `speed_pct` | `uint8` | Gait speed in percent: 20, 40, 60, 80 or 100 |

> **Robot firmware:** the speed byte needs hexapod firmware with motion-speed support. Older firmware only accepts the 6-byte packet and ignores this remote — update the robot too.

| ID | Command | Sent by this remote |
| -- | ------- | ------------------- |
| 0 | `CMD_STANDBY` | Yes — nothing pressed |
| 1 | `CMD_WALK_0` | Yes |
| 2 | `CMD_WALK_180` | Yes |
| 3 | `CMD_WALK_R45` | Yes |
| 4 | `CMD_WALK_R90` | Yes |
| 5 | `CMD_WALK_R135` | Yes |
| 6 | `CMD_WALK_L45` | Yes |
| 7 | `CMD_WALK_L90` | Yes |
| 8 | `CMD_WALK_L135` | Yes |
| 9 | `CMD_FAST_FORWARD` | Yes — turbo |
| 10 | `CMD_FAST_BACKWARD` | Yes — turbo |
| 11 | `CMD_TURN_LEFT` | Yes |
| 12 | `CMD_TURN_RIGHT` | Yes |
| 13 | `CMD_CLIMB_FORWARD` | Not mapped to a control |
| 14 | `CMD_CLIMB_BACKWARD` | Not mapped to a control |
| 15 | `CMD_ROTATE_X` | Yes — special + up |
| 16 | `CMD_ROTATE_Y` | Yes — special + left |
| 17 | `CMD_ROTATE_Z` | Yes — special + right |
| 18 | `CMD_TWIST` | Yes — special + down |

The layout matches `UdpControlPacket` in the hexapod firmware — see the [hexapod UDP reference](https://github.com/rookidroid/hexapod#sending-udp-commands) for the other packet types the robot understands.

## Troubleshooting

| Symptom | Things to check |
| ------- | --------------- |
| LED keeps blinking blue | The robot isn't powered up, or the SSID/password don't match — the remote keeps retrying until it finds the AP |
| LED is green but the robot ignores the remote | `udpAddress` and `udpPort` must match the robot, the robot must be in its normal (non-calibration) mode, and its firmware must accept the 7-byte packet — see [UDP Protocol](#udp-protocol) |
| Robot walks slowly | The speed level is low — hold special and flick the joystick up; a dim LED means a low level |
| One direction never triggers | Check that switch's signal wire and its `GND` — an unconnected `INPUT_PULLUP` pin just reads high forever |
| Diagonals don't work | The joystick has a 4-way restrictor plate fitted; swap in the 8-way gate |
| Robot keeps moving after you let go | Standby packets aren't arriving — check the WiFi link; the robot should also have its own failsafe |
| Board doesn't enumerate over USB | Hold **BOOT**, tap **RESET**, release **BOOT**, then upload |

## Related Projects

| Project | What it is |
| ------- | ---------- |
| [Build the Arcade Remote](https://rookidroid.com/build-the-arcade-remote/) | The four-phase build guide for this remote, with photos and wiring |
| [hexapod](https://github.com/rookidroid/hexapod) | The robot this remote drives — Nougat, Mochi and Macaroon all share the UDP protocol |
| [Arcade Controller](https://rookidroid.com/product/arcade-controller/) | The 3D print files for this cabinet, as a free download |
| [Arcade Controller Board](https://rookidroid.com/product/arcade-controller-board/) | The ESP32-C6 carrier board used here |
| [hexapod-link](https://github.com/rookidroid/hexapod-link) | Desktop app for real-time pose streaming to the hexapod |

## License

This project is licensed under the **MIT License** — see [LICENSE](./LICENSE) for the full text.

## Support

- Website: [rookidroid.com](https://rookidroid.com/)
- Build guide: [Build the Arcade Remote](https://rookidroid.com/build-the-arcade-remote/)
- Email: [info@rookidroid.com](mailto:info@rookidroid.com)
- Bugs and build questions: [GitHub Issues](https://github.com/rookidroid/remote-arcade/issues)
