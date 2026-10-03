# Stack-chan 桌面摇头机器人 详细资料

用表情屏与双轴头部动作表达注意、回应和情绪，是近期桌面机器人与学生创作工具的重要参考。原清单中的两条链接合并在此。

[返回项目总览](<../00_%E9%A1%B9%E7%9B%AE%E6%80%BB%E8%A7%88.md>) · [配套生态与代码导读](<%E9%85%8D%E5%A5%97%E7%94%9F%E6%80%81%E4%B8%8E%E4%BB%A3%E7%A0%81%E5%AF%BC%E8%AF%BB.md>) · [逐仓阅读记录](<%E4%BB%93%E5%BA%93%E9%98%85%E8%AF%BB%E8%AE%B0%E5%BD%95.md>) · [来源与固定版本](<%E6%9D%A5%E6%BA%90%E4%B8%8E%E7%89%88%E6%9C%AC.json>)

## 已核对的硬件与能力

M5Stack 体系，当前 develop 分支含 Moddable 固件、JavaScript／TypeScript MOD、浏览器烧录与编辑工具。v0、v1 和当前 M5StackChan CoreS3 的硬件配置应分别识别。

对话和控制配套现状：有主仓 MOD、社区 AI 固件及原作者 USB 对话配套。

MOD 和对话服务 → StackchanContext → 音频、脸和双轴头部；也有 Arduino AI 固件路线与 USB 外部计算路线。

## 外观参考

![Stack-chan v0 结构示例  与当前商品 CoreS3 配置不同](<%E5%9B%BE%E7%89%87/%E5%8F%82%E8%80%83%E5%9B%BE.jpg>)

Stack-chan v0 结构示例  与当前商品 CoreS3 配置不同。原图出处见下方来源，图片作为研究资料留档，不能从代码许可推定照片与角色的独立授权。

## 外观代码与产品思路借鉴

以下为面向后续自研与课程的分析建议。

- 表达方式：用注视、点头和动作节奏表达角色意图，适合在少量关节上验证互动体验。
- 软件结构：宿主固件提供 motion、face、audio 等能力，MOD 承载具体互动内容；可以参考这种分层开发不同课程任务。
- 学生工具：表情编辑、积木编辑和模拟器提供从设计到设备运行的流程参考，值得与现有 AI 创作平台对照。

## 本地资料组成

| 仓库入口 | 配套角色 | 分支 | 固定提交 |
|---|---|---|---|
| [VOICEVOX/voicevox_engine](<%E4%BB%93%E5%BA%93/VOICEVOX__voicevox_engine>) | ChatGPT MOD 示例配套语音合成服务 | `master` | `bfa930394709` |
| [meganetaaan/moddable-scservo](<%E4%BB%93%E5%BA%93/meganetaaan__moddable-scservo>) | 原作者串行舵机驱动 | `main` | `08c8ba164ae4` |
| [meganetaaan/simple-stt-server](<%E4%BB%93%E5%BA%93/meganetaaan__simple-stt-server>) | 示例使用的语音识别服务 | `master` | `0448f4edae27` |
| [meganetaaan/stack-chan-dock](<%E4%BB%93%E5%BA%93/meganetaaan__stack-chan-dock>) | 原作者充电底座 | `develop` | `20b212b18ec5` |
| [mongonta0716/stack-chan-tester](<%E4%BB%93%E5%BA%93/mongonta0716__stack-chan-tester>) | 社区舵机与板卡测试工具 | `main` | `0f3a7fc1013a` |
| [robo8080/AI_StackChan2](<%E4%BB%93%E5%BA%93/robo8080__AI_StackChan2>) | 主 README 指向的社区语音 AI 实现 | `main` | `3022de6ab233` |
| [robo8080/AI_StackChan2_README](<%E4%BB%93%E5%BA%93/robo8080__AI_StackChan2_README>) | AI StackChan2 使用说明配套 | `main` | `19e395d9fa64` |
| [stack-chan/m5stack-avatar](<%E4%BB%93%E5%BA%93/stack-chan__m5stack-avatar>) | 同组织表情渲染库 | `master` | `7a90083edd9b` |
| [stack-chan/stack-chan](<%E4%BB%93%E5%BA%93/stack-chan__stack-chan>) | 主项目 | `develop` | `fe7be1005d2c` |

## 开发试验建议

固定一种支持的硬件和固件版本，运行一个 MOD，再修改触发、表情与动作；比较屏幕预览和真机表现。

首轮固定一个 CoreS3 或 DIY 硬件版本，选择 MOD、Arduino AI 或 USB 三者之一跑通。后续借鉴双轴注视、讲话节奏、表情同步和插件隔离，避免同时承担步态开发。

## 已知限制和待补资料

当前默认分支为 develop，API 会变化。SG90、XL330 与商品套装不可按同一材料表采购；烧录社区固件会替换出厂固件。

源码存在、说明中的功能、作者的测试和本次真机验证是不同状态。本次完成资料核查和静态阅读，未编译固件、训练模型或测试实物。

## 许可记录

仓库 Apache-2.0；角色衍生另有 GUIDELINE，保留作者与来源信息，并分别核对代码、结构与角色的使用条件。

每个配套仓库单独保留许可证，具体文件、模型、音色和素材声明优先。各仓库阅读记录提供原许可文件入口。

## 原始来源

- [项目](https://github.com/stack-chan/stack-chan)
- [图片及 v0 结构](https://github.com/stack-chan/stack-chan/blob/develop/case/README.md)
- [许可](https://github.com/stack-chan/stack-chan/blob/develop/LICENSE)
- [角色指南](https://github.com/stack-chan/stack-chan/blob/develop/GUIDELINE.md)

整理日期为 2026-10-02 香港时间。源码版本以本夹来源与版本记录为准，作者历史成本不是当前香港交付预算。

## 可复用能力索引

表情、动作、库与真实调用入口已另存能力库；原环境和移植要求分别记录。

- [E05 M5Stack Avatar 情绪、嘴巴与眼睛参数](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%A1%A8%E6%83%85%E6%98%BE%E7%A4%BA/E05_M5Stack%20Avatar%20%E6%83%85%E7%BB%AA%E3%80%81%E5%98%B4%E5%B7%B4%E4%B8%8E%E7%9C%BC%E7%9D%9B%E5%8F%82%E6%95%B0.md>)
- [E06 Stack-chan Moddable 面部状态与皮肤](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%A1%A8%E6%83%85%E6%98%BE%E7%A4%BA/E06_Stack-chan%20Moddable%20%E9%9D%A2%E9%83%A8%E7%8A%B6%E6%80%81%E4%B8%8E%E7%9A%AE%E8%82%A4.md>)
- [M08 Stack-chan 注视、避视与头部姿态](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/02_%E5%8A%A8%E4%BD%9C%E4%B8%8E%E8%BF%90%E5%8A%A8/M08_Stack-chan%20%E6%B3%A8%E8%A7%86%E3%80%81%E9%81%BF%E8%A7%86%E4%B8%8E%E5%A4%B4%E9%83%A8%E5%A7%BF%E6%80%81.md>)
- [I03 M5Avatar 音量驱动嘴巴开合](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/03_%E4%BA%A4%E4%BA%92%E7%8A%B6%E6%80%81%E4%B8%8E%E8%B0%83%E5%BA%A6/I03_M5Avatar%20%E9%9F%B3%E9%87%8F%E9%A9%B1%E5%8A%A8%E5%98%B4%E5%B7%B4%E5%BC%80%E5%90%88.md>)

[库与版本](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/%E5%BA%93%E4%B8%8E%E4%BE%9D%E8%B5%96%E6%B8%85%E5%8D%95.md>) · [调用示例与移植路线](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
