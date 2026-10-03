# M20 TinyEngineer 舵机平滑、限位与释放输出

复用等级：**可单独提取；需接入驱动**。硬件：TinyEngineer C3＋PCA9685＋5舵机。语言：C++。

关联项目：[16 TinyEngineer桌面编程机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)、[15 小纸壳机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/15_%E5%B0%8F%E7%BA%B8%E5%A3%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：平滑动作、soft limit、deg/s、PCA9685、释放扭矩。依赖：ServoWrapper、settings、Adafruit_PWMServoDriver。

## 怎么实现

ServoWrapper 保存当前/目标角度，每次 update 根据时间差与 degree/sec 限制步长，再应用软件限位和 PWM 转换。normalized值映射到每关节配置区间；stop 仅将目标置为当前角。release 输出有独立逻辑与 PCA full-off/OE。

## 如何调用

servoAt(index).setTarget(degrees,speedDegS) 配 updateAllServos()；需要释放时 releaseAllServoOutputs()。setNormTarget 与 setTarget 单位不同，moveTo/servoMoveAllSmoothTo 存在同步路径，不能都叫非阻塞。

## 移植与提取范围

纸壳两舵机优先借目标/速度/update 和软限位，保留自己 pan/tilt 配置。改直接 ESP32Servo 输出时重写 writeAngle/release，而不移植全部5舵机配置。

## 限制与核对点

普通动作请求经过 I02 最短保持调度，不能作为紧急停止。释放 PWM 与电源断开、实体失去支撑分别评估；已有主机测试并未检查真实 PCA 接线。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [servo_wrapper.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/jamro__tiny-engineer/src/hardware/servo_wrapper.cpp>)：`void ServoWrapper::setTarget`，L148–L178。 [上游固定提交](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/hardware/servo_wrapper.cpp#L148-L178)；提交 `d71eb42a7abd98d81aae17472f35ba9d55ef5c89`。
- [servo_wrapper.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/jamro__tiny-engineer/src/hardware/servo_wrapper.cpp>)：`void ServoWrapper::update`，L181–L211。 [上游固定提交](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/hardware/servo_wrapper.cpp#L181-L211)；提交 `d71eb42a7abd98d81aae17472f35ba9d55ef5c89`。
- [servo_wrapper.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/jamro__tiny-engineer/src/hardware/servo_wrapper.cpp>)：`void releaseAllServoOutputs`，L239–L269。 [上游固定提交](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/hardware/servo_wrapper.cpp#L239-L269)；提交 `d71eb42a7abd98d81aae17472f35ba9d55ef5c89`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
