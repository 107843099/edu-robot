# E05 M5Stack Avatar 情绪、嘴巴与眼睛参数

复用等级：**原环境可调用；新硬件需核对**。硬件：M5Stack ESP32 彩屏＋M5Unified。语言：C++。

关联项目：[04 Stack-chan桌面机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：嘴巴、mouth、情绪、视线、自动眨眼、M5Stack。依赖：M5Stack_Avatar、M5Unified。

## 怎么实现

Avatar 将眼睛、眉毛、嘴巴等面部部件组合绘制。Expression 枚举控制情绪，眼睛开合、左右视线、嘴巴比例、位置、缩放和旋转分别有 setter。绘制任务与表情参数可独立更新，不必预画所有帧。

## 如何调用

M5 初始化后创建 m5avatar::Avatar，init()；setExpression(m5avatar::Expression::Happy)，setMouthOpenRatio(0.5f)，setRightGaze()/setLeftGaze()。此版本没有凭空通用的 setGaze() 调用；按 Avatar.h 的真实签名传参。

## 移植与提取范围

已保存 v0.10.0 完整库，不重复下载。新 M5Stack 方案可以调用原库；纸壳单色 OLED 需要重写显示后端或转用 E01/E02。Mouth 比例适合由音量、TTS 开始结束或音频包状态驱动。

## 限制与核对点

本库 MIT；依赖 M5Unified。附带 LipSync.h 是旧 AquesTalk/M5Stack 路线，不能直接当成任意音频输入的兼容组件，见 I03。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [Avatar.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__m5stack-avatar/src/Avatar.h>)：`void setExpression`，L75–L105。 [上游固定提交](https://github.com/stack-chan/m5stack-avatar/blob/7a90083edd9bbdc1a52ea13afe4d5c3b7fc7bfa8/src/Avatar.h#L75-L105)；提交 `7a90083edd9bbdc1a52ea13afe4d5c3b7fc7bfa8`。
- [Avatar.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__m5stack-avatar/src/Avatar.h>)：`void setMouthOpenRatio`，L107–L137。 [上游固定提交](https://github.com/stack-chan/m5stack-avatar/blob/7a90083edd9bbdc1a52ea13afe4d5c3b7fc7bfa8/src/Avatar.h#L107-L137)；提交 `7a90083edd9bbdc1a52ea13afe4d5c3b7fc7bfa8`。
- [Expression.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__m5stack-avatar/src/Expression.h>)：`enum class Expression`，L9–L12。 [上游固定提交](https://github.com/stack-chan/m5stack-avatar/blob/7a90083edd9bbdc1a52ea13afe4d5c3b7fc7bfa8/src/Expression.h#L9-L12)；提交 `7a90083edd9bbdc1a52ea13afe4d5c3b7fc7bfa8`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
