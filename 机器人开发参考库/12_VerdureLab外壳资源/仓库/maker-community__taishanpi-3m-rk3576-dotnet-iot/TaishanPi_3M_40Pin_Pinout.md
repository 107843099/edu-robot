# 泰山派 3M RK3576 40Pin 引脚速查

本文根据用户提供的《引脚定义说明书 泰山派3M - RK3576 V1.0.0》图片整理，用作本目录后续学习、查询和 .NET IoT 适配参考。

树莓派 BOARD / BCM / wiringPi 对照请看：[RaspberryPi_40Pin_Pinout.md](RaspberryPi_40Pin_Pinout.md)。

## 读表方式

泰山派 3M 的 40Pin 排针可以按树莓派物理 Pin 位置来理解，但软件侧不能直接套用树莓派 BCM 编号。建议同时关注：

- 物理 Pin：接线时使用，例如 Pin 3 / Pin 5 / Pin 19。
- 引脚功能复用：例如 I2C7、SPI1、PWM、UART。
- Rockchip GPIO 名称：例如 `GPIO2_D6`。
- Linux GPIO：按 `bank * 32 + port * 8 + index` 换算，A/B/C/D 分别是 0/1/2/3。
- gpiochip line：通常为同一个 bank 内的 line offset，例如 `GPIO2_D6` 是 `gpiochip2 line 30`。

## 40Pin 总表

| 物理 Pin | 引脚功能复用 | GPIO 编号 | Linux 全局 GPIO | gpiochip line | 备注 |
|---:|---|---|---:|---|---|
| 1 | 3V3_S3 | / | / | / | 3.3V 电源 |
| 2 | 5V0 | / | / | / | 5V 电源 |
| 3 | I2C7_SDA (M1) | GPIO3_A1 | 97 | gpiochip3 line 1 | 已验证为 `/dev/i2c-7` SDA |
| 4 | 5V0 | / | / | / | 5V 电源 |
| 5 | I2C7_SCL (M1) | GPIO3_A0 | 96 | gpiochip3 line 0 | 已验证为 `/dev/i2c-7` SCL |
| 6 | GND | / | / | / | 地 |
| 7 | GPIO | GPIO4_A6 | 134 | gpiochip4 line 6 | 普通 GPIO 候选 |
| 8 | UART4_TX (M0) | GPIO2_D0 | 88 | gpiochip2 line 24 | UART4 TX 复用 |
| 9 | GND | / | / | / | 地 |
| 10 | UART4_RX (M0) | GPIO2_D1 | 89 | gpiochip2 line 25 | UART4 RX 复用 |
| 11 | GPIO | GPIO4_A4 | 132 | gpiochip4 line 4 | 普通 GPIO 候选 |
| 12 | PWM1_CH1 (M0) | GPIO0_B5 | 13 | gpiochip0 line 13 | PWM 复用 |
| 13 | GPIO | GPIO2_C6 | 86 | gpiochip2 line 22 | 已验证作 SPI 屏 RESET |
| 14 | GND | / | / | / | 地 |
| 15 | GPIO | GPIO0_C7 | 23 | gpiochip0 line 23 | 普通 GPIO 候选 |
| 16 | GPIO | GPIO0_C6 | 22 | gpiochip0 line 22 | 普通 GPIO 候选 |
| 17 | 3V3_S0 | / | / | / | 3.3V 电源 |
| 18 | GPIO | GPIO3_A3 | 99 | gpiochip3 line 3 | 普通 GPIO 候选 |
| 19 | SPI1_MOSI (M1) | GPIO2_C2 | 82 | gpiochip2 line 18 | 已验证 SPI1 MOSI |
| 20 | GND | / | / | / | 地 |
| 21 | SPI1_MISO (M1) | GPIO2_C3 | 83 | gpiochip2 line 19 | 已验证 SPI1 MISO，屏幕通常可不接 |
| 22 | GPIO | GPIO2_D6 | 94 | gpiochip2 line 30 | 已验证作 SPI 屏 DC |
| 23 | SPI1_CLK (M1) | GPIO2_C5 | 85 | gpiochip2 line 21 | 已验证 SPI1 CLK |
| 24 | SPI1_CSN0 (M1) | GPIO2_C4 | 84 | gpiochip2 line 20 | 已验证 `/dev/spidev1.0` CS0 |
| 25 | GND | / | / | / | 地 |
| 26 | SPI1_CSN1 (M1) | GPIO2_C1 | 81 | gpiochip2 line 17 | SPI1 CS1 候选，当前项目未使用 |
| 27 | I2C8_SDA (M2) | GPIO2_B7 | 79 | gpiochip2 line 15 | I2C8 SDA 候选 |
| 28 | I2C8_SCL (M2) | GPIO2_B6 | 78 | gpiochip2 line 14 | I2C8 SCL 候选 |
| 29 | GPIO | GPIO2_C0 | 80 | gpiochip2 line 16 | 普通 GPIO 候选 |
| 30 | GND | / | / | / | 地 |
| 31 | GPIO | GPIO2_B0 | 72 | gpiochip2 line 8 | 普通 GPIO 候选 |
| 32 | PWM0_CH1 (M2) | GPIO2_C7 | 87 | gpiochip2 line 23 | PWM 复用 |
| 33 | PWM2_CH6 (M0) | GPIO4_A7 | 135 | gpiochip4 line 7 | PWM 复用 |
| 34 | GND | / | / | / | 地 |
| 35 | PWM1_CH5 (M0) | GPIO0_D2 | 26 | gpiochip0 line 26 | PWM 复用 |
| 36 | GPIO | GPIO2_D7 | 95 | gpiochip2 line 31 | 普通 GPIO 候选 |
| 37 | GPIO | GPIO2_A6 | 70 | gpiochip2 line 6 | 普通 GPIO 候选 |
| 38 | GPIO | GPIO3_A2 | 98 | gpiochip3 line 2 | 普通 GPIO 候选 |
| 39 | GND | / | / | / | 地 |
| 40 | GPIO | GPIO2_A7 | 71 | gpiochip2 line 7 | 普通 GPIO 候选 |

## 与树莓派 40Pin 的常用位置对照

| 常见用途 | 树莓派物理 Pin | 泰山派 3M 物理 Pin | 泰山派功能 | 本项目结论 |
|---|---:|---:|---|---|
| I2C SDA | 3 | 3 | I2C7_SDA (M1) | 使用 `/dev/i2c-7` |
| I2C SCL | 5 | 5 | I2C7_SCL (M1) | 使用 `/dev/i2c-7` |
| SPI MOSI | 19 | 19 | SPI1_MOSI (M1) | 使用 `/dev/spidev1.0` |
| SPI MISO | 21 | 21 | SPI1_MISO (M1) | 显示屏通常可不接 |
| SPI CLK | 23 | 23 | SPI1_CLK (M1) | 使用 `/dev/spidev1.0` |
| SPI CE0 | 24 | 24 | SPI1_CSN0 (M1) | 硬件 CS0 |
| 屏幕 RESET | 13 | 13 | GPIO2_C6 | `gpiochip2 line 22` |
| 屏幕 DC | 22 | 22 | GPIO2_D6 | `gpiochip2 line 30` |

## GPIO 换算示例

```text
GPIO2_C6 = 2 * 32 + 2 * 8 + 6 = gpio86 = gpiochip2 line 22
GPIO2_D6 = 2 * 32 + 3 * 8 + 6 = gpio94 = gpiochip2 line 30
GPIO3_A0 = 3 * 32 + 0 * 8 + 0 = gpio96 = gpiochip3 line 0
GPIO3_A1 = 3 * 32 + 0 * 8 + 1 = gpio97 = gpiochip3 line 1
```

## 使用注意

- 电源和 GND 引脚不能当 GPIO 使用。
- 标注为 SPI/I2C/UART/PWM 的引脚需要先确认当前 pinmux 状态。
- 当引脚被 SPI/I2C/UART/PWM 接管时，不应再用普通 GPIO 方式抢占。
- .NET `LibGpiodV2Driver(n)` 中的 `n` 是 gpiochip 编号，不是物理 Pin，也不是 Linux 全局 GPIO。
- 本项目已验证的显示屏路径使用 SPI1_M1；舵机路径使用 I2C7_M1。
