# XGO-Duck 赛博鸭子 详细资料

鸭形双足和可动脖颈、头嘴提供鲜明表现力，可作为未来进阶运动项目。用户提供的是硬件仓，运行与训练代码在配套仓库。

[返回项目总览](<../00_%E9%A1%B9%E7%9B%AE%E6%80%BB%E8%A7%88.md>) · [配套生态与代码导读](<%E9%85%8D%E5%A5%97%E7%94%9F%E6%80%81%E4%B8%8E%E4%BB%A3%E7%A0%81%E5%AF%BC%E8%AF%BB.md>) · [逐仓阅读记录](<%E4%BB%93%E5%BA%93%E9%98%85%E8%AF%BB%E8%AE%B0%E5%BD%95.md>) · [来源与固定版本](<%E6%9D%A5%E6%BA%90%E4%B8%8E%E7%89%88%E6%9C%AC.json>)

## 已核对的硬件与能力

Arduino UNO Q，Linux 与 STM32 分工；15 个总线舵机，其中腿部 10、头颈 4、嘴 1。硬件仓提供打印结构、PCB 源文件、BOM 和装配指南，项目明确继承 Microduck 上游。

对话和控制配套现状：硬件、运行与训练配套明确；鸭子主链未看到通用语音聊天实现。

训练电脑的 MuJoCo 与 PPO → ONNX → UNO Q Linux 策略与网页 → Arduino Bridge → STM32 舵机及 IMU；嘴部另控制。

## 外观参考

![LuwuDynamics XGO-Duck 原型实物图  来源为硬件仓](<%E5%9B%BE%E7%89%87/%E5%8F%82%E8%80%83%E5%9B%BE.png>)

LuwuDynamics XGO-Duck 原型实物图  来源为硬件仓。原图出处见下方来源，图片作为研究资料留档，不能从代码许可推定照片与角色的独立授权。

## 外观代码与产品思路借鉴

以下为面向后续自研与课程的分析建议。

- 角色表达：把脖子、头和嘴的表现与行走分开，可以先验证固定底座上的鸭头互动。
- 控制结构：参考 Linux 处理策略、MCU 处理执行器的分工，保留底层状态与命令边界。
- 工程工具：独立舵机编号、零位校准与传感反馈记录，适合后续多关节平台的调试流程。

## 本地资料组成

| 仓库入口 | 配套角色 | 分支 | 固定提交 |
|---|---|---|---|
| [LuwuDynamics/rig_omni](<%E4%BB%93%E5%BA%93/LuwuDynamics__rig_omni>) | 同组织多形态固件参考 | `main` | `c2b42cd73ef6` |
| [LuwuDynamics/xgoduck_hardware](<%E4%BB%93%E5%BA%93/LuwuDynamics__xgoduck_hardware>) | 主项目硬件 | `master` | `703bfd274071` |
| [LuwuDynamics/xgoduck_rl](<%E4%BB%93%E5%BA%93/LuwuDynamics__xgoduck_rl>) | 训练与策略导出配套 | `main` | `326d77a11228` |
| [LuwuDynamics/xgoduck_runtime_arduino](<%E4%BB%93%E5%BA%93/LuwuDynamics__xgoduck_runtime_arduino>) | 执行器与策略运行配套 | `master` | `8cdbbd84710d` |
| [pollen-robotics/microduck](<%E4%BB%93%E5%BA%93/pollen-robotics__microduck>) | 鸭子硬件与运行时上游 | `main` | `1fa84386f078` |
| [pollen-robotics/microduck_rl](<%E4%BB%93%E5%BA%93/pollen-robotics__microduck_rl>) | 鸭子训练上游 | `develop` | `8d0db74916a4` |

## 开发试验建议

先核对打印与电气材料，做单舵机和头颈原型；准备腿部运动时，再核对模型参数、策略与实物机构。

优先研究关节映射、执行器模型和仿真到实机的契约。整机复现先逐个设 ID、固定零位、支撑下测回传，再验证默认姿态；若以后加对话，采用独立高层指令接口，不让语言模型输出每周期关节角。

## 已知限制和待补资料

打印参数、部分电池定义和复刻验证仍有待完善项。硬件仓不含完整运行程序，仿真策略也不能直接证明真机稳定行走。

源码存在、说明中的功能、作者的测试和本次真机验证是不同状态。本次完成资料核查和静态阅读，未编译固件、训练模型或测试实物。

## 许可记录

硬件 LICENSING.md 明确尚无最终顶层许可证，复制范围需确认；运行仓未识别根许可，RL 仓为 Apache-2.0，仍需保留上游范围。

每个配套仓库单独保留许可证，具体文件、模型、音色和素材声明优先。各仓库阅读记录提供原许可文件入口。

## 原始来源

- [硬件项目及图片](https://github.com/LuwuDynamics/xgoduck_hardware)
- [许可现状](https://github.com/LuwuDynamics/xgoduck_hardware/blob/master/LICENSING.md)
- [上游记录](https://github.com/LuwuDynamics/xgoduck_hardware/blob/master/UPSTREAM.md)

整理日期为 2026-10-02 香港时间。源码版本以本夹来源与版本记录为准，作者历史成本不是当前香港交付预算。
