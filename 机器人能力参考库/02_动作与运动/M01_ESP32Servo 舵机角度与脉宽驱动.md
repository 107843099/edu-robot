# M01 ESP32Servo 舵机角度与脉宽驱动

复用等级：**可单独提取；需接入驱动**。硬件：ESP32 Arduino；芯片与 core 版本影响 PWM 后端。语言：C++。

关联项目：[01 芝麻机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)、[05 AlbertMicro机器小狗](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/05_AlbertMicro%E6%9C%BA%E5%99%A8%E5%B0%8F%E7%8B%97/README.md>)、[15 小纸壳机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/15_%E5%B0%8F%E7%BA%B8%E5%A3%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：舵机、PWM、角度、微秒、ESP32、detach。依赖：ESP32Servo、Arduino-ESP32。

## 怎么实现

Servo 把角度映射为脉宽，再用 ESP32 PWM 外设持续输出。attach 提供 pin 和可选微秒上下限，write 写角度，writeMicroseconds 直接给脉宽；setPeriodHertz 配周期。芝麻额外加 trim、0..180 限幅和每次 20ms 等待。

## 如何调用

在匹配 Arduino core 中 include <ESP32Servo.h>，Servo 对象 setPeriodHertz(50)、attach(pin,minUs,maxUs)、write(degrees)。detach() 是停止该 PWM 通道；write(90) 是目标角度，二者不同。

## 移植与提取范围

两舵机纸壳方案可以单独使用，先确认 GPIO、舵机中心、脉宽范围、安装方向和供电。芝麻 732..2929µs 是它的设定，不能作为所有 SG90 的默认边界。

## 限制与核对点

新增库版本 3.2.1，头文件声明 LGPL-2.1-or-later，原机器人 include 没锁定此提交。角度范围不等于实体关节无碰撞范围；电源与机械限制仍需目标硬件验证。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [ESP32Servo.h](<../%E9%80%9A%E7%94%A8%E5%BA%93%E6%BA%90%E7%A0%81/madhephaestus__ESP32Servo/src/ESP32Servo.h>)：`class Servo`，L145–L175。 [上游固定提交](https://github.com/madhephaestus/ESP32Servo/blob/88be58c5eb07d89c057d9c5fd0bcbf63b1c7d283/src/ESP32Servo.h#L145-L175)；提交 `88be58c5eb07d89c057d9c5fd0bcbf63b1c7d283`。
- [sesame-firmware-main.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/dorianborian__sesame-robot/firmware/sesame-firmware-main.ino>)：`setPeriodHertz(50)`，L740–L770。 [上游固定提交](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/firmware/sesame-firmware-main.ino#L740-L770)；提交 `d106cbc8e158c982f408db421134f23273c5f51f`。
- [sesame-firmware-main.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/dorianborian__sesame-robot/firmware/sesame-firmware-main.ino>)：`void setServoAngle`，L195–L225。 [上游固定提交](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/firmware/sesame-firmware-main.ino#L195-L225)；提交 `d106cbc8e158c982f408db421134f23273c5f51f`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
