# M11 RookiDroid LUT 与 UDP 实时姿态接管

复用等级：**需要移植或配套运行环境**。硬件：ESP32＋18舵机原构型。语言：Arduino C++。

关联项目：[07 RookiDroid六足机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/07_RookiDroid%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：六足、UDP、实时姿态、slew、超时、控制所有权。依赖：PCA9685、UDP协议、RealtimePose。

## 怎么实现

预置 LUT 动作与外部实时姿态不能同时拥有输出。enterRealtimeMode 保留当前姿态并切换控制来源，serviceRealtimePose 消费最新姿态包，按 slew 限制每次变化；超时或退出后返回 LUT standby。共享包通过临界区同步。

## 如何调用

使用匹配 protocol.h 与 robot_config 的客户端发送目标；输出单位按原 PWM tick 表处理。HexapodLinkDash 先读 /robot_config，再按返回几何映射；remote-arcade 是另外的遥控器端。

## 移植与提取范围

值得借鉴最新包覆盖、接管/归还和超时恢复模式。新舵机控制器需要重写角度到 tick 转换、包布局和限幅，不直接把18个 degree 写入原包。

## 限制与核对点

one-shot snap 可直接跳变，不能等同全部姿态都有平滑保障。固件 GPL 范围与 MIT 配套界面/遥控器范围分开记录，实际 timeout 常量见 config.h。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [realtime.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/07_RookiDroid%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/rookidroid__hexapod/software/hexapod_esp32/realtime.ino>)：`void enterRealtimeMode`，L31–L61。 [上游固定提交](https://github.com/rookidroid/hexapod/blob/2c51f9e3bf3f5dbbe600a2a24182aa3e9837c60c/software/hexapod_esp32/realtime.ino#L31-L61)；提交 `2c51f9e3bf3f5dbbe600a2a24182aa3e9837c60c`。
- [realtime.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/07_RookiDroid%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/rookidroid__hexapod/software/hexapod_esp32/realtime.ino>)：`void serviceRealtimePose`，L79–L109。 [上游固定提交](https://github.com/rookidroid/hexapod/blob/2c51f9e3bf3f5dbbe600a2a24182aa3e9837c60c/software/hexapod_esp32/realtime.ino#L79-L109)；提交 `2c51f9e3bf3f5dbbe600a2a24182aa3e9837c60c`。
- [realtime.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/07_RookiDroid%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/rookidroid__hexapod/software/hexapod_esp32/realtime.ino>)：`void exitRealtimeMode`，L56–L86。 [上游固定提交](https://github.com/rookidroid/hexapod/blob/2c51f9e3bf3f5dbbe600a2a24182aa3e9837c60c/software/hexapod_esp32/realtime.ino#L56-L86)；提交 `2c51f9e3bf3f5dbbe600a2a24182aa3e9837c60c`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
