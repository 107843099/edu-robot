# M13 小智 Otto 六舵机与双臂动作

复用等级：**原环境可调用；新硬件需核对**。硬件：ESP-IDF Otto板型＋4腿/脚舵机＋可选2臂。语言：C++。

关联项目：[09 Otto闪猫侠机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：挥手、举手、害羞、广播体操、六舵机、动作序列。依赖：otto_movements、ESP-IDF、板型PWM。

## 怎么实现

OttoMovements 将基础四通道动作扩展到6通道，双臂 pin 可为 -1。双臂举起、挥手、风车、起飞、健身、问候、害羞与体操都有实际方法；controller 的动作任务和 MCP 注册负责排队。

## 如何调用

HandsUp、HandWave 等入口按头文件签名；远程统一 self.otto.action 的 action 参数调用。servo_sequences 支持 s/v/d 及振荡 a/o/ph/p/c；其中 ph 是度，会与经典 Oscillator 的弧度接口形成单位差异。

## 移植与提取范围

原 Otto 板型可用现成任务队列。若新纸壳只有两舵机，建立自己的 pan/tilt 名字到通道映射，不套 ll/rl/lf/rf/lh/rh。速度字段通常是动作周期毫秒，小值更快。

## 限制与核对点

Init 时可选手臂不等于实体都有6通道。README 举例可能出现超出文字约定的序列偏移，执行以代码约束为准；使用原有 stop 注册回调而非凭空假定 self.otto.home 独立工具存在。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [otto_movements.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/txp666__xiaozhi-esp32/main/boards/otto-robot/otto_movements.h>)：`void HandsUp`，L83–L113。 [上游固定提交](https://github.com/txp666/xiaozhi-esp32/blob/becc84f58908d96a8aaeae046dcd22e099aad7e9/main/boards/otto-robot/otto_movements.h#L83-L113)；提交 `becc84f58908d96a8aaeae046dcd22e099aad7e9`。
- [otto_movements.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/txp666__xiaozhi-esp32/main/boards/otto-robot/otto_movements.h>)：`void HandWave`，L85–L115。 [上游固定提交](https://github.com/txp666/xiaozhi-esp32/blob/becc84f58908d96a8aaeae046dcd22e099aad7e9/main/boards/otto-robot/otto_movements.h#L85-L115)；提交 `becc84f58908d96a8aaeae046dcd22e099aad7e9`。
- [otto_controller.cc](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/txp666__xiaozhi-esp32/main/boards/otto-robot/otto_controller.cc>)：`self.otto.servo_sequences`，L669–L699。 [上游固定提交](https://github.com/txp666/xiaozhi-esp32/blob/becc84f58908d96a8aaeae046dcd22e099aad7e9/main/boards/otto-robot/otto_controller.cc#L669-L699)；提交 `becc84f58908d96a8aaeae046dcd22e099aad7e9`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
