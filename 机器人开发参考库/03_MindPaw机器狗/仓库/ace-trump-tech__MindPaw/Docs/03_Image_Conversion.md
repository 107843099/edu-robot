# 03 — 图片转 OLED 像素图指南

> ⭐ **使用本教程前，请先支持一下这个开源项目：**
>
> 1. **Star ⭐** — 点击 GitHub 仓库右上角 ⭐ Star，收藏本项目，方便以后找到
> 2. **Fork 🍴** — 点击 Fork，把项目复制到你的 GitHub 账号下，可以自由修改
> 3. **Download 📥** — 点击绿色 **Code** 按钮 → **Download ZIP**，下载到本地开始复刻
>
> 📸 **操作示意图：**
>
> ![Star-Fork-Download](../Picture/demo.jpg)

---

## 概述

MindPaw 使用 **128×64 OLED 显示屏** 显示表情图标。图片需要经过以下流水线：

```
源文件 (BMP/PNG/JPG) → bmp.py → 128×64 二值 BMP → PCtoLCD2002 → C 数组 → image.cpp
```

---

## 方法一：使用 Python 脚本（推荐，全自动）

### 1. 安装依赖

```bash
pip install Pillow
```

### 2. 运行脚本

```bash
cd Picture\PCtoLCD2002

# 基本用法
python bmp.py -i input.png -o output.bmp

# 调整二值化阈值（浅色图片用低阈值）
python bmp.py -i input.png -o output.bmp -t 100

# 批量转换（示例批处理脚本）
for %f in (..\MindPaw_oled\*.png) do python bmp.py -i "%f" -o "..\MindPaw_oled\%~nf.bmp"
```

### 3. 脚本参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i, --input` | 输入图片路径 | `input.png` |
| `-o, --output` | 输出 BMP 路径 | `output.bmp` |
| `-t, --threshold` | 二值化阈值 (0-255) | `128` |

**阈值调优技巧：**
- 原始图片偏暗 → 降低阈值（`-t 80`）
- 原始图片偏亮 → 提高阈值（`-t 180`）
- 线条画/漫画 → 保持 `128` 即可

---

## 方法二：使用 PCtoLCD2002（经典 Windows 工具）

### Step 1：准备源图片

1. 准备一张图片（建议 128×64 或更大）
2. 先用 `bmp.py` 转为 128×64 黑白 BMP：

```bash
python bmp.py -i Picture\MindPaw_oled\hi.png -o hi.bmp
```

### Step 2：打开 PCtoLCD2002

1. 运行 `Picture\PCtoLCD2002\PCtoLCD2002.exe`
2. 界面说明：
   - 左侧：图形预览区
   - 右侧：参数设置区
   - 底部：生成的 C 代码区

### Step 3：导入图片

1. 点击菜单 **文件 → 打开图像**
2. 选择上一步生成的 `.bmp` 文件
3. 确认显示正常

### Step 4：设置参数

在右侧面板设置：

| 参数 | 设置值 | 说明 |
|------|--------|------|
| **取模方式** | 逐行式 | OLED 的 SSD1306 驱动方式 |
| **每行显示** | 128 点 | OLED 宽度 |
| **每页显示** | 64 点 | OLED 高度 |
| **字节内点阵** | 高位在前 | 与 U8g2 库匹配 |
| **输出格式** | C 语言 | 生成 C 代码 |
| **码制** | 十六进制 | 最常用 |

### Step 5：生成 C 代码

1. 点击 **参数 → 生成图像数据**
2. 底部代码区会生成类似内容：

```c
{0x00, 0x80, 0x40, 0x20, ...}  // 共 1024 字节 (128 × 64 / 8)
```

### Step 6：导入到 project

1. 将生成的数组复制到 `image.cpp` 中
2. 按照已有格式添加：

```c
// 在 image.cpp 添加
const unsigned char myEmoji[] PROGMEM = {
    // 粘贴 PCtoLCD2002 生成的代码
};
```

3. 在 `main.cpp` 的 `drawXBMP()` 中调用：

```c
do {
    u8g2.drawXBMP(0, 0, 128, 64, myEmoji);
} while (u8g2.nextPage());
```

---

## 现有表情文件清单

`Picture/MindPaw_oled/` 目录下的源文件：

| 文件名 | 对应表情 | image.cpp 常量名 |
|--------|---------|-----------------|
| `hi.bmp` | 开心/打招呼 | `hi` |
| `gogo.bmp` | 生气 | `angry` |
| `did.bmp` | 错误/困惑 | `error` |
| `dowhat2.bmp` | 好奇 | `dowhat` |
| `love.bmp` | 喜爱 | `love` |
| `error.bmp` | 难过 | `sick` |
| `yun.bmp` | 晕 | `yun` |
| `cloud.bmp` | 多云天气 | `cloud` |
| `sun.bmp` | 晴天 | `sun` |
| `rain.bmp` | 雨天 | `rain` |
| `time-svgrepo-com.bmp` | 时钟 | `timeimage` |
| `wifi-problem-svgrepo-com.bmp` | WiFi 断连 | `wifi` |

> **注意**：部分文件名与 `image.cpp` 中的常量名不完全对应。添加新表情时请先确认常量名再替换。
