# M07 AlbertMicro 四舵机步态与插值

复用等级：**需要移植或配套运行环境**。硬件：ESP32 Arduino＋4舵机＋SH1106。语言：C++。

关联项目：[05 AlbertMicro机器小狗](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/05_AlbertMicro%E6%9C%BA%E5%99%A8%E5%B0%8F%E7%8B%97/README.md>)。

检索词：四足、gait、正弦步态、俯卧撑、gallop。依赖：ESP32Servo、RoboEyes、ArduinoJson、BLE。

## 怎么实现

动作层对4个舵机插值移动，期间更新 RoboEyes；runGait 依时间相位驱动腿部周期动作，方向/侧移通过不同参数组合。俯卧撑、摇摆、奔跑是写好的动作函数，并联动 HAPPY/ANGRY 表情。

## 如何调用

原工程命令处理 WALK/BACK/LEFT/RIGHT、SL/SR、STOP、PUSHUPS、SWING、GALLOP 等。直接函数调用依赖原 servo/trim/姿态全局变量；先沿 setup 初始化后再使用。

## 移植与提取范围

可以参考“四个周期通道＋动作前后插值”的组织；新机器人的腿长/中心/方向需重新标定。同步动作应拆成可推进任务，保证 BLE 指令与显示持续被处理。

## 限制与核对点

原主体未找到整体许可证，不把相关 AlbertPro 或 RoboEyes 许可套上。STOP 是将模式设为 idle，不意味着 detach 或断电。本次静态阅读没有验证步态稳定性。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [AlbertMicro.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/05_AlbertMicro%E6%9C%BA%E5%99%A8%E5%B0%8F%E7%8B%97/%E4%BB%93%E5%BA%93/thinking0things__AlbertMicro/AlbertMicro.ino>)：`void moveUntilReachedAll`，L321–L351。 [上游固定提交](https://github.com/thinking0things/AlbertMicro/blob/8d0ae147e967c798469a551c1dc49da781fc5587/AlbertMicro.ino#L321-L351)；提交 `8d0ae147e967c798469a551c1dc49da781fc5587`。
- [AlbertMicro.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/05_AlbertMicro%E6%9C%BA%E5%99%A8%E5%B0%8F%E7%8B%97/%E4%BB%93%E5%BA%93/thinking0things__AlbertMicro/AlbertMicro.ino>)：`void runGait`，L423–L453。 [上游固定提交](https://github.com/thinking0things/AlbertMicro/blob/8d0ae147e967c798469a551c1dc49da781fc5587/AlbertMicro.ino#L423-L453)；提交 `8d0ae147e967c798469a551c1dc49da781fc5587`。
- [AlbertMicro.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/05_AlbertMicro%E6%9C%BA%E5%99%A8%E5%B0%8F%E7%8B%97/%E4%BB%93%E5%BA%93/thinking0things__AlbertMicro/AlbertMicro.ino>)：`void runPushups`，L377–L407。 [上游固定提交](https://github.com/thinking0things/AlbertMicro/blob/8d0ae147e967c798469a551c1dc49da781fc5587/AlbertMicro.ino#L377-L407)；提交 `8d0ae147e967c798469a551c1dc49da781fc5587`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
