# MindPaw 完整引脚接线图 (V2.0)
## HLK-V20 取代 LD3320 后的最终方案

## 1. ESP12F 完整引脚分配表

```
ESP12F 封装引脚排列 (面向芯片, 顶部凹口向上):
┌─────────────────────────────────┐
│  RST □                     TX □│← GPIO1 (串口TX) ✅ 空闲!
│  ADC □ (A0, 电池监测)      RX □│← GPIO3 (串口RX) ✅ 空闲!
│  EN  □                     D5 □│← GPIO14 → Servo 1 SCK + OV2640 SCK
│  IO16□← D0 → Servo 2/扬声器  D6 □│← GPIO12 → Servo 3 + OV2640 MISO
│  IO14□← D5 → Servo 1        D7 □│← GPIO13 → Servo 4 + OV2640 MOSI
│  IO12□← D6 → Servo 3        D8 □│← GPIO15 → OV2640 CS + 10KΩ↓GND
│  IO13□← D7 → Servo 4        3V3□│
│  VCC□                         GND□│
│  CLK□(闪存)                  GND□│
│  SDO□(闪存)                 3V3□│
│  CMD□(闪存)                 EN □│
│  SD1□(闪存)                RST □│
│  SD2□(闪存)                GND □│
│  SD3□(闪存)               D8□│← GPIO15
│  GND□                     D4□│← GPIO2 → Button 1 (INPUT_PULLUP)
│                            D3□│← GPIO0 → HLK-V20 TX (SoftwareSerial RX)
│                      D1□│← GPIO5 → OLED SCL (I2C时钟)
│  ┌─ 3.3V ─ 接SD3 ┐    D2□│← GPIO4 → OLED SDA (I2C数据)
└───────────────────────────────┘
```

## 2. 模块接线总表

| 模块 | ESP12F 引脚 | 连接方式 | 备注 |
|------|------------|---------|------|
| **Servo 1** | **GPIO14 (D5)** | 信号线 → Servo1 橙线 | 通过 1KΩ 与 OV2640 SCK 共享 |
| **Servo 2** | **GPIO16 (D0)** | 信号线 → Servo2 橙线 | 独占（也可以挪给扬声器） |
| **Servo 3** | **GPIO12 (D6)** | 信号线 → Servo3 橙线 | 通过 1KΩ 与 OV2640 MISO 共享 |
| **Servo 4** | **GPIO13 (D7)** | 信号线 → Servo4 橙线 | 通过 1KΩ 与 OV2640 MOSI 共享 |
| 舵机电源 | **VCC (5V 外接)** | 舵机红线 → 5V 电池 | ⚠不要用 ESP 的 3.3V |
| 舵机地 | **GND** | 舵机棕线 → 共地 | — |
| **OLED I2C** | **GPIO4 (D2) = SDA** | I2C 数据线 | 4.7KΩ 上拉到 3.3V |
| | **GPIO5 (D1) = SCL** | I2C 时钟线 | 4.7KΩ 上拉到 3.3V |
| | VCC → 3.3V, GND → GND | — | — |
| **OV2640** | **GPIO15 (D8) = CS** | CS → OV2640 CS | **10KΩ 下拉到 GND（必需！）** |
| | **GPIO14 (D5) = SCK** | 1KΩ → OV2640 SCK | 与 Servo 1 共享 |
| | **GPIO13 (D7) = MOSI** | 1KΩ → OV2640 MOSI | 与 Servo 4 共享 |
| | **GPIO12 (D6) = MISO** | 1KΩ → OV2640 MISO | 与 Servo 3 共享 |
| | VCC → 3.3V, GND → GND | — | 实测 3.3V 供电够 |
| | **SDA/SDI** | → OV2640 SDA | SDA 需 4.7KΩ 上拉 |
| | **SCL/SIOC** | → OV2640 SCL | 与 SDA 配合 I2C 控制 |
| **HLK-V20** | **GPIO0 (D3) = UART RX** | HLK-V20 TX → D3 | SoftwareSerial 仅接收 |
| | 不接 RX | HLK-V20 RX 悬空 | 仅在 PC 配置时接 USB-TTL |
| | VCC → 3.3V~5V, GND → GND | — | 可宽电压 3.3~5V |
| **扬声器** | **GPIO16 (D0)** | 信号 → 三极管基极 | Servo 2 和二选一 |
| 或保留 Servo 2 | **GPIO16 (D0)** | 仅接 Servo 2 | 扬声器改用 D2/D3？ |
| **Button 1** | **GPIO2 (D4)** | 按键 → GND | INPUT_PULLUP |
| **电池 ADC** | **A0** | 分压电阻 → 电池+ | 8.4V→1.0V 分压 |
| **串口调试** | **GPIO1 (TX)** | USB-TTL RX | ✅ 完全保留！ |
| | **GPIO3 (RX)** | USB-TTL TX | ✅ 完全保留！ |

## 3. 扬声器接线详解

### 3.1 无源喇叭 + 三极管驱动（推荐，¥2）

扬声器本身需要 **2 根线**（喇叭两根引脚），但控制它只需要 **1 个 GPIO**：

```
                    +5V
                     │
                    ╱
                  ╱ 喇叭 (8Ω/0.5W)
                  ╲
                    │
                    │  C
GPIO16(D0) ──[1KΩ]── B  NPN三极管 (S8050/2N2222)
                      E
                      │
                     GND
```

- **喇叭本身**：2 根线（+ → 5V，- → 三极管 C 极）
- **控制电路**：1 个 GPIO + 1 个 1KΩ + 1 个 NPN 三极管
- **总共占用引脚**：**GPIO16 1 个**

### 3.2 有源蜂鸣器模块（最简单，¥1）

```
GPIO16(D0) ──→ 蜂鸣器模块信号引脚
蜂鸣器模块 VCC ──→ 3.3V
蜂鸣器模块 GND ──→ GND
```

有源蜂鸣器只能发单音调（不能 `tone()` 调频），不推荐。

### 3.3 功放模块 + 小喇叭（音质最好，¥5）

用 MAX98357/PAM8403 功放板：

```
GPIO16(D0) ──→ 功放模块 IN
功放模块 VCC ──→ 5V 电池直供
功放模块 GND ──→ 共地
功放模块 OUT+,OUT- ──→ 喇叭 2 根线
```

## 4. 完整的电路连接图

```
                                 +5V (电池直供)
                                  │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
     Servo1-4                喇叭/蜂鸣器                  HLK-V20
     (红线→5V)                   │                         │
                                ╱                          │
                              ╱ 8Ω                        │
                              ╲                            │
                                │                          │
                                C                          │
                          ┌────┤ NPN                      │
                          │    │  三极管                    │
                          │ 1KΩ E                          │
                          │    │                           │
                          │    GND                         │
                          │                                │
ESP12F                     │                                │
┌──────────────────────────┼────────────────────────────────┐
│                          │                                │
│  GPIO16(D0) ─────────────┘        GPIO0(D3) ◄──────── HLK-V20 TX
│                                                       
│  GPIO14(D5) ──┐──1KΩ──▶ Servo 1           共用    │
│               └──▶ OV2640 SCK                      │
│                                       3.3V──┬──┤   │
│  GPIO12(D6) ──┐──1KΩ──▶ Servo 3            │  4.7KΩ│
│               └──▶ OV2640 MISO              │  4.7KΩ│
│                                        ┌────┴──┘   │
│  GPIO13(D7) ──┐──1KΩ──▶ Servo 4        │           │
│               └──▶ OV2640 MOSI         │           │
│                                   GPIO4(D2)── OLED SDA
│  GPIO15(D8) ───▶ OV2640 CS + 10KΩ↓GND  GPIO5(D1)── OLED SCL
│                                                   
│  GPIO2(D4) ◀═ Button 1 ═ GND           A0 ── 分压 ──▶ 电池+
│                                                   
│  GPIO1(TX) ◀═══ USB-TTL RX (调试)            GND ──▶ 共地
│  GPIO3(RX) ◀═══ USB-TTL TX (调试)    3.3V ──▶ OLED/OV2640
│                                                   
└─────────────────────────────────────────────────────────┘
                              │
                           ◇ GND
```

## 5. 最终引脚占用清单

| 引脚 | 功能 | 优先级 |
|------|------|--------|
| **GPIO0 (D3)** | HLK-V20 RX (SoftwareSerial) | ✅ 必须 |
| **GPIO2 (D4)** | Button 1 (INPUT_PULLUP) | ✅ 建议保留 |
| **GPIO4 (D2)** | OLED SDA (I2C) | ✅ 必须 |
| **GPIO5 (D1)** | OLED SCL (I2C) | ✅ 必须 |
| **GPIO12 (D6)** | Servo 3 + OV2640 MISO (1KΩ共享) | ✅ 必须 |
| **GPIO13 (D7)** | Servo 4 + OV2640 MOSI (1KΩ共享) | ✅ 必须 |
| **GPIO14 (D5)** | Servo 1 + OV2640 SCK (1KΩ共享) | ✅ 必须 |
| **GPIO15 (D8)** | OV2640 CS + 10KΩ↓GND | ✅ 必须 |
| **GPIO16 (D0)** | ⚠二选一: Servo 2 或 扬声器 | ⚠ 看需求 |
| **GPIO1 (TX)** | 串口调试 | ✅ 保留 |
| **GPIO3 (RX)** | 串口调试 | ✅ 保留 |
| **A0** | 电池 ADC | ✅ 建议 |
| **3.3V** | OLED/OV2640/HLK-V20 供电 | — |
| **5V (外接)** | 舵机/扬声器供电 | — |
| **GND** | 共地 | — |

## 6. 关于 Servo 2 和扬声器的取舍

GPIO16 (D0) 只能二选一：

### 方案 A：保留 Servo 2，扬声器改用其他引脚
```
GPIO16 → Servo 2
扬声器 → GPIO2(D4) + 按键复用 (按键短按=按钮，长按=发声?)
      → 或放弃 (用 OLED 的 buzzer? 不推荐)
```

### 方案 B：用扬声器，Servo 2 拆掉
```
GPIO16 → 扬声器 (三极管驱动)
Servo 2 拆掉 → 机器狗变成 3 条腿 (不行)
```

### 方案 C：换 ESP32（推荐，¥15）
```
ESP32 有 20+ 可用 GPIO，全部独立分配：
  Servo 1~4 → 任意 4 个引脚 (互不共享)
  OV2640   → 独立 SPI (不用共享)
  HLK-V20  → 独立 UART
  扬声器    → 独立 PWM
  OLED     → 独立 I2C
  还多 10 个 GPIO → 加传感器!
```

### ⭐ 最佳方案：PCA9685 舵机驱动板 (¥5)

```
ESP12F                        PCA9685 舵机驱动板
┌────────┐                   ┌──────────────────┐
│ GPIO4  ├──── SDA ────────┤ SDA              │
│ GPIO5  ├──── SCL ────────┤ SCL              │
│        │                   │                  │
│        │                   │ PWM0 ──▶ Servo 1 │
│        │                   │ PWM1 ──▶ Servo 2 │
│        │                   │ PWM2 ──▶ Servo 3 │
│        │                   │ PWM3 ──▶ Servo 4 │
│        │                   │ PWM4~15 ── 备用   │
│ GPIO14 ├──▶ OV2640 SCK     │                  │ (独占)
│ GPIO12 ├──▶ OV2640 MISO    │                  │ (独占)  
│ GPIO13 ├──▶ OV2640 MOSI    │                  │ (独占)
│ GPIO15 ├──▶ OV2640 CS     │                  │ (独占)
│ GPIO0  ├──▶ HLK-V20 TX    │                  │ (独占)
│ GPIO16 ├──▶ 扬声器         │                  │ (独占)
│ GPIO2  ├──▶ Button        │                  │
└────────┘                   └──────────────────┘
```

加 PCA9685 后：
- ✅ **所有模块独立接线，不再共享**
- ✅ **舵机控制更稳定**（PCA9685 硬件 PWM）
- ✅ Servo 2 **保留**
- ✅ 扬声器也独立
- 价格：¥5 模块 +几根杜邦线
