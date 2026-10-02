# 泰山派 3M RK3576 使用 .NET 控制 I2C 舵机上手指南

本文档用于把一块新的 LCKFB 泰山派 3M RK3576 开发板配置到可以使用 .NET 控制 I2C 舵机控制板的状态。内容基于本次实测记录整理，最终已经验证物理 Pin 3 / Pin 5 对应的 I2C7_M1 可以被启用，`.NET 10` 可以通过 `System.Device.I2c` 与舵机控制器通信，并且使用 `ServoI2cTest` 成功让舵机运动。

## 1. 已验证的目标状态

最终目标是让板子具备以下能力：

- 系统中出现 `/dev/i2c-7`
- 40Pin 排针的物理 Pin 3 / Pin 5 可用作 I2C
- `.NET 10` 可以打开 `/dev/i2c-7`
- `.NET` 可以通过 `System.Device.I2c` 与舵机控制器通信
- `ServoI2cTest` 可以成功读状态、发送角度、执行循环测试

本次验证通过的板子信息：

```text
Board: LCKFB TaishanPi 3M RK3576
OS: Debian 12
Kernel: Linux 6.1.99
Architecture: aarch64
.NET SDK: 10.0.203
.NET Runtime: 10.0.7
I2C device: /dev/i2c-7
Verified control address: 0x03
```

## 2. 安全提醒

这块板子上 WiFi、蓝牙、4G、USB、Type-C 等功能已经占用了一些 GPIO / pinmux。启用 I2C 时不要随意改动当前正在用于 SPI、WiFi、4G、USB 的引脚，否则可能导致 WiFi / 4G 掉线，SSH 无法连接。

本次 I2C 舵机测试使用的是：

| 泰山派物理 Pin | 功能 | Rockchip GPIO | 全局 GPIO |
|---:|---|---|---:|
| 3 | I2C7_SDA_M1 | GPIO3_A1 | gpio97 |
| 5 | I2C7_SCL_M1 | GPIO3_A0 | gpio96 |

本次启用的是 `i2c7m1_xfer`，它与本次已经工作的 SPI1_M1 不冲突，可以和 SPI overlay 同时启用。

## 3. 40Pin 排针接线关系

树莓派风格 I2C 模块迁移到泰山派 3M 时，物理排针接线最直观。对 I2C 舵机控制器，建议最少连接以下几根：

| 舵机控制板信号 | 树莓派物理 Pin | 泰山派物理 Pin | 泰山派功能 |
|---|---:|---:|---|
| VCC | 1 / 17 | 1 / 17 | 3.3V 电源或按模块要求供电 |
| GND | 6 / 9 / 14 / 20 / 25 | 6 / 9 / 14 / 20 / 25 / 30 / 34 / 39 | GND |
| SDA | 3 | 3 | I2C7_SDA_M1 |
| SCL | 5 | 5 | I2C7_SCL_M1 |

注意事项：

- 物理 Pin 3 / 5 在这块板子上默认不是 `/dev/i2c-1`，必须先启用 `I2C7_M1`
- 舵机电源要按控制板规格单独确认，很多舵机不能直接靠开发板 3.3V 供电
- GND 必须共地，否则 I2C 通信即便有回包也可能动作异常

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

如果新板没有 .NET，可以按下面步骤安装 `.NET SDK 10`：

```bash
wget https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install -y dotnet-sdk-10.0
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

### 4.4 安装 I2C / 设备树工具

建议安装以下工具，方便启用和排查 I2C：

```bash
sudo apt-get update
sudo apt-get install -y i2c-tools device-tree-compiler
```

检查：

```bash
for c in i2cdetect i2cget i2cset i2cdump dtc; do
    printf '%-10s ' "$c"
    command -v "$c" || echo missing
done
```

## 5. 启用 I2C7_M1 设备树 overlay

### 5.1 为什么需要 overlay

这块板子的物理 Pin 3 / Pin 5 虽然是树莓派风格 I2C 位置，但实际对应的是 `I2C7_M1`，不是 `/dev/i2c-1`。如果没有启用对应 overlay，系统里不会出现 `/dev/i2c-7`，.NET 也无法通过这些排针和舵机控制器通信。

重启前后可用下面命令检查：

```bash
ls -l /dev/i2c*
```

如果没有 `/dev/i2c-7`，需要启用 I2C7 overlay。

### 5.2 已验证的 overlay 源码

工作区内已保留本次验证使用的 overlay 源文件：

- `v2_tspi-3m-i2c7-m1.dts`

内容非常简单，只启用 `&i2c7` 并绑定 `i2c7m1_xfer`：

```dts
/dts-v1/;
/plugin/;

&i2c7 {
    status = "okay";
    pinctrl-names = "default";
    pinctrl-0 = <&i2c7m1_xfer>;
    clock-frequency = <100000>;
};
```

当前设备树符号也已经实测确认存在：

```text
i2c7 -> /i2c@2aca0000
i2c7m1_xfer -> /pinctrl/i2c7/i2c7m1-xfer
```

### 5.3 从本地复制 DTS 到板子家目录

建议和 SPI overlay 一样，固定放在家目录中保存：

```powershell
ssh lckfb@192.168.31.123 "mkdir -p ~/tspi-3m-spi1-m1-overlay"
scp .\v2_tspi-3m-i2c7-m1.dts lckfb@192.168.31.123:~/tspi-3m-spi1-m1-overlay/tspi-3m-i2c7-m1.dts
```

板子上确认：

```bash
ls -lh ~/tspi-3m-spi1-m1-overlay/tspi-3m-i2c7-m1.dts
sed -n '1,80p' ~/tspi-3m-spi1-m1-overlay/tspi-3m-i2c7-m1.dts
```

### 5.4 在板子家目录编译 overlay

```bash
cd ~/tspi-3m-spi1-m1-overlay
dtc -@ -I dts -O dtb -o tspi-3m-i2c7-m1.dtbo tspi-3m-i2c7-m1.dts
ls -lh tspi-3m-i2c7-m1.dtbo
```

本次实测编译结果：

```text
/home/lckfb/tspi-3m-spi1-m1-overlay/tspi-3m-i2c7-m1.dtbo
375 bytes
```

### 5.5 安装 overlay 并配置启动项

如果系统已经启用了 SPI overlay，I2C7 overlay 需要和它一起写入 `overlays=` 这一行，而不是覆盖掉 SPI。

本次最终工作的配置是：

```text
overlays=tspi-3m-spi1-m1-spidev.dtbo tspi-3m-i2c7-m1.dtbo
```

安装命令：

```bash
cd ~/tspi-3m-spi1-m1-overlay
sudo cp /boot/ubootEnv.txt /boot/ubootEnv.txt.bak-i2c7-copilot
sudo cp tspi-3m-i2c7-m1.dtbo /boot/overlays/
sudo sed -i 's#^[[:space:]]*overlays=.*#overlays=tspi-3m-spi1-m1-spidev.dtbo tspi-3m-i2c7-m1.dtbo#' /boot/ubootEnv.txt
sync
grep -n '^[[:space:]]*overlays=' /boot/ubootEnv.txt
ls -lh /boot/overlays/tspi-3m-spi1-m1-spidev.dtbo /boot/overlays/tspi-3m-i2c7-m1.dtbo
```

然后重启：

```bash
sudo reboot
```

### 5.6 重启后验证 I2C7

先看设备节点：

```bash
ls -l /dev/i2c*
```

期望：

```text
/dev/i2c-7
```

看 I2C7 对应的 sysfs 路径：

```bash
ls -l /dev/i2c-7
cat /sys/class/i2c-dev/i2c-7/name
readlink -f /sys/class/i2c-dev/i2c-7
```

本次实测为：

```text
/dev/i2c-7
rk3x-i2c
/sys/devices/platform/2aca0000.i2c/i2c-7/i2c-dev/i2c-7
```

查看 pinmux：

```bash
sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null || true
sudo grep -E 'pin 96|pin 97|2aca0000|i2c7' /sys/kernel/debug/pinctrl/pinctrl-rockchip-pinctrl/pinmux-pins /sys/kernel/debug/pinctrl/pinctrl-maps
```

期望关键结果：

```text
pin 96 (gpio3-0): 2aca0000.i2c function i2c7 group i2c7m1-xfer
pin 97 (gpio3-1): 2aca0000.i2c function i2c7 group i2c7m1-xfer
```

扫描 I2C7：

```bash
sudo i2cdetect -y 7
```

本次实测看到：

```text
40: -- -- -- 43 -- -- -- --
```

注意：`i2cdetect` 看到 `0x43`，不代表 .NET 控制协议就应该使用 `0x43`。本次实际验证可工作的协议地址是 `0x03`。

## 6. 舵机控制协议与 ID 映射

### 6.1 本次验证的协议

本次基于上游示例及实测确认，控制器支持以下 5 字节协议：

```text
启用:   FF 01 00 00 00
禁用:   FF 00 00 00 00
写角度: 01 + float32
读取:   11 00 00 00 00
```

`.NET` 使用的是：

```csharp
device.WriteRead(tx, rx)
```

### 6.2 地址格式说明

Linux / `.NET` 这里使用的是 7-bit I2C 地址，不需要再左移。也就是说：

- 正确：`0x03`
- 不要手动改成 8-bit 格式

本次实测：

- `--bus 7 --address 0x03` 可以正常回包
- `--bus 7 --address 0x43` 在 .NET 中失败

### 6.3 与 Verdure 示例一致的关节 ID 映射

上游 `VerdureEmojisAndAction` 中使用的关节 ID 是：

```text
2, 4, 6, 8, 10, 12
```

它们对应的 I2C 控制地址是：

| 关节 ID | I2C 地址 |
|---:|---:|
| 2 | 0x01 |
| 4 | 0x02 |
| 6 | 0x03 |
| 8 | 0x04 |
| 10 | 0x05 |
| 12 | 0x06 |

也就是说：

- 业务层仍然建议用 `2/4/6/8/10/12`
- 底层协议地址才是 `0x01..0x06`

本次实测通过的目标是：

```text
joint 6 -> address 0x03
```

## 7. .NET 测试项目

### 7.1 ServoI2cTest 项目说明

工作区内已准备好可运行项目：

- `ServoI2cTest`

该项目已经扩展为同时支持：

- 原始地址模式：`--address` / `--addresses`
- 关节 ID 模式：`--joint` / `--joints`
- 单次角度写入：`--angle`
- 循环测试：`--sweep --cycles`

本地构建：

```powershell
dotnet build .\ServoI2cTest\ServoI2cTest.csproj
```

复制到板子：

```powershell
scp -r .\ServoI2cTest lckfb@192.168.31.123:~/ServoI2cTest
```

注意：如果重复多次使用 `scp -r .\ServoI2cTest ...:~/ServoI2cTest`，可能会把项目递归复制成 `~/ServoI2cTest/ServoI2cTest/...`，导致远端出现旧版和新版源码并存，编译时报重复定义错误。若出现这种情况，先清理再重新复制：

```bash
ssh lckfb@192.168.31.123 "rm -rf ~/ServoI2cTest"
```

然后重新复制。

板子上构建：

```bash
cd ~/ServoI2cTest
dotnet build
```

### 7.2 查看帮助

```bash
cd ~/ServoI2cTest
dotnet run --no-build -- --help
```

可看到本次新增的参数：

```text
--joint <id>
--joints <list>
--sweep
--cycles <n>
```

## 8. 实测通过的命令

### 8.1 只读探测

```bash
cd ~/ServoI2cTest
sudo dotnet run --no-build -- --bus 7 --addresses 0x03,0x43 --retries 2
```

本次实测结果：

```text
== 0x03 ==
read ok

== 0x43 ==
read failed
```

### 8.2 单次使能并设置角度

```bash
cd ~/ServoI2cTest
sudo dotnet run --no-build -- --bus 7 --address 0x03 --enable --angle 90 --retries 2
```

### 8.3 使用关节 ID 的单轮循环测试

这是本次最终通过、并且用户确认舵机实际已经动了的命令：

```bash
cd ~/ServoI2cTest
sudo dotnet run --no-build -- --bus 7 --joint 6 --enable --angle 90 --sweep --delta 20 --cycles 1 --delay 400 --retries 2
```

本次实测输出：

```text
I2C bus: 7
Targets: joint 6 (左臂) -> 0x03
Retries: 2
Delay: 400 ms

== joint 6 (左臂) -> 0x03 ==
enable=1 ok
angle=90.0 ok
cycle 1/1: low=70.0, high=110.0, center=90.0
angle=70.0 ok
angle=110.0 ok
angle=90.0 ok
read ok, reported=91.05
```

### 8.4 多轮循环测试

```bash
cd ~/ServoI2cTest
sudo dotnet run --no-build -- --bus 7 --joint 6 --enable --angle 90 --sweep --delta 20 --cycles 5 --delay 400 --retries 2
```

### 8.5 多关节顺序测试

```bash
cd ~/ServoI2cTest
sudo dotnet run --no-build -- --bus 7 --joints 2,4,6,8,10,12 --enable --sweep --delta 15 --cycles 2 --delay 300 --retries 2
```

注意：当前 `ServoI2cTest` 对多个关节是顺序发命令，适合联调和排障，不是高层动作编排器。

## 9. 常见问题

### 9.1 为什么物理 Pin 3 / 5 不是 `/dev/i2c-1`

因为这块板子上的树莓派风格 40Pin 位置并不直接等于 Linux 设备编号。物理 Pin 3 / 5 对应的是 `I2C7_M1`，启用后设备节点是 `/dev/i2c-7`。

### 9.2 为什么 `i2cdetect -y 7` 显示 `0x43`，但程序用的是 `0x03`

这是本次实测里最容易混淆的点。`i2cdetect` 看到的 `0x43` 并没有在 `.NET` 协议读写里成功，真正能按 ServoF030 风格协议回包的是 `0x03`。因此当前文档和代码都以 `0x03` 为准。

### 9.3 为什么重复复制后远端编译报重复定义

因为多次递归复制会产生嵌套目录，例如：

```text
~/ServoI2cTest/Program.cs
~/ServoI2cTest/ServoI2cTest/Program.cs
```

这会让 `dotnet build` 同时看到两套源码，出现：

```text
Only one compilation unit can have top-level statements
already contains a definition for 'Options'
```

处理方式是：

```bash
ssh lckfb@192.168.31.123 "rm -rf ~/ServoI2cTest"
```

然后重新复制一份干净目录。

### 9.4 程序显示成功，但舵机没动怎么办

先按以下顺序排查：

1. 确认使用的是 `--bus 7`
2. 确认使用的是 `--joint 6` 或 `--address 0x03`
3. 确认舵机控制板供电足够，并且与开发板共地
4. 确认当前测试的确实是接在 `0x03` 这个控制地址对应的舵机通道
5. 先跑只读探测，确认 `read ok`
6. 再跑单次 `--enable --angle 90`
7. 最后跑 `--sweep --cycles`

## 10. 最小复现清单

如果你拿到一块新的开发板，想最快复现到“舵机能动”的状态，可以按下面顺序做：

1. 安装 `.NET SDK 10`、`i2c-tools`、`device-tree-compiler`
2. 复制 `v2_tspi-3m-i2c7-m1.dts` 到板子家目录
3. 编译得到 `tspi-3m-i2c7-m1.dtbo`
4. 把 `/boot/ubootEnv.txt` 配置成：
   `overlays=tspi-3m-spi1-m1-spidev.dtbo tspi-3m-i2c7-m1.dtbo`
5. 重启，确认 `/dev/i2c-7` 存在
6. 确认 Pin 96 / 97 已经 pinmux 到 `i2c7m1-xfer`
7. 复制并构建 `ServoI2cTest`
8. 执行：

```bash
cd ~/ServoI2cTest
sudo dotnet run --no-build -- --bus 7 --joint 6 --enable --angle 90 --sweep --delta 20 --cycles 1 --delay 400 --retries 2
```

如果这条命令能让舵机动作，就说明整条 I2C + .NET + 舵机控制链路已经跑通。
