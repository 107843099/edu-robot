# E06 Stack-chan Moddable 面部状态与皮肤

复用等级：**原环境可调用；新硬件需核对**。硬件：Moddable JavaScript/TypeScript＋Stack-chan 支持板。语言：TypeScript。

关联项目：[04 Stack-chan桌面机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：Piu、皮肤、face、emotion、颜色、呼吸。依赖：Moddable、Piu。

## 怎么实现

FaceState 保存 mouth.open、左右 eye.open/gazeX/gazeY、breath、emotion 和 theme。运行时上下文改变这些状态，Piu face-view 和当前 skin 消费状态绘制；分发前可量化呼吸值，避免无意义的逐像素重绘。

## 如何调用

Mod 的 onContextCreated(context) 中用 context.face.setEmotion(...)，参数按 firmware/docs/api.md。Emotion 有 NEUTRAL、ANGRY、SAD、HAPPY、SLEEPY、DOUBTFUL、COLD、HOT；还可改颜色和切换皮肤。

## 移植与提取范围

保留 host 状态、UI skin 与 Mod 生命周期配套，不能仅把 .ts 文件粘进 Arduino。若只借设计，提取状态模型和情绪到几何参数的映射，再用目标屏幕实现 renderer。

## 限制与核对点

当前归档 develop 是 Moddable 路线；Arduino 的 M5Avatar 是另外一套接口与工具链。context 关闭时释放相关资源，避免遗留 Timer。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [face-state.ts](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__stack-chan/firmware/host/modules/ui/state/face-state.ts>)：`export const Emotion`，L1–L31。 [上游固定提交](https://github.com/stack-chan/stack-chan/blob/fe7be1005d2cf8732f365176a91c7177c8533591/firmware/host/modules/ui/state/face-state.ts#L1-L31)；提交 `fe7be1005d2cf8732f365176a91c7177c8533591`。
- [face-state.ts](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__stack-chan/firmware/host/modules/ui/state/face-state.ts>)：`export type FaceState`，L62–L92。 [上游固定提交](https://github.com/stack-chan/stack-chan/blob/fe7be1005d2cf8732f365176a91c7177c8533591/firmware/host/modules/ui/state/face-state.ts#L62-L92)；提交 `fe7be1005d2cf8732f365176a91c7177c8533591`。
- [api.md](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__stack-chan/firmware/docs/api.md>)：`context.face`，L58–L88。 [上游固定提交](https://github.com/stack-chan/stack-chan/blob/fe7be1005d2cf8732f365176a91c7177c8533591/firmware/docs/api.md#L58-L88)；提交 `fe7be1005d2cf8732f365176a91c7177c8533591`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
