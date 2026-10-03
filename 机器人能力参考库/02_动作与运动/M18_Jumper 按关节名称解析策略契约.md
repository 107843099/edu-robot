# M18 Jumper 按关节名称解析策略契约

复用等级：**需要移植或配套运行环境**。硬件：Jumper螃蟹机器人＋对应部署主机。语言：Rust/Python。

关联项目：[14 Jumper螃蟹机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/14_Jumper%E8%9E%83%E8%9F%B9%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：22关节、20关节、layout.json、模型契约、RKNN。依赖：Rust FSM、serde、ONNX/RKNN导出资源。

## 怎么实现

导出的 layout.json 定义观测/动作关节顺序、默认姿态、尺度、控制频率、限位和参考轨迹。Contract::load/from_str 按 joint_names 映射到实际总线次序，校验缺失关节、维度、home、限位完整性；原任务可有20维观测与22条线关节。

## 如何调用

Contract::load(path,&joint_names) 生成 obs_wire_idx/action_wire_idx，按返回映射构造输入和执行输出。若 layout 声明 reference，还需 attach_reference 及配套轨迹，不能仅载入权重。

## 移植与提取范围

值得借“模型与机械的显式契约”。新项目先建立命名关节配置和版本化资源包，再做适配；不能按数组索引硬拼，夹爪等额外关节会造成偏移。

## 限制与核对点

任务目录是训练环境、奖励和资源配置；不是直接供 C3 调用的 dance()。导出工具、模型、运行时和硬件全部匹配才可执行；本次没做训练或实体跳跃。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [layout.rs](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/14_Jumper%E8%9E%83%E8%9F%B9%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/KingKongRobotics__jumper/deploy/fsm/src/layout.rs>)：`pub struct Layout`，L130–L160。 [上游固定提交](https://github.com/KingKongRobotics/jumper/blob/7d3cc4bebd1efe951e0adc38c053d417260867c0/deploy/fsm/src/layout.rs#L130-L160)；提交 `7d3cc4bebd1efe951e0adc38c053d417260867c0`。
- [layout.rs](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/14_Jumper%E8%9E%83%E8%9F%B9%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/KingKongRobotics__jumper/deploy/fsm/src/layout.rs>)：`pub fn load`，L246–L276。 [上游固定提交](https://github.com/KingKongRobotics/jumper/blob/7d3cc4bebd1efe951e0adc38c053d417260867c0/deploy/fsm/src/layout.rs#L246-L276)；提交 `7d3cc4bebd1efe951e0adc38c053d417260867c0`。
- [layout.rs](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/14_Jumper%E8%9E%83%E8%9F%B9%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/KingKongRobotics__jumper/deploy/fsm/src/layout.rs>)：`pub fn attach_reference`，L399–L429。 [上游固定提交](https://github.com/KingKongRobotics/jumper/blob/7d3cc4bebd1efe951e0adc38c053d417260867c0/deploy/fsm/src/layout.rs#L399-L429)；提交 `7d3cc4bebd1efe951e0adc38c053d417260867c0`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
