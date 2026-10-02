# 泰山派 3M RK3576 .NET 应用无 sudo 访问 GPIO/SPI/I2C 指南

本文档解决以下问题：在泰山派 3M 上运行需要同时使用 **SPI 显示屏、I2C 舵机、PipeWire 音频** 的 .NET 应用时，既不能用 `sudo`（PipeWire 是用户会话服务，root 下不可用），又需要访问默认只有 root 才能读写的 `/dev/gpiochip*`、`/dev/spidev*`、`/dev/i2c-*` 设备。

## 1. 问题根源

| 运行方式 | GPIO / SPI / I2C | PipeWire 音频 |
|---|---|---|
| `sudo dotnet run` | ✅ root 可访问 | ❌ socket 在 `/run/user/1000`，root 无法连接 |
| `dotnet run`（lckfb） | ❌ 设备默认 `root:root 600` | ✅ 用户会话正常 |

**解决方案**：通过 udev 规则 + 用户组，让 lckfb 用户直接拥有设备权限。

## 2. 一次性配置步骤

### 2.1 创建设备组

```bash
sudo groupadd -g 1003 gpio
sudo groupadd -g 1004 spi
# i2c 组通常已存在（GID 106），确认一下：
getent group i2c || sudo groupadd i2c
```

### 2.2 将用户加入各组

```bash
sudo usermod -aG gpio,spi,i2c lckfb
```

加入组后需要**重新登录**（或新开 SSH 会话）才能生效，用 `id` 确认：

```text
uid=1000(lckfb) gid=1000(lckfb) groups=1000(lckfb),...,106(i2c),...,1003(gpio),1004(spi)
```

### 2.3 写入 udev 规则

创建文件 `/etc/udev/rules.d/99-gpio-spi-i2c.rules`，内容如下：

```
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"
SUBSYSTEM=="spidev", KERNEL=="spidev*", GROUP="spi", MODE="0660"
SUBSYSTEM=="i2c-dev", KERNEL=="i2c-*", GROUP="i2c", MODE="0660"
```

推荐写法（避免引号转义问题）：

```bash
cat > /tmp/99-gpio-spi-i2c.rules << 'EOF'
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"
SUBSYSTEM=="spidev", KERNEL=="spidev*", GROUP="spi", MODE="0660"
SUBSYSTEM=="i2c-dev", KERNEL=="i2c-*", GROUP="i2c", MODE="0660"
EOF
sudo cp /tmp/99-gpio-spi-i2c.rules /etc/udev/rules.d/
```

### 2.4 重载规则并触发

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

触发后新权限**立即**对已有设备生效，无需重启。

### 2.5 验证权限

```bash
ls -la /dev/gpiochip2 /dev/i2c-7 /dev/spidev1.0
```

期望输出：

```text
crw-rw---- 1 root gpio  254, 2  /dev/gpiochip2
crw-rw---- 1 root i2c    89, 7  /dev/i2c-7
crw-rw---- 1 root spi   153, 0  /dev/spidev1.0
```

## 3. 验证结果

本次在以下环境验证通过（无 sudo，直接 `dotnet run`）：

```text
Board: LCKFB TaishanPi 3M RK3576
OS: Debian 12
Kernel: Linux 6.1.99
Architecture: aarch64
.NET SDK: 10.0.203
用户: lckfb
```

初始化日志摘要：

```
✅ 显示器初始化成功
✅ 初始化I2C设备地址 0x01 成功
✅ 初始化I2C设备地址 0x03 成功
✅ 初始化I2C设备地址 0x05 成功
✅ 初始化I2C设备地址 0x06 成功
✅ SoundFlow录音引擎初始化完成
✅ SoundFlow播放引擎初始化完成
✅ SoundFlow音频播放器设备初始化成功: 16000Hz, 1声道
✅ SoundFlow引擎初始化成功，播放设备: Built-in Audio Headphones + Speaker
Now listening on: http://0.0.0.0:5000
```

## 4. 重启持久性说明

- **udev 规则**（`/etc/udev/rules.d/99-gpio-spi-i2c.rules`）在重启后自动生效，内核加载设备时会自动应用 GROUP 和 MODE。
- **用户组成员关系**（`/etc/group`）是永久的，不受重启影响。
- 无需任何开机脚本或 `rc.local`。

## 5. 常见问题

**Q：`udevadm trigger` 之后设备权限没有变化？**

检查规则文件是否有语法错误：
```bash
sudo udevadm test $(udevadm info --query=path --name=/dev/gpiochip2) 2>&1 | grep -E 'GROUP|MODE'
```

**Q：已在组里，但运行时仍报 Permission denied？**

当前 shell 可能是在加组之前登录的，需要新开 SSH 会话：
```bash
# 在新会话中确认
id | grep gpio
```

**Q：为什么 gpiochip2 而不是 gpiochip0？**

泰山派 3M 的 40Pin 排针 GPIO 对应 `gpiochip2`（RK3576 GPIO Bank 2 / GPIO2_xxx）。可通过以下命令确认：
```bash
gpioinfo | grep -A5 "gpiochip2"
# 或者
cat /sys/bus/gpio/devices/gpiochip2/label
```
