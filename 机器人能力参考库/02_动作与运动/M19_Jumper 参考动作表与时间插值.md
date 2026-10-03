# M19 Jumper 参考动作表与时间插值

复用等级：**可单独提取；需接入驱动**。硬件：Rust部署运行时＋配套轨迹JSON。语言：Rust。

关联项目：[14 Jumper螃蟹机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/14_Jumper%E8%9E%83%E8%9F%B9%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：参考轨迹、舞蹈、跳跃、录制动作、插值、q_cmd。依赖：Trajectory、ReferenceSpec、layout契约。

## 怎么实现

Trajectory 区分实际达到的 q 与控制命令 q_cmd，两者可拥有不同帧率和长度。parse 按关节名称重排并校验；q_at_into 线性插值，baseline_into 使用控制命令的采样时刻和提前量。finished 判定动作结束而非无限循环最后姿势。

## 如何调用

使用 ReferenceSpec 配套表调用 Trajectory::parse(spec,text,wire)；传相对 go 时间（秒）采样。q 的 rec_hz 与 q_cmd 的 control_hz 不得互换；相位和四元数采用各自处理方式。

## 移植与提取范围

可借录制动作格式用于未来桌面动作编辑器，但应建立更简单的两舵机表，保留关节名字、单位、时间和结束策略。复制 Rust组件需要整个契约依赖，不能只取一张 q 表。

## 限制与核对点

夹爪、参考残差和 go 事件由任务决定。原训练/部署的 dance、jump 标签并不保证新机器人具有对应技能；轨迹到实体的限位、重心与动力学仍需重新验证。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [trajectory.rs](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/14_Jumper%E8%9E%83%E8%9F%B9%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/KingKongRobotics__jumper/deploy/fsm/src/trajectory.rs>)：`pub fn parse`，L157–L187。 [上游固定提交](https://github.com/KingKongRobotics/jumper/blob/7d3cc4bebd1efe951e0adc38c053d417260867c0/deploy/fsm/src/trajectory.rs#L157-L187)；提交 `7d3cc4bebd1efe951e0adc38c053d417260867c0`。
- [trajectory.rs](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/14_Jumper%E8%9E%83%E8%9F%B9%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/KingKongRobotics__jumper/deploy/fsm/src/trajectory.rs>)：`pub fn q_at_into`，L306–L336。 [上游固定提交](https://github.com/KingKongRobotics/jumper/blob/7d3cc4bebd1efe951e0adc38c053d417260867c0/deploy/fsm/src/trajectory.rs#L306-L336)；提交 `7d3cc4bebd1efe951e0adc38c053d417260867c0`。
- [trajectory.rs](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/14_Jumper%E8%9E%83%E8%9F%B9%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/KingKongRobotics__jumper/deploy/fsm/src/trajectory.rs>)：`pub fn baseline_into`，L316–L346。 [上游固定提交](https://github.com/KingKongRobotics/jumper/blob/7d3cc4bebd1efe951e0adc38c053d417260867c0/deploy/fsm/src/trajectory.rs#L316-L346)；提交 `7d3cc4bebd1efe951e0adc38c053d417260867c0`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
