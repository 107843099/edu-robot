# I03 M5Avatar 音量驱动嘴巴开合

复用等级：**需要移植或配套运行环境**。硬件：旧 M5Stack/AquesTalkTTS配套环境。语言：C++。

关联项目：[04 Stack-chan桌面机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：lip sync、嘴巴、TTS、音量、说话同步。依赖：M5Stack_Avatar、AquesTalkTTS、FreeRTOS任务。

## 怎么实现

任务无限循环读取 TTS.getLevel，将音量除以12000、上限1.0，传给 setMouthOpenRatio，每33ms等待一次。它是声音幅度的视觉近似，不按音素判断嘴形。

## 如何调用

原 DriveContext 提供 Avatar 指针，由原任务管理方式启动 lipSync。若使用其他 TTS/音频引擎，取对应幅度或 RMS 转0..1，再调 Avatar 的嘴巴 setter。

## 移植与提取范围

纸壳可使用“音量/播放状态→嘴巴比例”思路，但要换自己的屏幕 renderer。没有音量时，用播放起止启停 talk_* 帧，不标称精确同步。

## 限制与核对点

这个头文件还 include AquesTalkTTS 与旧 M5Core2/M5Stack，和当前库声明 M5Unified 的依赖不能机械拼装。停止任务/归零嘴巴是上层职责。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [LipSync.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__m5stack-avatar/src/tasks/LipSync.h>)：`extern void lipSync`，L18–L31。 [上游固定提交](https://github.com/stack-chan/m5stack-avatar/blob/7a90083edd9bbdc1a52ea13afe4d5c3b7fc7bfa8/src/tasks/LipSync.h#L18-L31)；提交 `7a90083edd9bbdc1a52ea13afe4d5c3b7fc7bfa8`。
- [LipSync.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/04_Stack-chan%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/stack-chan__m5stack-avatar/src/tasks/LipSync.h>)：`TTS.getLevel()`，L22–L31。 [上游固定提交](https://github.com/stack-chan/m5stack-avatar/blob/7a90083edd9bbdc1a52ea13afe4d5c3b7fc7bfa8/src/tasks/LipSync.h#L22-L31)；提交 `7a90083edd9bbdc1a52ea13afe4d5c3b7fc7bfa8`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
