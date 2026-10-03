# M08 Stack-chan 注视、避视与头部姿态

复用等级：**原环境可调用；新硬件需核对**。硬件：Stack-chan Moddable＋其支持舵机驱动。语言：TypeScript/JavaScript。

关联项目：[04 Stack-chan桌面机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：点头、摇头、lookAt、lookAway、注视目标、扭矩。依赖：Moddable、motion-controller、舵机驱动。

## 怎么实现

motion-controller 将三维目标转为头部旋转，再交给驱动 applyRotation；lookAway 与 setPose 提供不同的姿态入口，setTorque 控制驱动力。示例按 Timer 周期随机看向周围目标。

## 如何调用

在 onContextCreated(robot) 中 robot.motion.lookAt([0.5,0,0])；坐标单位米，姿态角单位弧度。setPose 的结构和 time/callback 按当前类型定义使用；不能把 Arduino degree 数组直接传进来。

## 移植与提取范围

桌面头部机器人优先借“目标坐标→偏航/俯仰→驱动”的分层。纸壳 C3 可复用几何思路并换 ESP32Servo，但 Mod 生命周期、Timer 和串口驱动必须重接。

## 限制与核对点

注意旧 flat API 已被当前 context API 取代。几何尺寸、旋转方向和软限位由板型/驱动决定；0.5米目标并不承诺任何新构型的有效行程。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [motion-controller.ts](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__stack-chan/firmware/host/modules/motion/motion-controller.ts>)：`lookAt(`，L143–L173。 [上游固定提交](https://github.com/stack-chan/stack-chan/blob/fe7be1005d2cf8732f365176a91c7177c8533591/firmware/host/modules/motion/motion-controller.ts#L143-L173)；提交 `fe7be1005d2cf8732f365176a91c7177c8533591`。
- [mod.js](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__stack-chan/firmware/mods/examples/look_around/mod.js>)：`robot.motion.lookAt`，L31–L34。 [上游固定提交](https://github.com/stack-chan/stack-chan/blob/fe7be1005d2cf8732f365176a91c7177c8533591/firmware/mods/examples/look_around/mod.js#L31-L34)；提交 `fe7be1005d2cf8732f365176a91c7177c8533591`。
- [api.md](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__stack-chan/firmware/docs/api.md>)：`setTorque`，L57–L87。 [上游固定提交](https://github.com/stack-chan/stack-chan/blob/fe7be1005d2cf8732f365176a91c7177c8533591/firmware/docs/api.md#L57-L87)；提交 `fe7be1005d2cf8732f365176a91c7177c8533591`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
