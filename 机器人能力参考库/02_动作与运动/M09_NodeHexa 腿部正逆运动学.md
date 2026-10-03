# M09 NodeHexa 腿部正逆运动学

复用等级：**可单独提取；需接入驱动**。硬件：18舵机六足＋PCA9685。语言：C++。

关联项目：[06 NodeHexa六足机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/06_NodeHexa%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：六足、IK、FK、足端坐标、三关节、余弦定理。依赖：NodeHexa Leg、Point3D、Servo驱动。

## 怎么实现

Leg 把世界足端坐标转换为腿局部坐标，再以 atan2 与余弦定理求三个关节角，最后 Servo.setAngle 写输出。IK 对三角函数输入限幅并避免接近零的半径；FK 将关节角反算足端位置。

## 如何调用

moveTip(worldPoint) 与 moveTipLocal(localPoint) 坐标系不同。输出角度为度；连杆长度和 Point3D 要遵守 robot_geometry/base 定义的同一长度尺度，不擅自把所有 Point 值称为米。

## 移植与提取范围

六足/三自由度腿复用时先设置关节原点、安装旋转、连杆长度、trim/反向和目标可达区。用于四足需重建几何与步态，纸壳两舵机头部无须引入完整腿部 IK。

## 限制与核对点

数值限幅会生成边界角度，不能代替碰撞和不可达目标判断。README GPL-3.0 声明与缺失根 LICENSE 的情况在原项目记录中标明，沿用前核对具体代码许可。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [leg.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/06_NodeHexa%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/ViolinLee__NodeHexa/firmware/src/leg.cpp>)：`void Leg::moveTip`，L144–L174。 [上游固定提交](https://github.com/ViolinLee/NodeHexa/blob/ba844a107de8dbb95bba51c2d5e870928d72cbd9/firmware/src/leg.cpp#L144-L174)；提交 `ba844a107de8dbb95bba51c2d5e870928d72cbd9`。
- [leg.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/06_NodeHexa%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/ViolinLee__NodeHexa/firmware/src/leg.cpp>)：`Leg::_inverseKinematics`，L193–L223。 [上游固定提交](https://github.com/ViolinLee/NodeHexa/blob/ba844a107de8dbb95bba51c2d5e870928d72cbd9/firmware/src/leg.cpp#L193-L223)；提交 `ba844a107de8dbb95bba51c2d5e870928d72cbd9`。
- [leg.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/06_NodeHexa%E5%85%AD%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/ViolinLee__NodeHexa/firmware/src/leg.h>)：`moveTipLocal`，L26–L56。 [上游固定提交](https://github.com/ViolinLee/NodeHexa/blob/ba844a107de8dbb95bba51c2d5e870928d72cbd9/firmware/src/leg.h#L26-L56)；提交 `ba844a107de8dbb95bba51c2d5e870928d72cbd9`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
