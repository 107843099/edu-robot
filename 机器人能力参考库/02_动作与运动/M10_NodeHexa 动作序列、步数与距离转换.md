# M10 NodeHexa 动作序列、步数与距离转换

复用等级：**原环境可调用；新硬件需核对**。硬件：NodeHexa ESP32 固件。语言：C++。

关联项目：[06 NodeHexa六足机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/06_NodeHexa%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：动作队列、六足步态、距离、角度、cycles、8队列。依赖：MotionController、MovementMetrics、Robot。

## 怎么实现

Action 保存 mode、unit、value、speed、sequenceId；队列容量8。控制器根据 tick 估算周期完成度，Cycles/Steps/Distance/Angle 统一换算成目标周期数，结束时恢复原速度。Continuous 没有固定周期终点。

## 如何调用

enqueue(action)、enqueueSequence(...) 与 onLoopTick(elapsedMs) 配套。Action 单位 Distance 为米、Angle 为度；speed 要落在原 config 允许范围。clear() 清队列及活跃状态，具体最终姿态由原 Robot 行为决定。

## 移植与提取范围

可借“语义动作→单位转换→调度”的模型；移植到新底盘必须重新估计每周期距离/转角和时间，不把模型估算当编码器测距。固定8容量需处理 enqueue 失败。

## 限制与核对点

Distance/Angle 是依据 movement metrics 的开环换算，没有真实里程反馈保证。动作队列也不提供语言识别，需要串口/网络适配接入。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [motion_controller.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/06_NodeHexa%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/ViolinLee__NodeHexa/firmware/src/motion_controller.h>)：`class MotionController`，L31–L61。 [上游固定提交](https://github.com/ViolinLee/NodeHexa/blob/ba844a107de8dbb95bba51c2d5e870928d72cbd9/firmware/src/motion_controller.h#L31-L61)；提交 `ba844a107de8dbb95bba51c2d5e870928d72cbd9`。
- [motion_controller.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/06_NodeHexa%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/ViolinLee__NodeHexa/firmware/src/motion_controller.cpp>)：`MotionController::convertToCycles`，L158–L188。 [上游固定提交](https://github.com/ViolinLee/NodeHexa/blob/ba844a107de8dbb95bba51c2d5e870928d72cbd9/firmware/src/motion_controller.cpp#L158-L188)；提交 `ba844a107de8dbb95bba51c2d5e870928d72cbd9`。
- [motion_controller.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/06_NodeHexa%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/ViolinLee__NodeHexa/firmware/src/motion_controller.cpp>)：`MotionController::clear`，L58–L88。 [上游固定提交](https://github.com/ViolinLee/NodeHexa/blob/ba844a107de8dbb95bba51c2d5e870928d72cbd9/firmware/src/motion_controller.cpp#L58-L88)；提交 `ba844a107de8dbb95bba51c2d5e870928d72cbd9`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
