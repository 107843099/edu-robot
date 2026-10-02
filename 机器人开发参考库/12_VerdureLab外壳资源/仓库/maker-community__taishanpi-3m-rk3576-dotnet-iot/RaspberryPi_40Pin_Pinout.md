# 树莓派 40Pin 引脚对照表

本文根据用户提供的《树莓派 40Pin 引脚对照表》图片整理，用于和泰山派 3M RK3576 的 40Pin 表进行物理 Pin 对照。

## 读表方式

树莓派常见有三种编号体系：

- 物理引脚 BOARD 编码：排针上的实际位置，1 到 40。
- BCM 编码：Broadcom SoC GPIO 编号，很多 Python / .NET / libgpiod 示例会用它。
- wiringPi 编码：旧 wiringPi 库的编号体系，新项目通常不建议优先使用。

迁移到泰山派 3M 时，建议优先按物理 Pin 对齐接线，再把软件侧改成泰山派对应的 Linux 设备号或 gpiochip line。

## 40Pin 总表

| 物理 Pin | 功能名 | BCM 编码 | wiringPi 编码 | 备注 |
|---:|---|---:|---:|---|
| 1 | 3.3V | / | / | 3.3V 电源 |
| 2 | 5V | / | / | 5V 电源 |
| 3 | SDA.1 | 2 | 8 | I2C1 SDA |
| 4 | 5V | / | / | 5V 电源 |
| 5 | SCL.1 | 3 | 9 | I2C1 SCL |
| 6 | GND | / | / | 地 |
| 7 | GPIO.7 | 4 | 7 | 普通 GPIO |
| 8 | TXD | 14 | 15 | UART TX |
| 9 | GND | / | / | 地 |
| 10 | RXD | 15 | 16 | UART RX |
| 11 | GPIO.0 | 17 | 0 | 普通 GPIO |
| 12 | GPIO.1 | 18 | 1 | 普通 GPIO / PWM 候选 |
| 13 | GPIO.2 | 27 | 2 | 普通 GPIO |
| 14 | GND | / | / | 地 |
| 15 | GPIO.3 | 22 | 3 | 普通 GPIO |
| 16 | GPIO.4 | 23 | 4 | 普通 GPIO |
| 17 | 3.3V | / | / | 3.3V 电源 |
| 18 | GPIO.5 | 24 | 5 | 普通 GPIO |
| 19 | MOSI | 10 | 12 | SPI0 MOSI |
| 20 | GND | / | / | 地 |
| 21 | MISO | 9 | 13 | SPI0 MISO |
| 22 | GPIO.6 | 25 | 6 | 普通 GPIO，常作屏幕 DC |
| 23 | SCLK | 11 | 14 | SPI0 SCLK |
| 24 | CE0 | 8 | 10 | SPI0 CE0 |
| 25 | GND | / | / | 地 |
| 26 | CE1 | 7 | 11 | SPI0 CE1 |
| 27 | SDA.0 | 0 | 30 | ID EEPROM I2C SDA |
| 28 | SCL.0 | 1 | 31 | ID EEPROM I2C SCL |
| 29 | GPIO.21 | 5 | 21 | 普通 GPIO |
| 30 | GND | / | / | 地 |
| 31 | GPIO.22 | 6 | 22 | 普通 GPIO |
| 32 | GPIO.26 | 12 | 26 | 普通 GPIO / PWM 候选 |
| 33 | GPIO.23 | 13 | 23 | 普通 GPIO / PWM 候选 |
| 34 | GND | / | / | 地 |
| 35 | GPIO.24 | 19 | 24 | 普通 GPIO |
| 36 | GPIO.27 | 16 | 27 | 普通 GPIO |
| 37 | GPIO.25 | 26 | 25 | 普通 GPIO |
| 38 | GPIO.28 | 20 | 28 | 普通 GPIO |
| 39 | GND | / | / | 地 |
| 40 | GPIO.29 | 21 | 29 | 普通 GPIO |

## 与泰山派 3M 已验证功能对照

| 常见用途 | 树莓派物理 Pin | 树莓派 BCM | 树莓派功能 | 泰山派 3M 物理 Pin | 泰山派功能 | 本项目软件入口 |
|---|---:|---:|---|---:|---|---|
| I2C SDA | 3 | 2 | SDA.1 | 3 | I2C7_SDA (M1) | `/dev/i2c-7` |
| I2C SCL | 5 | 3 | SCL.1 | 5 | I2C7_SCL (M1) | `/dev/i2c-7` |
| SPI MOSI | 19 | 10 | MOSI | 19 | SPI1_MOSI (M1) | `/dev/spidev1.0` |
| SPI MISO | 21 | 9 | MISO | 21 | SPI1_MISO (M1) | `/dev/spidev1.0`，屏幕通常可不接 |
| SPI SCLK | 23 | 11 | SCLK | 23 | SPI1_CLK (M1) | `/dev/spidev1.0` |
| SPI CE0 | 24 | 8 | CE0 | 24 | SPI1_CSN0 (M1) | `/dev/spidev1.0` CS0 |
| SPI CE1 | 26 | 7 | CE1 | 26 | SPI1_CSN1 (M1) | 当前项目未使用 |
| 屏幕 DC 常用位 | 22 | 25 | GPIO.6 | 22 | GPIO2_D6 | `gpiochip2 line 30` |
| 屏幕 RESET 示例位 | 13 | 27 | GPIO.2 | 13 | GPIO2_C6 | `gpiochip2 line 22` |

## 迁移注意

- 物理 Pin 位置可以帮助接线，但树莓派 BCM 编码不能直接用于泰山派 3M。
- 树莓派 I2C 常见是 `/dev/i2c-1`；泰山派 3M 本项目实测物理 Pin 3/5 对应 `/dev/i2c-7`。
- 树莓派 SPI0 CE0 常见是 `/dev/spidev0.0`；泰山派 3M 本项目实测物理 Pin 19/21/23/24 对应 `/dev/spidev1.0`。
- 树莓派教程中的 `GPIO25` 对应物理 Pin 22；泰山派 3M 的物理 Pin 22 是 `GPIO2_D6`，在 .NET libgpiod 中使用 `gpiochip2 line 30`。
- 树莓派教程中的 `GPIO27` 对应物理 Pin 13；泰山派 3M 的物理 Pin 13 是 `GPIO2_C6`，在 .NET libgpiod 中使用 `gpiochip2 line 22`。
