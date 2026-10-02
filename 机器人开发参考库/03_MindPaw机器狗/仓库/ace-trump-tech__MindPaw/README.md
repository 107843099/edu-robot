
<p align="center">
  <img src="Picture/MindPaw_oled/hi.bmp" alt="MindPaw" width="128"/>
</p>

<h1 align="center">🐕 MindPaw</h1>

<p align="center">
  <em>桌面级四足机器狗 — 语音交互·手势识别·AI对话·网页控制</em>
  <br>
  <strong>v2.0 — 新增流式 3D 重建感知层（端到端 ~150 ms，ABot-Recon 思想）</strong>
  <br>
  <strong>总物料成本 ≈¥50，全开源</strong>
</p>

<p align="center">
  <!-- 第一行：社交 + 核心文档入口 -->
  <a href="https://github.com/ace-trump-tech/MindPaw/stargazers" target="_blank">
    <img src="https://img.shields.io/github/stars/ace-trump-tech/MindPaw?style=social" alt="GitHub Stars">
  </a>
  <a href="https://github.com/ace-trump-tech/MindPaw/fork" target="_blank">
    <img src="https://img.shields.io/github/forks/ace-trump-tech/MindPaw?style=social" alt="GitHub Forks">
  </a>
  <a href="Docs/06_Quick_Start.md">
    <img src="https://img.shields.io/badge/Quick_Start-5分钟上手-brightgreen" alt="Quick Start">
  </a>
  <a href="Docs/07_API_Guide.md">
    <img src="https://img.shields.io/badge/API_配置-图文教程-blue" alt="API Guide">
  </a>
  <a href="Docs/04_Firmware_Flashing.md">
    <img src="https://img.shields.io/badge/烧录指南-VSCode+PlatformIO-orange" alt="Flashing Guide">
  </a>
  <br>
  <!-- 第二行：许可证 + 硬件 / 3D / 打样 -->
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  </a>
  <a href="SCH&PCB/">
    <img src="https://img.shields.io/badge/PCB-立创EDA专业版-blueviolet" alt="PCB">
  </a>
  <a href="3Dmodel/">
    <img src="https://img.shields.io/badge/3D打印-STL文件-yellow" alt="3D Model">
  </a>
  <a href="https://oshwhub.com/">
    <img src="https://img.shields.io/badge/免费打样-嘉立创-red" alt="JLCPCB">
  </a>
</p>

---

## 📋 目录

- [这是什么？](#-这是什么)
- [功能总览](#-功能总览)
- [你需要准备什么](#-你需要准备什么)
- [如何复刻](#-如何复刻)
- [项目结构](#-项目结构)
- [AI Infra 网关](#-ai-infra-网关)
- [硬件接线图](#-硬件接线图)
- [文档索引](#-文档索引)
- [分支与版本](#-分支与版本)
- [常见问题](#-常见问题)
- [维护与贡献](#-维护与贡献)
- [许可证](#-许可证)

---

## 🎯 这是什么

**MindPaw** 是一个桌面四足机器人项目，基于 **ESP8266** 微控制器。它的特色是：

- **不只是遥控车** — 你可以和它对话、对它做手势、它会有情绪反应
- **真的能聊 AI** — 接入了豆包大模型，能做智能对话
- **真的便宜** — 全部物料加起来不到 **¥50**（基础版仅 ¥35）
- **真的开源** — 代码、电路图、3D 打印文件全部提供

> 这个项目是从零开始自己做的，不是用现成的开发板套件。所以如果你想学习怎么把 ESP8266、舵机、摄像头、语音模块、AI 全部整合在一起，这里的代码和文档应该能帮到你。

## 🚦 从哪里开始

这个仓库分为两条互不阻塞的路径：

| 路径 | 适合人群 | 入口 |
|------|---------|------|
| **MindPaw Demo** | 初学者、硬件爱好者，目标是把机器狗复现并玩起来 | [MindPaw_main/README.md](MindPaw_main/README.md) |
| **MindPaw AI Infra** | AI Infra、边缘计算和 Agent 研究者 | [ai-infra/README.md](ai-infra/README.md) |
| **🛰️ MindPaw 2.0 流式 3D 重建** | 给机器狗加"看见前方"的能力（避障 + 浏览器点云） | [Docs/09_Streaming_Recon.md](Docs/09_Streaming_Recon.md) |
| **SCH & PCB** | 想自己画板、打样或排查供电/接线问题的人 | [SCH&PCB/README.md](SCH%26PCB/README.md) |

初学者不需要安装 Python、Docker 或 AI Gateway；完成基础 Demo 后，再按兴趣进入研究路径。两条路径共享同一套固件和硬件，Gateway 地址留空即可回到原有直连模式。2.0 感知层默认关闭，在 aiconfig.html 里填一个 Recon Gateway URL 即可启用。

---

## ✨ 功能总览

| 功能 | 怎么触发 | 机器人会做什么 |
|------|---------|---------------|
| **语音控制** | 说"前进""开心""你好" | 执行动作、切换表情、播放音效 |
| **手势控制** | 在摄像头前挥手/握拳/指点 | 识别手势后执行对应动作 |
| **网页控制** | 手机浏览器打开 192.168.4.1 | 完整的遥控界面，可点按控制 |
| **AI 对话** | 网页聊天 / 语音说"你好" | 调用豆包 API，用动作+表情回复 |
| **AI Infra 网关** | 可选配置 Gateway 地址 | 面向研究者的 AI 基础设施教程；初学者可以完全跳过 |
| **🛰️ 流式 3D 重建感知层（v2.0）** | 摄像头自动推流 | 每帧推流到 Edge Gateway，机器狗能感知障碍距离并自动避障；浏览器可视化稀疏点云。详见 [Docs/09_Streaming_Recon.md](Docs/09_Streaming_Recon.md) |
| **情感反应** | 持续运行中自动变化 | 根据交互频率和内容，表现出开心/无聊/难过等情绪 |
| **表情显示** | OLED 屏幕显示 | 7 种表情 + 天气 + 时间 |
| **声音反馈** | 扬声器播放旋律 | 开机/命令确认/情绪表达共 10 种音效 |

---

## 🛒 你需要准备什么

### 硬件清单

> 以下价格来自 **淘宝/拼多多** 真实售价（2026年7月）。量大还能更便宜。

#### 🏆 方案一：完整版（≈¥50，带摄像头手势识别）

| 模块 | 参考价格 | 购买建议 |
|------|---------|---------|
| ESP12F 模块 | **¥5** | 买裸模块自己焊，不要买 NodeMCU 开发板（¥15 贵 3 倍） |
| SG90 舵机 ×4 | **¥12** | 拼多多 4 个装 ¥12，淘宝散买约 ¥3.5/个 |
| SSD1306 OLED 128×64 I2C | **¥6** | 选白色最便宜，蓝色¥7、双色¥9 |
| OV2640 摄像头 | **¥15** | 买不带 FIFO 的裸板，不要买 ArduCAM Mini（¥25） |
| HLK-V20 语音模块 | **¥9** | 搜 "SU-03T" 比 "HLK-V20" 便宜，同一个东西 |
| 8Ω 喇叭 + S8050 + 电阻电容 | **¥3** | 一套散件，邮费都比货贵，建议和其他一起买 |
| PCB 打样 | **¥0** | 嘉立创每月 2 张免费券 |
| 3D 打印 | **¥0** | 嘉立创新用户有免费券 |
| USB 供电 | **¥0** | 手机充电器 + MicroUSB 线，人人都有 |
| **合计** | **≈ ¥50** | |

#### 🥉 方案二：基础版（≈¥35）

去掉摄像头，保留语音控制 + AI 对话 + 情感交互。适合先入门、再升级。

| 模块 | 价格 |
|------|------|
| ESP12F ¥5 + SG90×4 ¥12 + OLED ¥6 + SU-03T ¥9 + 喇叭套件 ¥3 | **≈ ¥35** |

> 💡 **注**：¥35-¥50 是 **物料裸价**，不含邮费（约 ¥8）。首次购买建议一次买齐所有器件，邮费只付一次。

### 软件准备

| 软件 | 用途 | 下载地址 |
|------|------|---------|
| **VSCode** | 代码编辑器 | [code.visualstudio.com](https://code.visualstudio.com/) |
| **PlatformIO 扩展** | 编译和烧录 | VSCode 扩展商店搜索安装 |
| **Python 3** | 图片转换工具 | [python.org](https://www.python.org/) |
| **嘉立创 EDA 专业版** | 查看/修改 PCB | [pro.lceda.cn](https://pro.lceda.cn/) |
| **SU-03T 配置工具** | 配置语音模块 | 百度搜索 "SU-03T 配置工具" |

### 需要申请的免费账号

| 服务 | 用途 | 申请地址 | 是否必选 |
|------|------|---------|---------|
| **心知天气** | 获取天气信息 | [seniverse.com](https://www.seniverse.com/) | 可选 |
| **火山引擎方舟** | AI 对话 (豆包) | [console.volcengine.com](https://console.volcengine.com/ark/) | 可选 |
| **嘉立创** | 免费打样 PCB、3D 打印 | [jlc.com](https://www.jlc.com/) | 可选 |

> 以上两个 API 都是可选功能。不配置的话，机器狗的基本运动、表情、语音控制仍能正常工作。

---

## 🚀 如何复刻

从零开始做一台 MindPaw，按这个顺序走。

> ⭐ **开始前，请先支持一下这个开源项目：**
>
> 1. **Star ⭐** — 点击仓库右上角 ⭐ Star，收藏本项目，方便以后找到
> 2. **Fork 🍴** — 点击 Fork，把项目复制到你自己的 GitHub，之后可自由修改并提交 PR
> 3. **Download 📥** — 点击绿色 **Code** 按钮 → **Download ZIP**，或直接 clone：
>
> 📸 **操作示意图：**
>
> ![Star-Fork-Download](Picture/demo.jpg)

```bash
git clone https://github.com/ace-trump-tech/MindPaw.git
```

### 第一步：烧录固件（先让代码跑起来）

先只买 **NodeMCU + USB-TTL**，花 30 分钟验证环境：

```bash
# 1. 安装 VSCode + PlatformIO 扩展
# 2. 克隆项目并打开
git clone https://github.com/你的用户名/MindPaw.git
cd MindPaw/MindPaw_main

# 3. 编译
pio run

# 4. 连接 NodeMCU（GPIO0 接地 → 上电）
# 5. 烧录固件
pio run -t upload

# 6. 上传 Web 页面
pio run -t uploadfs

# 7. 断开 GPIO0 接地 → 按 RST
# 8. 连接 WiFi "MindPaw" → 打开 192.168.4.1
```

详细步骤 → [Docs/04_Firmware_Flashing.md](Docs/04_Firmware_Flashing.md)

### 第二步：打样 PCB 和 3D 打印（做硬件）

如果你有嘉立创的免费打样券，这一步可以不花钱：

| 步骤 | 说明 | 参考文档 |
|------|------|---------|
| 导出 PCB Gerber 文件 | 打开 `SCH&PCB/MindPaw_SCH&PCB.epro2` → 文件 → 制造 → Gerber | [01_Hardware_Guide.md](Docs/01_Hardware_Guide.md) |
| 下单免费打样 | 嘉立创下单助手 → 上传 Gerber → 使用优惠券 | [02_PCB_Fabrication.md](Docs/02_PCB_Fabrication.md) |
| 3D 打印外壳 | 上传 `3Dmodel/*.stl` → 选择 PLA → 使用优惠券 | [02_PCB_Fabrication.md](Docs/02_PCB_Fabrication.md) |

### 第三步：焊接和组装

收到 PCB 和 3D 打印件后：

1. **先焊接电源部分** — 测试 3.3V 和 5V 输出正常
2. **焊接 ESP12F 核心** — 烧录固件验证
3. **逐个添加模块** — OLED → 舵机 → 语音 → 摄像头 → 扬声器
4. **3D 打印件组装** — 舵机装入底盘 → 合上身体 → 安装脚部

接线图 → [05_Assembly_Guide.md](Docs/05_Assembly_Guide.md)

### 第四步：配置 API（可选）

如果你想要 AI 对话和天气查询功能：

| 服务 | 申请步骤 | 配置位置 |
|------|---------|---------|
| 心知天气 API | 注册 → 创建免费版 → 复制 Key | 网页控制台 → 设置页面 |
| 火山引擎 API | 注册 → 创建推理接入点 → 复制 Key | `http://192.168.4.1/aiconfig.html` |

图文步骤 → [Docs/07_API_Guide.md](Docs/07_API_Guide.md)

### 第四步（可选）：启动 AI Infra 网关

`ai-infra` 是可选的独立 AI 基础设施层。它负责上游模型适配、鉴权、超时和结构化输出校验，适合希望研究 Agent、模型接入和边缘设备协同的开发者。初学者可以跳过这一节，直接使用原有的 ESP8266 直连豆包模式，不会影响机器狗的基础功能和 AI 对话。

```bash
cd ai-infra
cp .env.example .env
# 编辑 .env，配置 GATEWAY_TOKEN、AI_PROVIDER 和上游 API Key
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn gateway.app:app --host 0.0.0.0 --port 8000
```

没有云端 Key 时，可以将 `.env` 中的 `AI_PROVIDER` 设为 `mock`，先验证设备链路。然后打开 `http://192.168.4.1/aiconfig.html`：

- **API Key**：填写 `GATEWAY_TOKEN`
- **推理端点 ID**：填写 `mindpaw`
- **AI Gateway 地址**：填写 `http://网关IP:8000/v1/chat/completions`

Docker 用户可以运行 `cd ai-infra && docker compose up --build -d`。完整说明见 [ai-infra/README.md](ai-infra/README.md)。

### 两种使用路径

| 目标 | 建议路径 |
|------|---------|
| 第一次复现机器狗、学习 ESP8266 和 Arduino | 跳过 `ai-infra`，直接配置豆包 API |
| 研究 AI Agent、模型路由、结构化输出和边缘网关 | 启动 `ai-infra`，通过 Gateway 接入设备 |

这两条路径共享同一套固件和网页功能，可以随时从直连模式切换到 Gateway 模式。

### 为什么先放在同一个仓库？

当前阶段保持 monorepo 的好处是：初学者只需下载一个仓库即可复现，研究者也能在同一个仓库中阅读固件、协议和 Gateway。等接口稳定、网关需要服务其他机器人后，再把 `ai-infra` 独立成可插拔仓库或 Python 包，并保留本仓库的版本化配置示例。

### 第五步：配置语音模块

HLK-V20 需要用电脑配置好之后才能用：

1. 下载 SU-03T 配置工具
2. 通过 USB-TTL 连接模块
3. 按表格添加 22 条语音命令
4. 烧录 → 断电 → 接到 MindPaw

详细命令表 → [Docs/07_API_Guide.md#3-hlk-v20-语音模块配置](Docs/07_API_Guide.md#3-hlk-v20-语音模块配置)

---

## 📁 项目结构

```
MindPaw/
│
├── 3Dmodel/                    ← 3D 打印件（body.stl / bottom.stl / foot.stl）
│
├── SCH&PCB/                    ← 电路设计文件（立创 EDA 专业版）
│   ├── MindPaw_SCH&PCB.epro2
│   └── README.md                ← 硬件复现、打样和排障入口
│
├── MindPaw_main/               ← 固件源代码（初学者 Demo 入口）
│   ├── README.md                ← 编译、烧录、验收和故障排查
│   ├── src/                    ← C++ 源码
│   │   ├── main.cpp            ← 主程序（入口、Web服务器、舵机动作）
│   │   ├── image.cpp           ← OLED 屏幕显示的位图数据
│   │   ├── hlkv20.*            ← HLK-V20 语音识别模块驱动
│   │   ├── ov2640.*            ← OV2640 摄像头驱动
│   │   ├── speaker.*           ← 扬声器旋律播放
│   │   ├── motion_emotion.*    ← 机器狗的情感动作（跳舞、点头等）
│   │   ├── emotion_engine.*    ← 情感状态机（PAD 模型）
│   │   ├── gesture_nn.*        ← 手势识别（轻量 MLP）
│   │   ├── multimodal_fusion.* ← 多模态输入融合
│   │   ├── doubao_agent.*      ← 豆包 AI API 客户端
│   │   └── doubao_config.h     ← AI 提示词和配置
│   ├── data/                   ← 网页控制界面（11 个 HTML 文件）
│   ├── tools/                  ← Python 工具脚本
│   │   └── distill_gesture.py  ← 手势模型训练脚本
│   ├── platformio.ini          ← 编译配置文件
│   └── PIN_WIRING.md           ← 引脚接线图
│
├── ai-infra/                   ← 独立 AI Gateway（可选，研究者教程）
│   ├── gateway/app.py          ← OpenAI 兼容入口、鉴权和上游适配
│   ├── tests/                  ← Gateway 契约单元测试
│   ├── .env.example            ← 网关配置模板
│   ├── Dockerfile              ← 容器部署
│   └── README.md               ← 研究问题、实验路线和网关启动说明
│
├── Picture/                    ← 图片资源
│   ├── MindPaw_oled/           ← 表情源文件（BMP）
│   └── PCtoLCD2002/            ← 图片转像素图工具
│
├── Docs/                       ← 文档
│   ├── 01_Hardware_Guide.md    ← 硬件设计导入指南
│   ├── 02_PCB_Fabrication.md   ← PCB 免费打样指南
│   ├── 03_Image_Conversion.md  ← OLED 表情制作指南
│   ├── 04_Firmware_Flashing.md ← 固件烧录指南
│   ├── 05_Assembly_Guide.md    ← 结构组装与接线指南
│   ├── 06_Quick_Start.md       ← 5 分钟快速上手
│   └── 07_API_Guide.md         ← API 密钥获取指南
│
├── hardware-manifest.json      ← 硬件、固件和复现路径清单
├── scripts/validate_project.py ← 自动校验清单和敏感配置
│
└── README.md                   ← 就是这个文件
```

---

## 🔌 硬件接线图

### 快速接线表

| ESP12F 引脚 | 接到哪里 | 注意事项 |
|-------------|---------|---------|
| GPIO0 (D3) | HLK-V20 TX | 语音模块的发送引脚 |
| GPIO2 (D4) | 按键 → GND | 启动时必须 HIGH |
| GPIO4 (D2) | OLED SDA | I2C 数据，需 4.7KΩ 上拉 |
| GPIO5 (D1) | OLED SCL | I2C 时钟，需 4.7KΩ 上拉 |
| GPIO14 (D5) | Servo 1 + OV2640 SCK | ⚠ 串联 1KΩ 与舵机共享 |
| GPIO12 (D6) | Servo 3 + OV2640 MISO | ⚠ 串联 1KΩ 与舵机共享 |
| GPIO13 (D7) | Servo 4 + OV2640 MOSI | ⚠ 串联 1KΩ 与舵机共享 |
| GPIO15 (D8) | OV2640 CS | ⚠ **必须** 10KΩ 下拉到 GND |
| GPIO16 (D0) | 扬声器 (三极管驱动) | 或改接 Servo 2（二选一） |
| A0 | 电池分压检测 | — |
| TX/RX | USB-TTL 调试口 | 烧录和串口调试 |

> ⚠ **最重要的两条规则：**
> 1. **GPIO15 必须接 10KΩ 下拉电阻到 GND** — 否则 ESP8266 无法启动
> 2. **OV2640 的 SCK/MISO/MOSI 与舵机共享时串联 1KΩ** — 防止信号冲突

完整接线图 → [Docs/05_Assembly_Guide.md](Docs/05_Assembly_Guide.md)

---

## 📚 文档索引

| 如果你想... | 看这个 |
|------------|--------|
| **机器狗送人了，教他怎么玩** | [使用说明书（给不懂技术的人）](Docs/08_Product_Manual.md) |
| **5 分钟跑起来** | [快速上手指南](Docs/06_Quick_Start.md) |
| **编译烧录代码** | [固件烧录指南](Docs/04_Firmware_Flashing.md) |
| **看懂/修改 PCB** | [硬件设计导入指南](Docs/01_Hardware_Guide.md) |
| **免费打样 PCB** | [PCB 打样指南](Docs/02_PCB_Fabrication.md) |
| **组装接线** | [结构组装与接线指南](Docs/05_Assembly_Guide.md) |
| **改 OLED 表情** | [图片转换指南](Docs/03_Image_Conversion.md) |
| **申请 API 密钥** | [API 密钥获取指南](Docs/07_API_Guide.md) |
| **所有引脚定义** | [PIN_WIRING.md](MindPaw_main/PIN_WIRING.md) |
| **从零复现固件 Demo** | [MindPaw_main/README.md](MindPaw_main/README.md) |
| **研究 AI Infra 和边缘-云 Agent** | [ai-infra/README.md](ai-infra/README.md) |
| **导入/修改/打样 PCB** | [SCH&PCB/README.md](SCH%26PCB/README.md) |

---

## 🌿 分支与版本

仓库当前有两条远程分支，分别承担不同角色：

| 分支 | 状态 | 说明 |
|---|---|---|
| **`main`** | ✅ 受保护候选（建议在 GitHub Settings → Branches 加规则） | 稳定发布线。当前是 [MindPaw 2.0](https://github.com/ace-trump-tech/MindPaw/releases/tag/v2.0.0)。 |
| **`feature/2.0-streaming-recon`** | ✅ 已合并进 `main`（merge commit `4900898`） | 2.0 感知层开发分支。代码已经在 `main`，可以安全删除。 |

### 推荐的 main 保护规则

GitHub 网页会提示 *"Your main branch isn't protected"*。建议在
**Settings → Branches → Add rule** 加：

- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging（至少勾上 `docs-and-manifest` + `gateway-tests` + `recon-tests` 三个 job）
- ✅ Do not allow force pushes
- ✅ Do not allow deletions
- ✅ Require linear history（可选；如果想保留 `--no-ff` merge commit 就**不要**勾这个）

### 清理已合并的 feature 分支

```bash
git push origin --delete feature/2.0-streaming-recon
git branch -d feature/2.0-streaming-recon       # 本地
```

### 发布历史

| Tag | Commit | 备注 |
|---|---|---|
| `v2.0.0` | `ac65e8c` | MindPaw 2.0 — 流式 3D 重建感知层 |
| (older) | — | MindPaw 1.x — 桌面狗 + 豆包对话 + 情感反应 |

详细 changelog 见 [`RELEASE_NOTES.md`](RELEASE_NOTES.md)。

---

## ❓ 常见问题

### 我不会编程，能做出这个吗？

如果你没有嵌入式开发经验，建议至少先了解 **Arduino 的基本用法**（点亮 LED、串口输出）。然后跟着文档一步步来，遇到问题可以在 GitHub 提 Issue。

### 一定要用嘉立创打样 PCB 吗？

不是。你也可以用**洞洞板（万用板）**手焊。PCB 文件只是更方便、更可靠。第一次做建议用手焊，成功后再打样。

### 一定要 3D 打印外壳吗？

不是。你也可以用纸板、亚克力、积木搭一个身体。3D 模型只是我设计的参考外形。

### 可以用 ESP32 代替吗？

**当然，而且推荐。** ESP32 引脚更多、内存更大、还有蓝牙。迁移方法：
1. `platformio.ini` 中改 `board = nodemcu-32s`
2. 引脚分配按 ESP32 重新调整
3. 大部分代码无需修改

### 语音模块一定要用 HLK-V20 吗？

如果你已经有 LD3320，也可以接（需要 5 个 SPI 引脚）。但 HLK-V20 只需要 1 个引脚，识别率更高，推荐用它。

### 为什么 GPIO15 要下拉到 GND？

这是 ESP8266 的硬件要求：GPIO15 在启动时如果为 HIGH，芯片会进入**测试模式**导致无法正常工作。10KΩ 电阻下拉确保启动时是 LOW。

---

## 🧰 维护与贡献

MindPaw 同时包含固件、真实硬件、3D 模型和可选 AI Gateway。为了让贡献可以复现，提交前请先阅读：

- [贡献指南](CONTRIBUTING.md)：变更范围、证据和人工验证要求
- [支持与排障](SUPPORT.md)：按固件、接线、PCB、Gateway 分流问题
- [安全策略](SECURITY.md)：物理执行器、API 密钥和漏洞报告
- [硬件清单](hardware-manifest.json)：固件、接线、原理图和模型的权威路径

Issue 不能只是一段无法验证的 AI 生成文本；作者必须亲自复现、提供日志或测量结果，并能回答维护者追问。AI 可以辅助检索、翻译和排版，但不能替代硬件安全审查和实验验证。

仓库的 `Quality`、`Firmware build` 和 `Link check` 工作流会自动检查项目清单、Gateway 契约、固件编译和文档链接。涉及舵机、供电、引脚或动作协议的改动必须附上断电措施和兼容性说明。

---

## 📜 许可证

- **软件代码**（`MindPaw_main/src/`）：MIT License
- **硬件设计**（`SCH&PCB/`）：CC BY-NC 4.0
- **3D 模型**（`3Dmodel/`）：CC BY-NC 4.0
- **文档**（`Docs/` 和 `README.md`）：CC BY 4.0

简单说：代码随便用，硬件和 3D 模型可以个人使用、修改，但不要商用。

---

<p align="center">
  <strong>Made with ❤️ and a lot of coffee</strong>
  <br>
  <sub>如果你也做了这个项目，欢迎在 GitHub 上 @ 我！</sub>
</p>
```
