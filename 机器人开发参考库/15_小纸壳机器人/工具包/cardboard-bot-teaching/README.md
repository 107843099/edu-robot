# cardboard-bot 六步教学安装包

当前版本：V0.3。

这是给零基础用户使用的离线教学入口。它包含一个静态网页、五个独立教学固件和一个完整系统固件。普通用户只需要 ESP32-C3、数据 USB 线，以及最新版 Chrome 或 Edge；不需要安装 Arduino IDE、PlatformIO、Python 或其他开发库。

## 使用方法

1. 运行 `start-offline-installer.cmd`，或把本目录发布到 HTTPS；不要直接双击 `index.html`。
2. 第一次使用新版固件前，同时断开 USB 和全部外部电源，把 OLED 永久改为 SDA→GPIO0、SCL→GPIO1，并保持 GPIO8/GPIO9 空闲。以后刷机不需要拔 OLED 信号线，只需关闭外部电源，让 ESP32 由电脑 USB 供电。
3. 点击当前步骤的安装按钮，在浏览器弹窗选择 ESP32-C3 串口，按提示完成刷机。
4. 安装成功后关闭刷机窗口，恢复页面要求的模块电源并按一次 `RST`。前五步可点击“连接测试”核对固件身份；两个舵机步骤再点击“开始测试”。第 06 步点击“连接完整系统”，识别固件后可直接使用校准按钮。
5. 现场观察通过后断开全部电源，再进入下一步。屏幕通过后按页面要求保留 OLED。

如果打开后只看到标题和安全提示、没有第 01～06 步，说明直接双击了 `index.html`；关闭页面并运行同目录的 `start-offline-installer.cmd`，再打开脚本显示的 `http://localhost:端口/` 地址。`file://` 页面不能加载本地模块，也不能获得 Web Serial 权限。

设备选择窗口已按本项目实测的 Espressif 原生 USB 标识 `303A:1001` 筛选，通常只显示 `USB JTAG/serial debug unit` 或对应的 USB 串行设备。浏览器不会把 Windows 的 `COM7` 这类端口号提供给网页，首次使用仍需在弹窗中点击设备并授权；如果同时连接多块同型号 ESP 开发板，请先拔掉其他板，只保留当前要安装的一块。使用 CH340 / CP210x 转接芯片的其他板型不在当前筛选范围内。

步骤固定为：

- 01 屏幕：循环显示 HELLO、BORDER、棋盘格和 INVERT。
- 02 双红外：左红外 OUT→GPIO4、右红外 OUT→GPIO3；分别遮挡左、右、同时遮挡，再移开，确认 LEFT/RIGHT 与实物一致。
- 03 水平舵机：只接 GPIO5 的一只舵机，空载执行 `90° → 85° → 95° → 90°` 一轮。
- 04 俯仰舵机：只接 GPIO6 的一只舵机，空载执行同样一轮小动作。
- 05 触摸：触摸和松开 TTP223，确认状态变化并完成 5 次计数。
- 06 完整系统：安装完整固件；首次装配先取下舵盘与负载，进入校准后点“恢复默认中位”让两轴到默认 90°，断电后朝正装舵盘。之后可点“回到自定义中位”、每次 1°微调并“保存自定义中位”，再做整机验收。默认回中不改写自定义中位；急停会关闭 PWM，恢复驱动不会自动回中。

## 安全边界

- 改线前同时断开 ESP32 USB 和外部 5V；外部 5V 不得接到 ESP32 的 5V 电源脚。
- OLED、红外和 TTP223 使用电源模块 3.3V；舵机使用独立稳定 5V；所有模块共地。
- 两个舵机教学步骤都不安装舵盘、不接纸板头部或其他负载。出现嗡鸣、卡住、异常复位或发热，立即断开外部 5V。
- 页面中的身份匹配、串口应答和“现场观察通过”是不同事项；软件不会替用户声称硬件已验收。

## 分区域安装

每个 manifest 都写入四个区域：bootloader `0x0000`、partitions `0x8000`、boot_app0 `0xE000` 和应用 `0x10000`。安装默认不整片擦除，`release.json` 会记录每个区域的大小、SHA-256 和 NVS 未覆盖范围。页面与资源必须同源，通过 HTTPS 或 `localhost` 打开。

发布目录由脚本生成：

```text
web-installer/
├─ index.html
├─ teaching-page.js
├─ test-connection.js
├─ device-status.js
├─ release.json
├─ manifest-display.json ... manifest-touch.json
├─ manifest.json
└─ firmware/teaching/01-display ... 06-robot/*.bin
```

开发者在仓库根目录执行：

```text
PlatformIO: Build robot, test_display, test_infrared, test_servo_pan, test_servo_tilt, test_touch
python tools/build_teaching_package.py --platformio-home D:/PlatformIO
```

打包脚本只读取六个构建目录和 `boot_app0.bin`，生成 `release.json`、分区域资源及 `artifacts/cardboard-bot-teaching-offline-V<version>.zip`；不会打开串口，也不会执行刷写。

## 常见问题

- 页面提示浏览器不支持：使用最新版 Chrome 或 Edge。
- 页面提示没有串口权限：确认网址是 HTTPS 或 `localhost`，不要从 `file://` 打开。
- 弹窗里没有设备：使用数据 USB 线，关闭 Arduino/PlatformIO 串口监视器后重新插拔设备。
- 弹窗里有多个相同的 Espressif 设备：拔掉其他 ESP 开发板，只保留当前要安装的一块，再重新点击安装。
- 安装提示 `SPI_DOWNLOAD_BOOT / wait spi download`：这不是可刷写的串口下载模式，说明复位时 GPIO8 被拉低。结束安装并断开全部电源，确认 GPIO8/GPIO9 没有连接任何模块、OLED 已接 GPIO0/GPIO1，再只接 USB 重新执行 BOOT → RESET → 松 RESET → 松 BOOT。新版会立即显示中文处理办法，不再继续转圈。`Blocked aria-hidden` 只是浏览器无障碍警告，与刷写失败无关。
- 安装失败：断开外部 5V，重新插拔 USB，再选择当前实际出现的串口。
- 舵机测试按钮不可用：先关闭刷机窗口并点击“连接测试”；固件身份和 OLED 应答通过后才能开始。
