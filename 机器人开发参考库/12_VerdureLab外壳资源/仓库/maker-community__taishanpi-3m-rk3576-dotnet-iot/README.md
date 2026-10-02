# TaishanPi 3M RK3576 .NET IoT 上手指南

这个目录整理了把 LCKFB 泰山派 3M RK3576 当作“类似树莓派的 .NET IoT 开发板”来使用时需要的资料、overlay、测试代码和实测结论。

它的目标不是完整替代官方手册，而是帮助已经熟悉树莓派 40Pin、SPI、I2C、GPIO 的开发者，快速理解泰山派 3M 的差异，并跑通两个常见场景：

- SPI 显示屏：已验证 2.4 寸 ST7789 正常显示
- I2C 舵机控制器：已验证物理 Pin 3 / Pin 5 上的 I2C7 可控制舵机运动
- USB 音频：已验证 USB audio CODEC 播放、录音、`mpg123` 播放和音量上限保护

## 当前验证结论

本次实测环境：

```text
Board: LCKFB TaishanPi 3M RK3576
OS: Debian 12
Kernel: Linux 6.1.99
Architecture: aarch64
.NET SDK: 10.0.203
.NET Runtime: 10.0.7
SPI: /dev/spidev1.0
I2C: /dev/i2c-7
```

已验证能力：

- SPI1_M1 overlay 可安全启用，得到 `/dev/spidev1.0`
- I2C7_M1 overlay 可安全启用，得到 `/dev/i2c-7`
- SPI1_M1 与 I2C7_M1 可以同时启用
- WiFi / SSH 在当前 overlay 组合下保持可用
- .NET 可通过 `System.Device.Spi`、`System.Device.I2c`、`System.Device.Gpio` 使用外设
- ST7789 屏幕测试通过
- ServoF030 风格 I2C 舵机控制测试通过
- udev 规则 + 用户组方案可让 lckfb 用户无需 sudo 访问 GPIO/SPI/I2C，同时兼容 PipeWire 用户会话音频
- USB audio CODEC 通过 PipeWire / ALSA 播放测试，`mpg123 1.31.2` 播放 MP3 测试通过
- PipeWire 默认播放与默认录音均已切到 USB audio CODEC，可用 `aplay -D default` / `arecord -D default` 走 USB 音频板
- 已配置用户级音量上限守护服务，实测 60% / 70% / 80% / 90% 上限均可播放，最终保留 90% 上限
- 录音测试建议将 USB Mic Capture 降至 60%，避免满幅削波；播放 WAV 优先用 `aplay -D default` 或 `aplay -D plughw:3,0`

当前推荐启动 overlay 配置：

```text
overlays=tspi-3m-spi1-m1-spidev.dtbo tspi-3m-i2c7-m1.dtbo
```

## 目录说明

| 路径 | 用途 |
|---|---|
| `TaishanPi_3M_DotNet_SPI_Display_Onboarding.md` | SPI 显示屏完整上手文档 |
| `TaishanPi_3M_DotNet_I2C_Servo_Onboarding.md` | I2C 舵机完整上手文档 |
| `TaishanPi_3M_DotNet_NonRoot_Permissions_Guide.md` | 无 sudo 运行：udev 规则 + 用户组配置，兼容 PipeWire 音频 |
| `TaishanPi_3M_USB_Audio_mpg123_Test_Guide.md` | USB 音频、mpg123、录放音和音量上限保护实测文档 |
| `TaishanPi_3M_40Pin_Pinout.md` | 根据引脚图整理的 40Pin Markdown 速查表 |
| `RaspberryPi_40Pin_Pinout.md` | 根据树莓派引脚图整理的 BOARD / BCM / wiringPi 对照表 |
| `v2_tspi-3m-spi1-m1-spidev.dts` | 已验证的 SPI1_M1 spidev overlay 源码 |
| `v2_tspi-3m-i2c7-m1.dts` | 已验证的 I2C7_M1 overlay 源码 |
| `St7789ScreenTest/` | 已验证通过的 ST7789 SPI 屏幕测试项目 |
| `ServoI2cTest/` | 已验证通过的 I2C 舵机测试项目 |
| `fri_may_01_2026_rockchip_gpio_driver_adaptation_guide.md` | 原始 AI 对话导出，内容很长，主要作为历史记录 |

新用户建议先读本文件，然后根据目标进入：

- SPI 屏幕：[TaishanPi_3M_DotNet_SPI_Display_Onboarding.md](TaishanPi_3M_DotNet_SPI_Display_Onboarding.md)
- I2C 舵机：[TaishanPi_3M_DotNet_I2C_Servo_Onboarding.md](TaishanPi_3M_DotNet_I2C_Servo_Onboarding.md)
- 无 sudo 权限配置：[TaishanPi_3M_DotNet_NonRoot_Permissions_Guide.md](TaishanPi_3M_DotNet_NonRoot_Permissions_Guide.md)
- USB 音频与 mpg123：[TaishanPi_3M_USB_Audio_mpg123_Test_Guide.md](TaishanPi_3M_USB_Audio_mpg123_Test_Guide.md)
- 40Pin 引脚：[TaishanPi_3M_40Pin_Pinout.md](TaishanPi_3M_40Pin_Pinout.md)
- 树莓派引脚：[RaspberryPi_40Pin_Pinout.md](RaspberryPi_40Pin_Pinout.md)

## 树莓派 5 与泰山派 3M 的核心差异

### 1. 物理 40Pin 像树莓派，但 Linux 设备号不同

泰山派 3M 的 40Pin 排针在使用习惯上接近树莓派，但不要假设 Linux 设备号完全一致。

例如：

| 功能 | 树莓派常见设备 | 泰山派 3M 实测设备 |
|---|---|---|
| SPI0 CE0 | `/dev/spidev0.0` | `/dev/spidev1.0` |
| 物理 Pin 3 / 5 I2C | `/dev/i2c-1` | `/dev/i2c-7` |
| GPIO 编号 | BCM 编号常用 | Rockchip gpiochip line / 全局 GPIO / pinctrl 共同判断 |

因此迁移树莓派代码时，重点不是只改引脚号，而是先确认：

- 对应控制器是否已经在设备树中启用
- Linux 下是否出现了 `/dev/spidevX.Y` 或 `/dev/i2c-X`
- GPIO 是否被 pinmux 配成普通 GPIO
- GPIO line 属于哪个 `gpiochip`

### 2. 树莓派 BCM 编号不能直接套用

树莓派教程常说 `GPIO10`、`GPIO11`、`GPIO8`、`GPIO25`。这些是 BCM 编号。

在泰山派 3M 上，更可靠的做法是使用物理 Pin + 泰山派功能名 + Linux 设备来对应。

例如 SPI 屏幕：

| 信号 | 树莓派 BCM | 树莓派物理 Pin | 泰山派物理 Pin | 泰山派功能 | .NET 使用方式 |
|---|---:|---:|---:|---|---|
| MOSI / DIN | GPIO10 | 19 | 19 | SPI1_MOSI_M1 | SPI 控制器 |
| MISO / DOUT | GPIO9 | 21 | 21 | SPI1_MISO_M1 | SPI 控制器，可不接 |
| CLK | GPIO11 | 23 | 23 | SPI1_CLK_M1 | SPI 控制器 |
| CE0 / CS | GPIO8 | 24 | 24 | SPI1_CSN0_M1 | `/dev/spidev1.0` CS0 |
| DC | GPIO25 | 22 | 22 | GPIO2_D6 | `gpiochip2 line 30` |
| RESET | GPIO27 | 13 | 13 | GPIO2_C6 | `gpiochip2 line 22` |

I2C 舵机控制器：

| 信号 | 树莓派物理 Pin | 泰山派物理 Pin | 泰山派功能 | Linux 设备 |
|---|---:|---:|---|---|
| SDA | 3 | 3 | I2C7_SDA_M1 / GPIO3_A1 | `/dev/i2c-7` |
| SCL | 5 | 5 | I2C7_SCL_M1 / GPIO3_A0 | `/dev/i2c-7` |

### 3. Rockchip GPIO 有三种常见编号视角

同一个引脚可能会同时出现三种编号方式：

| 视角 | 示例 | 用途 |
|---|---|---|
| Rockchip 名称 | `GPIO2_D6` | 看原理图、设备树、pinmux 时常用 |
| 全局 GPIO | `gpio94` | sysfs 老接口中常见 |
| gpiochip line | `gpiochip2 line 30` | libgpiod / .NET `LibGpiodV2Driver` 中常用 |

换算规则：

```text
全局 GPIO = bank * 32 + port * 8 + index
A = 0, B = 1, C = 2, D = 3
```

例子：

```text
GPIO2_C6 = 2 * 32 + 2 * 8 + 6 = gpio86 = gpiochip2 line 22
GPIO2_D6 = 2 * 32 + 3 * 8 + 6 = gpio94 = gpiochip2 line 30
GPIO3_A0 = 3 * 32 + 0 * 8 + 0 = gpio96
GPIO3_A1 = 3 * 32 + 0 * 8 + 1 = gpio97
```

在 .NET 中控制普通 GPIO 时，本次实测推荐：

```csharp
using var gpio = new GpioController(new LibGpiodV2Driver(2));
```

然后使用 chip 内 line 编号，例如：

```text
RESET: gpiochip2 line 22
DC:    gpiochip2 line 30
```

## 已验证的 40Pin 映射速查

### SPI1_M1 显示屏相关

| 物理 Pin | 树莓派习惯 | 泰山派功能 | Rockchip GPIO | 全局 GPIO | 备注 |
|---:|---|---|---|---:|---|
| 19 | MOSI / GPIO10 | SPI1_MOSI_M1 | GPIO2_C2 | gpio82 | 已验证 |
| 21 | MISO / GPIO9 | SPI1_MISO_M1 | GPIO2_C3 | gpio83 | 显示屏通常可不接 |
| 23 | SCLK / GPIO11 | SPI1_CLK_M1 | GPIO2_C5 | gpio85 | 已验证 |
| 24 | CE0 / GPIO8 | SPI1_CSN0_M1 | GPIO2_C4 | gpio84 | `/dev/spidev1.0` CS0 |
| 22 | DC / GPIO25 | 普通 GPIO | GPIO2_D6 | gpio94 | `gpiochip2 line 30` |
| 13 | RESET / GPIO27 | 普通 GPIO | GPIO2_C6 | gpio86 | `gpiochip2 line 22` |

已验证 SPI 参数：

```text
SPI bus: 1
SPI chip select: 0
SPI mode: Mode0
SPI clock: 24 MHz，可降到 6 MHz 调试
Device: /dev/spidev1.0
```

### I2C7_M1 舵机相关

| 物理 Pin | 树莓派习惯 | 泰山派功能 | Rockchip GPIO | 全局 GPIO | Linux 设备 |
|---:|---|---|---|---:|---|
| 3 | SDA / GPIO2 | I2C7_SDA_M1 | GPIO3_A1 | gpio97 | `/dev/i2c-7` |
| 5 | SCL / GPIO3 | I2C7_SCL_M1 | GPIO3_A0 | gpio96 | `/dev/i2c-7` |

舵机项目中使用的 Verdure 关节 ID 映射：

| 关节 ID | 控制地址 | 说明 |
|---:|---:|---|
| 2 | `0x01` | 上游保留/头部相关 |
| 4 | `0x02` | 左耳 |
| 6 | `0x03` | 左臂，本次实测通过 |
| 8 | `0x04` | 右耳 |
| 10 | `0x05` | 右臂 |
| 12 | `0x06` | 脖子 |

注意：`i2cdetect -y 7` 本次会看到 `0x43`，但 .NET 控制协议验证通过的是 `0x03`，不要把 `0x43` 当成当前测试程序的控制地址。

## 如何像使用树莓派一样使用泰山派 3M

### 第一步：先确认系统与工具

```bash
cat /proc/device-tree/model
uname -a
dotnet --info
```

推荐安装：

```bash
sudo apt-get update
sudo apt-get install -y dotnet-sdk-10.0 i2c-tools device-tree-compiler
sudo apt-get install -y -t bookworm-backports gpiod
```

### 第二步：启用需要的 overlay

SPI 显示屏需要：

```text
tspi-3m-spi1-m1-spidev.dtbo
```

I2C 舵机需要：

```text
tspi-3m-i2c7-m1.dtbo
```

从 Windows 主机复制 DTS 到开发板：

```powershell
ssh lckfb@192.168.31.123 "mkdir -p ~/tspi-3m-overlay"
scp .\v2_tspi-3m-spi1-m1-spidev.dts lckfb@192.168.31.123:~/tspi-3m-overlay/tspi-3m-spi1-m1-spidev.dts
scp .\v2_tspi-3m-i2c7-m1.dts lckfb@192.168.31.123:~/tspi-3m-overlay/tspi-3m-i2c7-m1.dts
```

在开发板上编译并安装 overlay：

```bash
cd ~/tspi-3m-overlay
sudo apt-get install -y device-tree-compiler
dtc -@ -I dts -O dtb -o tspi-3m-spi1-m1-spidev.dtbo tspi-3m-spi1-m1-spidev.dts
dtc -@ -I dts -O dtb -o tspi-3m-i2c7-m1.dtbo tspi-3m-i2c7-m1.dts
sudo cp tspi-3m-spi1-m1-spidev.dtbo tspi-3m-i2c7-m1.dtbo /boot/overlays/
sudo cp /boot/ubootEnv.txt /boot/ubootEnv.txt.bak-taishanpi-iot
overlays=$(grep '^[[:space:]]*overlays=' /boot/ubootEnv.txt | tail -n 1 | cut -d= -f2-)
for item in tspi-3m-spi1-m1-spidev.dtbo tspi-3m-i2c7-m1.dtbo; do
	case " $overlays " in
		*" $item "*) ;;
		*) overlays="$overlays $item" ;;
	esac
done
overlays=$(echo "$overlays" | xargs)
if grep -q '^[[:space:]]*overlays=' /boot/ubootEnv.txt; then
	sudo sed -i "s#^[[:space:]]*overlays=.*#overlays=$overlays#" /boot/ubootEnv.txt
else
	printf '\noverlays=%s\n' "$overlays" | sudo tee -a /boot/ubootEnv.txt >/dev/null
fi
sync
grep -n '^[[:space:]]*overlays=' /boot/ubootEnv.txt
ls -lh /boot/overlays/tspi-3m-spi1-m1-spidev.dtbo /boot/overlays/tspi-3m-i2c7-m1.dtbo
sudo reboot
```

最终 `/boot/ubootEnv.txt` 的 `overlays=` 至少应包含这两个条目；如果你的系统原本还有其他 overlay，应一并保留：

```text
overlays=tspi-3m-spi1-m1-spidev.dtbo tspi-3m-i2c7-m1.dtbo
```

重启后验证：

```bash
ls -l /dev/spidev*
ls -l /dev/i2c-7
```

期望看到：

```text
/dev/spidev1.0
/dev/i2c-7
```

### 第三步：检查 pinmux

```bash
sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null || true
sudo grep -E 'pin (82|83|84|85|86|94|96|97) ' /sys/kernel/debug/pinctrl/pinctrl-rockchip-pinctrl/pinmux-pins
```

期望含义：

- pin 82/83/84/85 被 SPI1 接管
- pin 86/94 保持普通 GPIO，可作 RESET/DC
- pin 96/97 被 I2C7 接管

### 系统级自检命令

在运行具体 .NET 测试项目前，建议先保留并执行下面这组命令。它们用于确认开发板型号、内核、.NET 环境、overlay、生效后的设备节点和 pinmux 状态。

```bash
cat /proc/device-tree/model
uname -a
dotnet --info
grep '^overlays=' /boot/ubootEnv.txt
ls -l /dev/spidev* 2>/dev/null || echo "no /dev/spidev*"
ls -l /dev/i2c-7
gpioinfo gpiochip2 | grep -E 'line +(22|30):'
sudo i2cdetect -y 7
sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null || true
sudo grep -E 'pin (82|83|84|85|86|94|96|97) ' /sys/kernel/debug/pinctrl/pinctrl-rockchip-pinctrl/pinmux-pins
```

期望重点：

- `model` 显示 LCKFB TaishanPi 3M RK3576
- `overlays=` 同时包含 SPI1_M1 和 I2C7_M1 overlay
- `/dev/spidev1.0` 和 `/dev/i2c-7` 存在
- `gpiochip2 line 22`、`line 30` 可作为 RESET/DC 使用
- `i2cdetect -y 7` 能看到舵机控制器相关响应

### 第四步：按目标运行测试

SPI 显示屏：

```bash
cd ~/St7789ScreenTest
dotnet build
sudo dotnet run --no-build -- --clock 6000000 --delay 1500
```

I2C 舵机：

```bash
cd ~/ServoI2cTest
dotnet build
sudo dotnet run --no-build -- --bus 7 --joint 6 --enable --angle 90 --sweep --delta 20 --cycles 1 --delay 400 --retries 2
```

## 实测命令速查

这一节保留从 Windows 主机部署到泰山派 3M，并在开发板上完成验收的最小命令。详细解释仍放在两份 onboarding 文档中。

### 主机侧可选构建检查

这一步用于确认项目源码本身能编译。正式在开发板上运行前，仍建议在开发板侧重新 `dotnet build`。

```powershell
dotnet build .\St7789ScreenTest\St7789ScreenTest.csproj
dotnet build .\ServoI2cTest\ServoI2cTest.csproj
```

### 部署 SPI 屏幕测试项目

```powershell
ssh lckfb@192.168.31.123 "rm -rf ~/St7789ScreenTest"
scp -r .\St7789ScreenTest lckfb@192.168.31.123:~/St7789ScreenTest
```

开发板侧运行：

```bash
cd ~/St7789ScreenTest
dotnet build
sudo dotnet run --no-build -- --clock 6000000 --delay 1500
```

### 部署 I2C 舵机测试项目

```powershell
ssh lckfb@192.168.31.123 "rm -rf ~/ServoI2cTest"
scp -r .\ServoI2cTest lckfb@192.168.31.123:~/ServoI2cTest
```

开发板侧构建和运行：

```bash
cd ~/ServoI2cTest
dotnet build
sudo dotnet run --no-build -- --bus 7 --joint 6 --enable --angle 90 --sweep --delta 20 --cycles 1 --delay 400 --retries 2
```

期望看到类似输出：

```text
enable=1 ok
angle=90.0 ok
cycle 1/1: low=70.0, high=110.0, center=90.0
read ok, reported=91.05
```

如果命令成功但硬件无反应，优先检查电源、GND 是否共地、I2C 是否确认为 `/dev/i2c-7`、屏幕 DIN 是否接到物理 Pin 19。

## 最短上手路径

如果你只是想最快确认这套资料是否可用：

1. 接 SPI 屏幕到 Pin 19/23/24/22/13 和电源/GND
2. 接 I2C 舵机控制板到 Pin 3/5 和电源/GND
3. 安装 .NET、`gpiod`、`i2c-tools`、`device-tree-compiler`
4. 编译并安装两个 overlay
5. `/boot/ubootEnv.txt` 写入：

```text
overlays=tspi-3m-spi1-m1-spidev.dtbo tspi-3m-i2c7-m1.dtbo
```

6. 重启后确认：

```bash
ls -l /dev/spidev1.0 /dev/i2c-7
```

7. 跑屏幕测试和舵机测试

如果两者都通过，说明这块泰山派 3M 已经可以按“树莓派式 40Pin 外设开发”的方式继续做 .NET IoT 项目。

## 不要踩的坑

### 不要把树莓派设备号原样照搬

树莓派常用 `/dev/i2c-1` 和 `/dev/spidev0.0`。本次泰山派 3M 实测是：

```text
I2C: /dev/i2c-7
SPI: /dev/spidev1.0
```

### 不要把屏幕 DIN 接到 Pin 21

SPI 屏幕 DIN / SDA / SDI 应接 MOSI，也就是物理 Pin 19。Pin 21 是 MISO。

### 不要把 SPI CS0 当普通 GPIO 抢占

物理 Pin 24 已由 SPI 控制器作为 CS0 管理。应用层测试 ST7789 时，`cs-line` 使用 `-1`，不要再用 GPIO 抢 Pin 24。

### 不要覆盖已有 overlay 列表

如果原来已经有 SPI overlay，再启用 I2C 时不要把它覆盖掉。应写成同一行多个 overlay：

```text
overlays=tspi-3m-spi1-m1-spidev.dtbo tspi-3m-i2c7-m1.dtbo
```

### 不要随意动 WiFi / 4G 相关 GPIO

已知应避开的 GPIO 包括：

| GPIO | 用途 |
|---:|---|
| gpio25 | WiFi VBAT |
| gpio54 | WiFi power / reset |
| gpio55 | BT reset |
| gpio60 | BT wake |
| gpio61 | 4G VBAT / PCIe/SATA 3.3V |
| gpio73 | 4G reset / PCIe reset |
| gpio77 | USB2 host power enable |
| gpio92 | BT UART RTS |
| gpio151 | 4G power |

### 不要反复递归复制到同名目录

如果执行多次：

```powershell
scp -r .\ServoI2cTest lckfb@192.168.31.123:~/ServoI2cTest
```

可能生成：

```text
~/ServoI2cTest/ServoI2cTest/Program.cs
```

这会导致 .NET 编译时重复定义。修复：

```bash
ssh lckfb@192.168.31.123 "rm -rf ~/ServoI2cTest"
scp -r .\ServoI2cTest lckfb@192.168.31.123:~/ServoI2cTest
```

## 原始对话文件如何处理

`fri_may_01_2026_rockchip_gpio_driver_adaptation_guide.md` 是原始 AI 对话导出，包含很多探索过程、错误路径和中间结论。它不适合作为新人入口。

不要直接照抄原始对话里的早期命令。里面包含一些探索阶段的写法，例如旧的 SPI 设备号、`LibGpiodDriver(0)` 示例、覆盖式修改 `overlays=` 等；本 README 和两份 onboarding 文档中的最终命令才是建议使用的版本。

本 README 已经保留并整理了其中重要内容：

- Rockchip GPIO 编号规则
- 树莓派 40Pin 到泰山派 3M 的实测映射
- SPI/I2C overlay 思路
- .NET IoT 使用方式
- 已验证命令和常见坑

建议后续把原始导出视为历史归档，新用户只看本 README 和两份 onboarding 文档。

## 参考文档

- [SPI 显示屏上手指南](TaishanPi_3M_DotNet_SPI_Display_Onboarding.md)
- [I2C 舵机上手指南](TaishanPi_3M_DotNet_I2C_Servo_Onboarding.md)
- [40Pin 引脚速查表](TaishanPi_3M_40Pin_Pinout.md)
- [树莓派 40Pin 引脚对照表](RaspberryPi_40Pin_Pinout.md)
