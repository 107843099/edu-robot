# M04 曼波 GitHub 非阻塞 ActionTask

复用等级：**可单独提取；需接入驱动**。硬件：STM32F103＋4舵机；GitHub 版本。语言：C。

关联项目：[02 曼波小狗](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/02_%E6%9B%BC%E6%B3%A2%E5%B0%8F%E7%8B%97/README.md>)。

检索词：动作队列、非阻塞、deadline、四舵机、抢占。依赖：ActionTask、Servo驱动、毫秒时钟。

## 怎么实现

动作脚本为 PoseStep 表：4 个 uint8 角度和 uint16 持续毫秒。任务实例保存脚本、步序和 deadline；Run(now_ms) 到期才应用下一步。HandleCommand 将字符指令映射到命名动作，避免每一步长 Delay 占住主循环。

## 如何调用

初始化舵机后 ActionTask_Init()；ActionTask_RequestMotion(ACTION_HELLO)，在主循环持续 ActionTask_Run(now_ms)。AbortToSafeStop() 让四个舵机回 90° 并清状态，不等于停止 PWM。动作名见预设清单。

## 移植与提取范围

纸壳可借时间驱动结构，把四角度表改为 pan/tilt 两通道。保持 tick 单调、正确处理 uint32 时间差及抢占策略；显示和串口仍在主循环刷新。

## 限制与核对点

这是 GitHub 中已有改进，不能反推本地收到的两个 HEX 对应此版本。MIT 范围仅能据 GitHub 项目声明判断，本地包未明确许可另记。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [ActionTask.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/02_%E6%9B%BC%E6%B3%A2%E5%B0%8F%E7%8B%97/%E4%BB%93%E5%BA%93/RussellCooper-DJZ__manbo-robot-dog/User/ActionTask.h>)：`ActionTask_RequestMotion`，L33–L39。 [上游固定提交](https://github.com/RussellCooper-DJZ/manbo-robot-dog/blob/9a3d315cfe50a62d8e6221cccf2aea696f96aedc/User/ActionTask.h#L33-L39)；提交 `9a3d315cfe50a62d8e6221cccf2aea696f96aedc`。
- [ActionTask.c](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/02_%E6%9B%BC%E6%B3%A2%E5%B0%8F%E7%8B%97/%E4%BB%93%E5%BA%93/RussellCooper-DJZ__manbo-robot-dog/User/ActionTask.c>)：`void ActionTask_Run`，L346–L376。 [上游固定提交](https://github.com/RussellCooper-DJZ/manbo-robot-dog/blob/9a3d315cfe50a62d8e6221cccf2aea696f96aedc/User/ActionTask.c#L346-L376)；提交 `9a3d315cfe50a62d8e6221cccf2aea696f96aedc`。
- [ActionTask.c](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/02_%E6%9B%BC%E6%B3%A2%E5%B0%8F%E7%8B%97/%E4%BB%93%E5%BA%93/RussellCooper-DJZ__manbo-robot-dog/User/ActionTask.c>)：`void ActionTask_AbortToSafeStop`，L451–L473。 [上游固定提交](https://github.com/RussellCooper-DJZ/manbo-robot-dog/blob/9a3d315cfe50a62d8e6221cccf2aea696f96aedc/User/ActionTask.c#L451-L473)；提交 `9a3d315cfe50a62d8e6221cccf2aea696f96aedc`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
