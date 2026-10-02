# Sesame 芝麻机器人 详细资料

八舵机四足、OLED 表情和同作者对话应用构成完整的互动参考生态。动作、表情由机器人执行，收音、模型与播音由电脑侧配套承担。

[返回项目总览](<../00_%E9%A1%B9%E7%9B%AE%E6%80%BB%E8%A7%88.md>) · [配套生态与代码导读](<%E9%85%8D%E5%A5%97%E7%94%9F%E6%80%81%E4%B8%8E%E4%BB%A3%E7%A0%81%E5%AF%BC%E8%AF%BB.md>) · [逐仓阅读记录](<%E4%BB%93%E5%BA%93%E9%98%85%E8%AF%BB%E8%AE%B0%E5%BD%95.md>) · [来源与固定版本](<%E6%9D%A5%E6%BA%90%E4%B8%8E%E7%89%88%E6%9C%AC.json>)

## 已核对的硬件与能力

8 个舵机，每腿 2 个自由度；BOM 列 MG90S 与 SSD1306 OLED。手工搭建和分线板版本的 ESP32 型号不同，须按硬件版本选固件。资料含固件、CAD、材料表和姿势编辑器。

对话和控制配套现状：已有同作者对话配套，收音、模型和播音在电脑侧。

电脑麦克风 → SpeechRecognition 和 Google ASR → Gemini 或本地兼容接口 → 结构化动作与回复 → HTTP → ESP32 舵机和 OLED；语音由电脑侧 TTS 输出。

## 外观参考

![Dorian Todd 项目实物图  来源为仓库 README](<%E5%9B%BE%E7%89%87/%E5%8F%82%E8%80%83%E5%9B%BE.png>)

Dorian Todd 项目实物图  来源为仓库 README。原图出处见下方来源，图片作为研究资料留档，不能从代码许可推定照片与角色的独立授权。

## 外观代码与产品思路借鉴

以下为面向后续自研与课程的分析建议。

- 外观与结构：低矮身体、前置表情屏和外露腿部，便于观察动作；我们可重新设计头壳与装饰，让机构共用而角色不同。
- 代码与工具：动作序列、表情位图和网页控制分开组织。Sesame Studio 用姿势与关键帧生成 C++，很适合转成可视化动作课程。
- 交互思路：先定义有限的动作名称，再把按钮、语音或传感输入映射到同一动作接口。

## 本地资料组成

| 仓库入口 | 配套角色 | 分支 | 固定提交 |
|---|---|---|---|
| [dorianborian/sesame-companion-app](<%E4%BB%93%E5%BA%93/dorianborian__sesame-companion-app>) | 同作者对话与桌面控制配套 | `main` | `86f82c137b99` |
| [dorianborian/sesame-robot](<%E4%BB%93%E5%BA%93/dorianborian__sesame-robot>) | 主项目 | `main` | `d106cbc8e158` |
| [lukehollis/sesame-ml](<%E4%BB%93%E5%BA%93/lukehollis__sesame-ml>) | 主 README 指向的第三方机器学习配套 | `main` | `a3910f67b4ae` |

## 开发试验建议

先复现站立、挥手与表情切换，再让学生改一个关键帧；记录中位校准、供电与实际动作偏差。

先用文字输入验证“挥手并回答”与纯表情请求，再打开电脑麦克风和 TTS；确认模型断网、非法动作和 STOP 的行为。机身自带麦克风、喇叭需要增加音频硬件和设备端实现，现有 Companion 可作为先期对话与动作联调原型。

## 已知限制和待补资料

抽查步行动作采用固定角度与延时，不能据此认定具备动态平衡或自主导航。麦克风、摄像头和 IMU 不属于所查核心 BOM 的标配。

源码存在、说明中的功能、作者的测试和本次真机验证是不同状态。本次完成资料核查和静态阅读，未编译固件、训练模型或测试实物。

## 许可记录

根目录 Apache-2.0；第三方 sesame-ml 为 Apache-2.0；同作者 Companion 未见根许可证，不能用主仓许可覆盖。作者材料价不作为当前交付预算。

每个配套仓库单独保留许可证，具体文件、模型、音色和素材声明优先。各仓库阅读记录提供原许可文件入口。

## 原始来源

- [项目与图片来源](https://github.com/dorianborian/sesame-robot)
- [材料表](https://github.com/dorianborian/sesame-robot/blob/main/hardware/bom/README.md)
- [许可](https://github.com/dorianborian/sesame-robot/blob/main/LICENSE)

整理日期为 2026-10-02 香港时间。源码版本以本夹来源与版本记录为准，作者历史成本不是当前香港交付预算。
