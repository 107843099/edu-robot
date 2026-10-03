# RookiDroid Hexapod 六足机器人 详细资料

一个固件支持多种六足造型，适合研究怎样通过结构参数、动作生成工具和校准流程支撑产品系列。

[返回项目总览](<../00_%E9%A1%B9%E7%9B%AE%E6%80%BB%E8%A7%88.md>) · [配套生态与代码导读](<%E9%85%8D%E5%A5%97%E7%94%9F%E6%80%81%E4%B8%8E%E4%BB%A3%E7%A0%81%E5%AF%BC%E8%AF%BB.md>) · [逐仓阅读记录](<%E4%BB%93%E5%BA%93%E9%98%85%E8%AF%BB%E8%AE%B0%E5%BD%95.md>) · [来源与固定版本](<%E6%9D%A5%E6%BA%90%E4%B8%8E%E7%89%88%E6%9C%AC.json>)

## 已核对的硬件与能力

Nougat、Mochi 和 Macaroon 三种 18 自由度机型，ESP32 与两个 PCA9685；不同机型的尺寸、舵机和供电配置分别记录。资料包含打印件、装配说明、共用固件和 Python 路径工具。

对话和控制配套现状：已有模拟器和实体遥控器配套；未看到作者的原生自由对话链路。

实体摇杆或 Hexapod Link → WiFi UDP 与姿态串流 → ESP32 的统一运动输出 → 18 个舵机；模拟器从机器人读取尺寸和配置。

## 外观参考

![Mochi 六足实物图  来源为 RookiDroid 机型说明](<%E5%9B%BE%E7%89%87/%E5%8F%82%E8%80%83%E5%9B%BE.jpg>)

Mochi 六足实物图  来源为 RookiDroid 机型说明。原图出处见下方来源，图片作为研究资料留档，不能从代码许可推定照片与角色的独立授权。

## 外观代码与产品思路借鉴

以下为面向后续自研与课程的分析建议。

- 外观与系列：Mochi 的圆顶与分色腿部形成角色；在自有外观中可以沿用按机型管理尺寸参数的方法。
- 算法与固件：由上位机生成运动路径，再由设备查表执行，把复杂计算和实时控制任务分开。
- 开发流程：网页校准、WiFi 姿态串流与设备配置读取，有利于比较虚拟姿态和真实动作。

## 本地资料组成

| 仓库入口 | 配套角色 | 分支 | 固定提交 |
|---|---|---|---|
| [mithi/hexapod-robot-simulator](<%E4%BB%93%E5%BA%93/mithi__hexapod-robot-simulator>) | Hexapod Link 的仿真上游 | `master` | `35d83a83880e` |
| [rookidroid/hexapod](<%E4%BB%93%E5%BA%93/rookidroid__hexapod>) | 主项目 | `main` | `2c51f9e3bf3f` |
| [rookidroid/hexapod-link](<%E4%BB%93%E5%BA%93/rookidroid__hexapod-link>) | 上位机与模拟器配套 | `master` | `0b4f709217f0` |
| [rookidroid/remote-arcade](<%E4%BB%93%E5%BA%93/rookidroid__remote-arcade>) | 实体遥控器配套 | `main` | `26b1c153b366` |

## 开发试验建议

先选一个机型和一套材料表，运行单腿轨迹、校准与停止；再测试完整步态和上位机掉线后的行为。

先只选 Mochi 或另一个机型，把模拟器尺寸与机器人的 /robot_config 对齐。无硬件先做正逆运动学演示，下一步加单关节串流与松手停止，再做全身步态。

## 已知限制和待补资料

18 舵机的峰值电流、间隙、校准与备件都要单独考虑。不同遥控模式需要协调输出控制；旧 Pico 固件已标为不维护。

源码存在、说明中的功能、作者的测试和本次真机验证是不同状态。本次完成资料核查和静态阅读，未编译固件、训练模型或测试实物。

## 许可记录

根 LICENSE 为 GPL-3.0；复用与分发按相应条款处理，配套上位机和遥控器另有自己的许可。

每个配套仓库单独保留许可证，具体文件、模型、音色和素材声明优先。各仓库阅读记录提供原许可文件入口。

## 原始来源

- [项目](https://github.com/rookidroid/hexapod)
- [Mochi 及图片来源](https://github.com/rookidroid/hexapod/blob/main/robots/mochi/README.md)
- [许可](https://github.com/rookidroid/hexapod/blob/main/LICENSE)

整理日期为 2026-10-02 香港时间。源码版本以本夹来源与版本记录为准，作者历史成本不是当前香港交付预算。

## 可复用能力索引

表情、动作、库与真实调用入口已另存能力库；原环境和移植要求分别记录。

- [M02 PCA9685 多通道舵机输出](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/02_%E5%8A%A8%E4%BD%9C%E4%B8%8E%E8%BF%90%E5%8A%A8/M02_PCA9685%20%E5%A4%9A%E9%80%9A%E9%81%93%E8%88%B5%E6%9C%BA%E8%BE%93%E5%87%BA.md>)
- [M11 RookiDroid LUT 与 UDP 实时姿态接管](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/02_%E5%8A%A8%E4%BD%9C%E4%B8%8E%E8%BF%90%E5%8A%A8/M11_RookiDroid%20LUT%20%E4%B8%8E%20UDP%20%E5%AE%9E%E6%97%B6%E5%A7%BF%E6%80%81%E6%8E%A5%E7%AE%A1.md>)

[库与版本](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/%E5%BA%93%E4%B8%8E%E4%BE%9D%E8%B5%96%E6%B8%85%E5%8D%95.md>) · [调用示例与移植路线](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%83%BD%E5%8A%9B%E5%8F%82%E8%80%83%E5%BA%93/%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
