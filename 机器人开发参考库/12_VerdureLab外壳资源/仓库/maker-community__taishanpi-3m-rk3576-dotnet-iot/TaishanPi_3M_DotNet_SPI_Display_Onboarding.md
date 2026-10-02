# 泰山派 3M RK3576 使用 .NET 控制 SPI 显示屏上手指南

本文档用于把一块新的 LCKFB 泰山派 3M RK3576 开发板配置到可以使用 .NET 控制 SPI 显示屏的状态。内容基于本次实测记录整理，最终已经验证 2.4 寸 ST7789 SPI 屏幕可以正常显示红、绿、蓝、白、黑、彩条、渐变、棋盘格。

## 1. 已验证的目标状态

最终目标是让板子具备以下能力：

- 系统中出现 `/dev/spidev1.0`
- SPI1_M1 的物理排针可用于 SPI 显示屏
- `.NET 10` 可以打开 `/dev/spidev1.0`
- `.NET` 可以通过 `LibGpiodV2Driver` 控制 DC / RESET GPIO
- 2.4 寸 ST7789 屏幕可以通过 `St7789ScreenTest` 正常刷屏

本次验证通过的板子信息：

```text
Board: LCKFB TaishanPi 3M RK3576
OS: Debian 12
Kernel: Linux 6.1.99
Architecture: aarch64
.NET SDK: 10.0.203
.NET Runtime: 10.0.7
GPIO library: libgpiod3 2.1.3-1~bpo12+1
SPI device: /dev/spidev1.0
```

## 2. 安全提醒

这块板子上 WiFi、蓝牙、4G、USB、Type-C 等功能已经占用了一些 GPIO。启用 SPI 或测试 GPIO 时不要随意改动这些引脚，否则可能导致 WiFi / 4G 掉线，SSH 无法连接。

本次没有触碰并需要避开的关键引脚包括：

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

本次启用的 SPI1_M1 使用：

| Rockchip GPIO | 全局 GPIO | 用途 |
|---|---:|---|
| GPIO2_C2 | gpio82 | SPI1 MOSI |
| GPIO2_C3 | gpio83 | SPI1 MISO |
| GPIO2_C4 | gpio84 | SPI1 CS0 |
| GPIO2_C5 | gpio85 | SPI1 CLK |

这些引脚与 WiFi / 4G 当前占用没有冲突。

## 3. 40Pin 排针接线关系

### 3.1 SPI 显示屏核心接线

树莓派风格 SPI 屏幕迁移到泰山派 3M 时，按物理排针接线最直观。

| 显示屏信号 | 树莓派 BCM | 树莓派物理 Pin | 泰山派物理 Pin | 泰山派功能 | .NET / gpiod 编号 |
|---|---:|---:|---:|---|---|
| VCC | - | 1 / 17 | 1 / 17 | 3.3V 电源 | 不适用 |
| GND | - | 6 / 9 / 14 / 20 / 25 | 6 / 9 / 14 / 20 / 25 / 30 / 34 / 39 | GND | 不适用 |
| DIN / SDA / MOSI | GPIO10 | 19 | 19 | SPI1_MOSI_M1 | SPI 控制器 |
| DOUT / MISO | GPIO9 | 21 | 21 | SPI1_MISO_M1 | SPI 控制器，可不接 |
| SCLK / CLK | GPIO11 | 23 | 23 | SPI1_CLK_M1 | SPI 控制器 |
| CS / CE0 | GPIO8 | 24 | 24 | SPI1_CSN0_M1 | `/dev/spidev1.0` CS0 |
| DC | GPIO25 | 22 | 22 | GPIO2_D6 | gpiochip2 line 30 / sysfs gpio94 |
| RESET / RST | GPIO27 | 13 | 13 | GPIO2_C6 | gpiochip2 line 22 / sysfs gpio86 |
| BL / LED | 常见 GPIO18 | 12 或其他 | 视屏幕接线而定 | GPIO 或 PWM | 按实际接线配置 |

注意：屏幕的数据输入必须接 MOSI，即物理 Pin 19。不要把屏幕 DIN 接到 Pin 21，Pin 21 是 MISO。

### 3.2 已验证的 2.4 寸 ST7789 默认参数

```text
SPI bus: 1
SPI chip select: 0
SPI mode: Mode0
SPI clock: 24 MHz，可降到 6 MHz 调试
DC: gpiochip2 line 30，物理 Pin 22
RESET: gpiochip2 line 22，物理 Pin 13
CS: 由 SPI 控制器控制，程序里 cs-line = -1
```

## 4. 新板环境安装

### 4.1 登录板子

示例：

```bash
ssh lckfb@192.168.31.123
```

本次测试板默认账号密码均为：

```text
用户名: lckfb
密码: lckfb
```

### 4.2 检查系统信息

```bash
uname -a
cat /proc/device-tree/model
ip addr
```

期望类似：

```text
LCKFB TaishanPi 3M RK3576 Board
Linux 6.1.99
aarch64
```

### 4.3 安装 .NET SDK

本次通过 `history` 查到板子实际使用的是 Microsoft Debian 12 软件源安装路线。新板如果没有 .NET，可以按下面步骤安装 `.NET SDK 10`：

```bash
wget https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install -y dotnet-sdk-10.0
```

本次历史记录里对应的关键命令是：

```text
wget https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb
sudo apt-get update && sudo apt-get install -y dotnet-sdk-10.0
dotnet --info
```

安装完成后检查：

```bash
dotnet --info
```

至少需要看到：

```text
.NET SDK 10.x
.NET runtime 10.x
```

### 4.4 安装 GPIO 命令行工具

板子默认可能只有 `libgpiod3` 运行库，没有 `gpioinfo` / `gpioset` / `gpioget` 命令。建议安装 `gpiod` 工具包，方便排查 GPIO。

```bash
sudo apt-get update
sudo apt-get install -y -t bookworm-backports gpiod
```

检查：

```bash
for c in gpiodetect gpioinfo gpioget gpioset gpiofind; do
    printf '%-10s ' "$c"
    command -v "$c" || echo missing
done
```

## 5. 启用 SPI1_M1 设备树 overlay

### 5.1 为什么需要 overlay

默认系统中不一定启用排针上的 SPI1_M1。如果没有 `/dev/spidev1.0`，.NET 的 `System.Device.Spi` 就无法打开 SPI 设备。

检查：

```bash
ls -l /dev/spidev*
```

如果没有输出，需要启用 SPI overlay。

### 5.2 已验证的 overlay 源码

工作区内已保留本次验证使用的 overlay 源文件：

- `v2_tspi-3m-spi1-m1-spidev.dts`

当前也已经复制到开发板家目录，路径为：

```text
/home/lckfb/tspi-3m-spi1-m1-overlay/tspi-3m-spi1-m1-spidev.dts
```

核心要点是启用 `spi@2ad00000` 对应的 `&spi1`，并明确使用 SPI1_M1 pinctrl：

```dts
/dts-v1/;
/plugin/;

&spi1 {
    status = "okay";
    #address-cells = <1>;
    #size-cells = <0>;

    pinctrl-names = "default";
    pinctrl-0 = <&spi1m1_csn0 &spi1m1_pins>;

    num-cs = <1>;
    max-freq = <50000000>;

    spidev@0 {
        compatible = "rohm,dh2228fv";
        status = "okay";
        reg = <0>;
        spi-max-frequency = <50000000>;
    };
};
```

其中：

```text
spi1m1_csn0 -> 物理 Pin 24 / GPIO2_C4 / CS0
spi1m1_pins -> 物理 Pin 19 / 21 / 23，对应 MOSI / MISO / CLK
```

### 5.3 从本地复制 DTS 到板子家目录

不要把最终版本只放在 `/tmp`，因为 `/tmp` 适合临时验证，不适合后续交接和复现。建议固定放在用户家目录下：

```powershell
ssh lckfb@192.168.31.123 "mkdir -p ~/tspi-3m-spi1-m1-overlay"
scp .\v2_tspi-3m-spi1-m1-spidev.dts lckfb@192.168.31.123:~/tspi-3m-spi1-m1-overlay/tspi-3m-spi1-m1-spidev.dts
```

在板子上确认文件存在：

```bash
ls -lh ~/tspi-3m-spi1-m1-overlay/tspi-3m-spi1-m1-spidev.dts
```

本次实测复制后的文件位置和大小：

```text
/home/lckfb/tspi-3m-spi1-m1-overlay/tspi-3m-spi1-m1-spidev.dts
389 bytes
```

### 5.4 在板子家目录编译 overlay

在开发板上执行：

```bash
cd ~/tspi-3m-spi1-m1-overlay
sudo apt-get install -y device-tree-compiler
dtc -@ -I dts -O dtb -o tspi-3m-spi1-m1-spidev.dtbo tspi-3m-spi1-m1-spidev.dts
ls -lh tspi-3m-spi1-m1-spidev.dtbo
```

本次实测 `dtc` 已安装在 `/usr/bin/dtc`，编译出的文件为：

```text
/home/lckfb/tspi-3m-spi1-m1-overlay/tspi-3m-spi1-m1-spidev.dtbo
647 bytes
```

### 5.5 安装 overlay 并配置启动项

```bash
cd ~/tspi-3m-spi1-m1-overlay
sudo cp tspi-3m-spi1-m1-spidev.dtbo /boot/overlays/
sudo cp /boot/ubootEnv.txt /boot/ubootEnv.txt.bak-spi1m1-$(date +%Y%m%d-%H%M%S)
```

编辑 `/boot/ubootEnv.txt`，确保有如下配置：

```text
overlays=tspi-3m-spi1-m1-spidev.dtbo
```

可以用命令直接写入或替换这一行：

```bash
if grep -q '^[[:space:]]*overlays=' /boot/ubootEnv.txt; then
    sudo sed -i 's#^[[:space:]]*overlays=.*#overlays=tspi-3m-spi1-m1-spidev.dtbo#' /boot/ubootEnv.txt
else
    printf '\noverlays=tspi-3m-spi1-m1-spidev.dtbo\n' | sudo tee -a /boot/ubootEnv.txt >/dev/null
fi
sync
grep -n '^[[:space:]]*overlays=' /boot/ubootEnv.txt
ls -lh /boot/overlays/tspi-3m-spi1-m1-spidev.dtbo
```

本次实测安装后的关键结果：

```text
/boot/ubootEnv.txt backup: /boot/ubootEnv.txt.bak-spi1m1-20260502-103237
/boot/ubootEnv.txt line 67: overlays=tspi-3m-spi1-m1-spidev.dtbo
/boot/overlays/tspi-3m-spi1-m1-spidev.dtbo: 647 bytes
```

本次还清理了一个 2026-04-25 生成的旧失败版本：

```text
/boot/overlays/tspi-3m-spi1.dtbo
```

该文件没有被 `/boot/ubootEnv.txt` 引用，且日期和系统原始 overlay 批次不同，已移到：

```text
/boot/overlays/disabled-by-copilot/tspi-3m-spi1.dtbo.failed-20260425
```

当前 `/boot/overlays` 顶层只保留正在使用的 SPI1_M1 spidev overlay。不要删除 `minipcie` / `dsi` 相关 overlay，它们不是 SPI 屏幕配置。

然后重启：

```bash
sudo reboot
```

如果当前系统已经通过该 overlay 启动，重新复制和安装同名 `.dtbo` 后不需要立刻重启才能继续当前验证；但新板首次启用 overlay 必须重启。

### 5.6 重启后验证 SPI

```bash
ls -l /dev/spidev*
```

期望：

```text
/dev/spidev1.0
```

查看设备树状态：

```bash
spi=/proc/device-tree/spi@2ad00000
for p in status pinctrl-names compatible; do
    printf "%s=" "$p"
    [ -f "$spi/$p" ] && tr '\0' ' ' < "$spi/$p"
    printf "\n"
done
```

期望：

```text
status=okay
pinctrl-names=default
compatible=rockchip,rk3066-spi
```

查看 pinmux：

```bash
sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null || true
sudo grep -E 'pin (82|83|84|85|86|94) ' /sys/kernel/debug/pinctrl/pinctrl-rockchip-pinctrl/pinmux-pins
```

期望关键结果：

```text
pin 82 (gpio2-18): 2ad00000.spi function spi1 group spi1m1-pins
pin 83 (gpio2-19): 2ad00000.spi function spi1 group spi1m1-pins
pin 84 (gpio2-20): 2ad00000.spi function spi1 group spi1m1-csn0
pin 85 (gpio2-21): 2ad00000.spi function spi1 group spi1m1-pins
pin 86 (gpio2-22): (MUX UNCLAIMED) ...
pin 94 (gpio2-30): (MUX UNCLAIMED) ...
```

这里的含义是：

- Pin 19 / 21 / 23 / 24 已被 SPI 控制器接管
- Pin 13 / 22 仍是普通 GPIO，可以给 RESET / DC 使用

## 6. 验证 GPIO 控制

### 6.1 使用 gpiod 工具验证

先查看 line 状态：

```bash
sudo gpioinfo -c gpiochip2 22 30
```

测试 RESET：

```bash
sudo timeout 5s gpioset --banner -c gpiochip2 22=0
sudo timeout 5s gpioset --banner -c gpiochip2 22=1
```

测试 DC：

```bash
sudo timeout 5s gpioset --banner -c gpiochip2 30=0
sudo timeout 5s gpioset --banner -c gpiochip2 30=1
```

### 6.2 使用 sysfs 验证

这套方式较旧，但排查时很直观。注意：如果使用 sysfs export 了 GPIO，后续 .NET / gpiod 可能会报 `Device or resource busy`，测试完要 unexport。

```bash
for n in 86 94; do
    echo "== gpio$n =="
    if [ ! -d /sys/class/gpio/gpio$n ]; then
        echo $n | sudo tee /sys/class/gpio/export >/dev/null
    fi
    echo out | sudo tee /sys/class/gpio/gpio$n/direction >/dev/null
    echo 0 | sudo tee /sys/class/gpio/gpio$n/value >/dev/null
    printf 'wrote 0 read='
    cat /sys/class/gpio/gpio$n/value
    echo 1 | sudo tee /sys/class/gpio/gpio$n/value >/dev/null
    printf 'wrote 1 read='
    cat /sys/class/gpio/gpio$n/value
done
```

释放：

```bash
for n in 86 94; do
    [ -d /sys/class/gpio/gpio$n ] && echo $n | sudo tee /sys/class/gpio/unexport >/dev/null || true
done
```

## 7. .NET 测试项目

### 7.1 ST7789 2.4 寸验证项目

工作区内已准备好可运行项目：

- `St7789ScreenTest`

本项目基于上游 `DualDisplayExample` 的 2.4 寸显示路径整理，只保留单屏测试，避免双屏逻辑干扰。

本地构建：

```powershell
dotnet build .\St7789ScreenTest\St7789ScreenTest.csproj
```

复制完整项目到板子家目录：

```powershell
scp -r .\St7789ScreenTest lckfb@192.168.31.123:~/St7789ScreenTest
```

如果只想复制源码，建议排除 `bin` / `obj` 后在板子上重新构建；如果直接复制整个目录，则本次实测也可以直接运行已经构建好的 `bin/Debug/net10.0/St7789ScreenTest.dll`。

板子上重新构建：

```bash
cd ~/St7789ScreenTest
dotnet restore
dotnet build
```

运行前建议释放可能被 sysfs 或 `gpioset` 占用的 RESET / DC GPIO：

```bash
sudo pkill -f gpioset || true
for n in 86 94; do
    [ -d /sys/class/gpio/gpio$n ] && echo $n | sudo tee /sys/class/gpio/unexport >/dev/null || true
done
```

板子上运行：

```bash
cd ~/St7789ScreenTest
sudo dotnet bin/Debug/net10.0/St7789ScreenTest.dll \
  --spi-bus 1 \
  --spi-cs 0 \
  --clock 24000000 \
  --gpiochip 2 \
  --dc 30 \
  --reset 22 \
  --cs-line -1 \
  --loops 1 \
  --delay 1000
```

低速观察版：

```bash
cd ~/St7789ScreenTest
sudo dotnet bin/Debug/net10.0/St7789ScreenTest.dll \
  --spi-bus 1 \
  --spi-cs 0 \
  --clock 6000000 \
  --gpiochip 2 \
  --dc 30 \
  --reset 22 \
  --cs-line -1 \
  --loops 1 \
  --delay 1500
```

运行后应看到：

```text
ST7789 2.4 inch screen test for TaishanPi 3M / RK3576
SPI: bus=1, chip-select=0, clock=24,000,000 Hz, mode=0
GPIO: gpiochip=2, dc-line=30, reset-line=22, cs-line=-1
Display initialized. Starting patterns...
Pattern: Red
Pattern: Green
Pattern: Blue
Pattern: White
Pattern: Black
Pattern: vertical color bars
Pattern: gradient
Pattern: checkerboard
Screen test completed.
```

屏幕上应依次显示：红、绿、蓝、白、黑、彩条、渐变、棋盘格。

本次实测也运行过源码方式：

```bash
cd ~/St7789ScreenTest
sudo dotnet run -- \
    --spi-bus 1 \
    --spi-cs 0 \
    --clock 24000000 \
    --gpiochip 2 \
    --dc 30 \
    --reset 22 \
    --cs-line -1 \
    --loops 1 \
    --delay 1000
```

### 7.2 项目依赖

`.csproj` 中关键依赖：

```xml
<PackageReference Include="System.Device.Gpio" Version="4.1.0" />
```

由于 `LibGpiodV2Driver` 在 .NET IoT 中会触发实验性 API 警告，需要关闭该诊断：

```xml
<NoWarn>$(NoWarn);SDGPIO0001</NoWarn>
```

### 7.3 .NET 代码关键点

GPIO 控制器必须使用 libgpiod v2：

```csharp
using var gpio = new GpioController(new LibGpiodV2Driver(2));
```

SPI 设置：

```csharp
var spiSettings = new SpiConnectionSettings(1, 0)
{
    ClockFrequency = 24_000_000,
    Mode = SpiMode.Mode0
};
```

DC / RESET：

```csharp
int dcLine = 30;     // gpiochip2 line 30, physical pin 22
int resetLine = 22;  // gpiochip2 line 22, physical pin 13
```

硬件 CS0 已由 SPI 控制器管理，所以应用层不要再抢 Pin 24 当 GPIO：

```text
cs-line = -1
```

## 8. 常见问题排查

### 8.1 没有 `/dev/spidev1.0`

说明 SPI overlay 没有启用或没有生效。

检查：

```bash
grep -n '^[[:space:]]*overlays=' /boot/ubootEnv.txt
ls -l /boot/overlays/tspi-3m-spi1-m1-spidev.dtbo
ls -l /dev/spidev*
```

修复方向：

- 确认 `/boot/overlays/tspi-3m-spi1-m1-spidev.dtbo` 存在
- 确认 `/boot/ubootEnv.txt` 中 `overlays=` 指向该 overlay
- 重启板子

### 8.2 .NET 报 `Device or resource busy`

常见原因是之前用 sysfs 或 gpioset 占用了 GPIO。

释放 sysfs：

```bash
for n in 86 94; do
    [ -d /sys/class/gpio/gpio$n ] && echo $n | sudo tee /sys/class/gpio/unexport >/dev/null || true
done
```

停止遗留 gpioset：

```bash
sudo pkill -f gpioset || true
```

### 8.3 屏幕背光亮但无画面

先确认 2.4 寸 ST7789 已知好屏是否能显示。如果 ST7789 能显示，说明板子的 SPI / GPIO / .NET 链路是通的。

继续排查：

- 屏幕 DIN 是否接 Pin 19 MOSI
- 屏幕 CLK 是否接 Pin 23
- 屏幕 CS 是否接 Pin 24，而不是 Pin 26
- DC 是否接 Pin 22
- RESET 是否接 Pin 13
- 屏幕控制器型号是否匹配代码，例如 ST7789 / GC9D01 / GC9A01 不可混用初始化序列

### 8.4 RESET 拉低没有看到背光变化

这是正常现象。多数 SPI 屏幕的背光和 LCD 控制器是分开的，RESET 通常只复位 LCD 控制器，不一定关闭背光。

如果要确认 RESET 是否真的到达屏幕模块，应使用万用表测屏幕模块 RST 焊盘：

```bash
sudo timeout 20s gpioset --banner -c gpiochip2 22=0
sudo timeout 20s gpioset --banner -c gpiochip2 22=1
```

低电平时应接近 0V，高电平时应接近 3.3V。

### 8.5 SPI 频率问题

默认使用 24 MHz。如果杜邦线较长或屏幕不稳定，可以降到 6 MHz：

```bash
sudo dotnet bin/Debug/net10.0/St7789ScreenTest.dll --clock 6000000 --delay 1500
```

### 8.6 权限问题

`/dev/spidev1.0` 和 `/dev/gpiochip*` 默认通常是 root-only，因此测试命令建议加 `sudo`。

如果不加 sudo，可能出现：

```text
Permission denied
```

## 9. 新人最短操作流程

如果板子已经配置好 overlay 和 .NET，新人只需要：

1. 接线：

```text
VCC   -> 3.3V
GND   -> GND
DIN   -> Pin 19
CLK   -> Pin 23
CS    -> Pin 24
DC    -> Pin 22
RESET -> Pin 13
BL    -> 按屏幕模块要求接 3.3V 或 GPIO/PWM
```

2. 登录板子：

```bash
ssh lckfb@192.168.31.123
```

3. 确认 SPI：

```bash
ls -l /dev/spidev1.0
```

4. 运行测试：

```bash
cd ~/St7789ScreenTest
sudo dotnet bin/Debug/net10.0/St7789ScreenTest.dll --clock 6000000 --delay 1500
```

5. 看到红、绿、蓝、白、黑、彩条、渐变、棋盘格，即说明链路可用。

## 10. 本次验证结论

本次最终确认：

- SPI1_M1 overlay 可以安全启用，不影响 WiFi / 4G SSH 连接
- `/dev/spidev1.0` 可以被 .NET 打开并传输
- `LibGpiodV2Driver(2)` 可以控制 `gpiochip2 line 22/30`
- 2.4 寸 ST7789 屏幕可以正常显示测试图案
- 如果 GC9D01 屏幕在树莓派和泰山派上都不能显示，应优先怀疑屏幕本体、控制器型号或初始化序列，而不是泰山派 SPI/.NET 链路

