# ElectronBot 类人桌面机器人 详细资料

圆脸、双臂与躯干动作带来较丰富的表现力，适合研究紧凑机构、舵机反馈和动作编辑。它是连接电脑的桌面机器人，不是自主双足行走平台。

[返回项目总览](<../00_%E9%A1%B9%E7%9B%AE%E6%80%BB%E8%A7%88.md>) · [配套生态与代码导读](<%E9%85%8D%E5%A5%97%E7%94%9F%E6%80%81%E4%B8%8E%E4%BB%A3%E7%A0%81%E5%AF%BC%E8%AF%BB.md>) · [逐仓阅读记录](<%E4%BB%93%E5%BA%93%E9%98%85%E8%AF%BB%E8%AE%B0%E5%BD%95.md>) · [来源与固定版本](<%E6%9D%A5%E6%BA%90%E4%B8%8E%E7%89%88%E6%9C%AC.json>)

## 已核对的硬件与能力

作者方案为 6 自由度，主板采用 STM32F405，包含圆屏、USB 通信与改造舵机。仓库分别提供电路、主控及舵机固件、SDK、Unity 工具和 CAD。

对话和控制配套现状：有 SDK、Unity 上位机、语音硬件与外设配套；完整 AI 对话仍需应用集成。

电脑 ElectronStudio 或应用 → USB SDK → STM32 主板 → 自定义反馈舵机和圆屏；语音扩展另提供 USB 音频硬件。

## 外观参考

![稚晖君 ElectronBot 外观参考  来源为原仓库](<%E5%9B%BE%E7%89%87/%E5%8F%82%E8%80%83%E5%9B%BE.jpg>)

稚晖君 ElectronBot 外观参考  来源为原仓库。原图出处见下方来源，图片作为研究资料留档，不能从代码许可推定照片与角色的独立授权。

## 外观代码与产品思路借鉴

以下为面向后续自研与课程的分析建议。

- 机械：研究紧凑手臂和舵机安装方式；将角度回传与控制协议作为进阶机电专题。
- 表现：把表情设计成进入、循环和退出阶段，让说话、等待与动作切换更连贯。
- 工具：参考从底层通信 SDK 到动画编辑器的分层，避免让每个角色程序重复处理硬件通信。

## 本地资料组成

| 仓库入口 | 配套角色 | 分支 | 固定提交 |
|---|---|---|---|
| [jinsonli/ElectronBot-Voice](<%E4%BB%93%E5%BA%93/jinsonli__ElectronBot-Voice>) | 主 README 指向的第三方语音扩展 | `main` | `d8cac34eb103` |
| [maker-community/ElectronBot-Peripheral](<%E4%BB%93%E5%BA%93/maker-community__ElectronBot-Peripheral>) | Otto 文档指向的 ElectronBot 外设开发 | `main` | `2f545c891c49` |
| [peng-zhihui/CycloidAcuratorNano](<%E4%BB%93%E5%BA%93/peng-zhihui__CycloidAcuratorNano>) | 同作者微型摆线减速器 | `main` | `d8fc82dedc05` |
| [peng-zhihui/Dummy-Robot](<%E4%BB%93%E5%BA%93/peng-zhihui__Dummy-Robot>) | 同作者机械臂参考 | `main` | `84453f1391c4` |
| [peng-zhihui/ElectronBot](<%E4%BB%93%E5%BA%93/peng-zhihui__ElectronBot>) | 主项目 | `main` | `819927015323` |
| [peng-zhihui/Peak](<%E4%BB%93%E5%BA%93/peng-zhihui__Peak>) | Dummy 子模块与图形界面参考 | `main` | `7605edc702c3` |
| [peng-zhihui/Peak](<%E4%BB%93%E5%BA%93/peng-zhihui__Peak__c7a90eda1068>) | Dummy 固定版本的 Peak 子模块 | `pinned-commit` | `c7a90eda1068` |
| [unlir/XDrive](<%E4%BB%93%E5%BA%93/unlir__XDrive>) | Dummy 配套步进电机驱动 | `master` | `e4aa58dee0e9` |

## 开发试验建议

先研究 USB 显示与一个舵机的独立控制，再实现短动作和表情联动；高阶阶段才验证整机机构。

先学习进入、循环、退出三段表情与动作编排接口；反馈舵机和 USB 音频作为高阶专题。新增对话先从电脑端串接，不把语音扩展板的存在当作自由问答实现。

## 已知限制和待补资料

定制舵机、紧凑打印和总线调试增加复刻难度；上位机说明偏 Windows。语音扩展来自第三方，不能写成本体已经具备的独立 AI 能力。

源码存在、说明中的功能、作者的测试和本次真机验证是不同状态。本次完成资料核查和静态阅读，未编译固件、训练模型或测试实物。

## 许可记录

根 LICENSE 为 GPL-3.0。分发适用的修改或衍生软件时需处理对应源码等义务；角色造型与第三方素材的权利另行判断。

每个配套仓库单独保留许可证，具体文件、模型、音色和素材声明优先。各仓库阅读记录提供原许可文件入口。

## 原始来源

- [项目及图片来源](https://github.com/peng-zhihui/ElectronBot)
- [许可](https://github.com/peng-zhihui/ElectronBot/blob/main/LICENSE)

整理日期为 2026-10-02 香港时间。源码版本以本夹来源与版本记录为准，作者历史成本不是当前香港交付预算。

## 可复用能力索引

表情、动作、库与真实调用入口已另存能力库；原环境和移植要求分别记录。

- [E11 ElectronBot USB 屏幕帧与媒体播放](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%A1%A8%E6%83%85%E6%98%BE%E7%A4%BA/E11_ElectronBot%20USB%20%E5%B1%8F%E5%B9%95%E5%B8%A7%E4%B8%8E%E5%AA%92%E4%BD%93%E6%92%AD%E6%94%BE.md>)
- [M14 ElectronBot 可用底层六关节接口](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/02_%E5%8A%A8%E4%BD%9C%E4%B8%8E%E8%BF%90%E5%8A%A8/M14_ElectronBot%20%E5%8F%AF%E7%94%A8%E5%BA%95%E5%B1%82%E5%85%AD%E5%85%B3%E8%8A%82%E6%8E%A5%E5%8F%A3.md>)
- [I07 停止、回中、保持和释放的语义对照](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/03_%E4%BA%A4%E4%BA%92%E7%8A%B6%E6%80%81%E4%B8%8E%E8%B0%83%E5%BA%A6/I07_%E5%81%9C%E6%AD%A2%E3%80%81%E5%9B%9E%E4%B8%AD%E3%80%81%E4%BF%9D%E6%8C%81%E5%92%8C%E9%87%8A%E6%94%BE%E7%9A%84%E8%AF%AD%E4%B9%89%E5%AF%B9%E7%85%A7.md>)

[库与版本](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/%E5%BA%93%E4%B8%8E%E4%BE%9D%E8%B5%96%E6%B8%85%E5%8D%95.md>) · [调用示例与移植路线](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
