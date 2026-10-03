# 小智 xiaozhi-esp32 详细资料

小智的参考价值在于可适配多种硬件的语音交互与通信架构。它没有唯一外观，可以服务桌面伙伴、机器狗或其他角色。

[返回项目总览](<../00_%E9%A1%B9%E7%9B%AE%E6%80%BB%E8%A7%88.md>) · [配套生态与代码导读](<%E9%85%8D%E5%A5%97%E7%94%9F%E6%80%81%E4%B8%8E%E4%BB%A3%E7%A0%81%E5%AF%BC%E8%AF%BB.md>) · [逐仓阅读记录](<%E4%BB%93%E5%BA%93%E9%98%85%E8%AF%BB%E8%AE%B0%E5%BD%95.md>) · [来源与固定版本](<%E6%9D%A5%E6%BA%90%E4%B8%8E%E7%89%88%E6%9C%AC.json>)

## 已核对的硬件与能力

程序按应用状态、音频、显示、协议和板级适配组织；设备能力通过 MCP 工具接口提供。唤醒、摄像头等能力依板型与构建配置而定，离线唤醒不等于离线完成大模型对话。

对话和控制配套现状：语音底座生态较完整；云端、私有后端与模型运行环境需另配置。

设备录音和唤醒 → Opus 与网络协议 → 服务端 ASR、LLM、TTS → 设备播音和表情；模型可通过 MCP 调用板级工具。

## 外观代码与产品思路借鉴

以下为面向后续自研与课程的分析建议。

- 程序架构：把语音、网络和显示做成共享基础，更换机器人外观时主要调整板级配置和动作层。
- 交互设计：将监听、思考、说话与闲置状态映射到不同表情和动作，让孩子知道机器人正在做什么。
- 执行方式：给模型提供有限、可校验的动作工具，例如点头或挥手；动作层检查参数与时间，再控制执行器。

## 本地资料组成

| 仓库入口 | 配套角色 | 分支 | 固定提交 |
|---|---|---|---|
| [100askTeam/xiaozhi-linux](<%E4%BB%93%E5%BA%93/100askTeam__xiaozhi-linux>) | README 列出的 Linux 客户端 | `master` | `9eff7f419122` |
| [78/xiaozhi-assets-generator](<%E4%BB%93%E5%BA%93/78__xiaozhi-assets-generator>) | 同作者角色资产打包工具 | `main` | `55517b40d724` |
| [78/xiaozhi-esp32](<%E4%BB%93%E5%BA%93/78__xiaozhi-esp32>) | 主项目 | `main` | `d395220a83fb` |
| [78/xiaozhi-sf32](<%E4%BB%93%E5%BA%93/78__xiaozhi-sf32>) | 同作者 SiFli 芯片客户端 | `main` | `1d3ef641ace4` |
| [AnimeAIChat/xiaozhi-server-go](<%E4%BB%93%E5%BA%93/AnimeAIChat__xiaozhi-server-go>) | README 列出的 Go 自建语音后端 | `main` | `0b1575cb5d43` |
| [QuecPython/solution-xiaozhiAI](<%E4%BB%93%E5%BA%93/QuecPython__solution-xiaozhiAI>) | README 列出的 QuecPython 客户端 | `master` | `afc111a6425b` |
| [TOM88812/xiaozhi-android-client](<%E4%BB%93%E5%BA%93/TOM88812__xiaozhi-android-client>) | README 列出的 Android 客户端 | `main` | `30a0c80446a3` |
| [hackers365/asr_server](<%E4%BB%93%E5%BA%93/hackers365__asr_server__bac6c49b3b4a>) | Go 服务端固定版本的 ASR 子模块 | `pinned-commit` | `bac6c49b3b4a` |
| [hackers365/xiaozhi-esp32-server-golang](<%E4%BB%93%E5%BA%93/hackers365__xiaozhi-esp32-server-golang>) | README 列出的另一 Go 自建语音后端 | `main` | `21f1a2e71ff3` |
| [huangjunsen0406/py-xiaozhi](<%E4%BB%93%E5%BA%93/huangjunsen0406__py-xiaozhi>) | README 列出的电脑 Python 客户端 | `main` | `9bfc807d368c` |
| [joey-zhou/xiaozhi-esp32-server-java](<%E4%BB%93%E5%BA%93/joey-zhou__xiaozhi-esp32-server-java>) | README 列出的 Java 自建语音后端 | `main` | `b2ff4d316ba6` |
| [xinnan-tech/xiaozhi-esp32-server](<%E4%BB%93%E5%BA%93/xinnan-tech__xiaozhi-esp32-server>) | README 列出的 Python 自建语音后端 | `main` | `87c6df77b022` |

## 开发试验建议

先在明确支持的开发板上调通语音和状态显示，再增加一个动作工具；验证断网、重复调用及恢复后的行为。

先用电脑客户端和一个后端跑通语音，再拿一块明确型号的音频板验证；最后将挥手、点头、行走等动作注册为有参数约束的工具。课堂多设备场景另测连接数量、音频打断和重连，作者宣传的性能数字不当作我们的验收结果。

## 已知限制和待补资料

所查当前说明要求 ESP-IDF 6.0.1 或以上，旧教程环境不能直接套用。客户端、后端服务、模型和音色分别核查；本次未验证云服务费用、账号条件或课堂并发。

源码存在、说明中的功能、作者的测试和本次真机验证是不同状态。本次完成资料核查和静态阅读，未编译固件、训练模型或测试实物。

## 许可记录

本仓库 MIT，保留版权与许可。第三方后端、音频及图像资源、外壳与硬件资料各自登记来源。

每个配套仓库单独保留许可证，具体文件、模型、音色和素材声明优先。各仓库阅读记录提供原许可文件入口。

## 原始来源

- [原项目](https://github.com/78/xiaozhi-esp32)
- [中文说明](https://github.com/78/xiaozhi-esp32/blob/main/README_zh.md)
- [许可](https://github.com/78/xiaozhi-esp32/blob/main/LICENSE)

整理日期为 2026-10-02 香港时间。源码版本以本夹来源与版本记录为准，作者历史成本不是当前香港交付预算。

## 可复用能力索引

表情、动作、库与真实调用入口已另存能力库；原环境和移植要求分别记录。

- [E07 小智 LCD 静态图与 GIF 表情播放器](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%A1%A8%E6%83%85%E6%98%BE%E7%A4%BA/E07_%E5%B0%8F%E6%99%BA%20LCD%20%E9%9D%99%E6%80%81%E5%9B%BE%E4%B8%8E%20GIF%20%E8%A1%A8%E6%83%85%E6%92%AD%E6%94%BE%E5%99%A8.md>)
- [E10 Otto 的 21 个 GIF 表情资源](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%A1%A8%E6%83%85%E6%98%BE%E7%A4%BA/E10_Otto%20%E7%9A%84%2021%20%E4%B8%AA%20GIF%20%E8%A1%A8%E6%83%85%E8%B5%84%E6%BA%90.md>)
- [I05 小智听、说、待机与 emotion 事件调度](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/03_%E4%BA%A4%E4%BA%92%E7%8A%B6%E6%80%81%E4%B8%8E%E8%B0%83%E5%BA%A6/I05_%E5%B0%8F%E6%99%BA%E5%90%AC%E3%80%81%E8%AF%B4%E3%80%81%E5%BE%85%E6%9C%BA%E4%B8%8E%20emotion%20%E4%BA%8B%E4%BB%B6%E8%B0%83%E5%BA%A6.md>)
- [A02 小智资源打包与主题版本配套](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/05_%E5%AA%92%E4%BD%93%E4%B8%8E%E8%B5%84%E6%BA%90/A02_%E5%B0%8F%E6%99%BA%E8%B5%84%E6%BA%90%E6%89%93%E5%8C%85%E4%B8%8E%E4%B8%BB%E9%A2%98%E7%89%88%E6%9C%AC%E9%85%8D%E5%A5%97.md>)

[库与版本](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/%E5%BA%93%E4%B8%8E%E4%BE%9D%E8%B5%96%E6%B8%85%E5%8D%95.md>) · [调用示例与移植路线](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
