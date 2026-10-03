# M06 MindPaw 正弦情感动作与离散动作

复用等级：**可单独提取；需接入驱动**。硬件：ESP8266 Arduino＋4舵机。语言：C++。

关联项目：[03 MindPaw机器狗](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/README.md>)。

检索词：点头、摇头、安慰、庆祝、情感强度、振荡器。依赖：Servo、MotionEmotion、EmotionAction。

## 怎么实现

两种执行路径：鞠躬/伸展/遮脸使用离散 MotionStep 表，舞蹈/点头/摇头/庆祝/安慰使用每通道独立正弦振荡。中心与振幅是度，frequency 是 Hz，phase 是弧度，durationMs 是毫秒。PAD 输入通过强度/速度缩放影响幅度、频率与时长。

## 如何调用

attach(s1,s2,s3,s4) 后 trigger(ACTION_NOD,1)；主循环不断 loop()。自定义动作可 triggerParametric(params,repeat)。setEmotionalIntensity(pleasure,arousal) 使用源码范围，再由原实现约束。stop() 清播放状态，没有自动回中或切断 PWM。

## 移植与提取范围

两舵机头部可借正弦公式和非阻塞计时，但重写通道数与预设：pitch 点头、yaw 摇头，不能把狗腿相位直接套到头部。任一时刻只允许一个控制器写同一舵机。

## 限制与核对点

原 main 检查 isPlaying() 暂停旧运动分支，防止两路争写。情感状态是软件参数模型；不把未训练手势权重或模拟 3D 重建当成熟感知组件。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [motion_emotion.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/%E4%BB%93%E5%BA%93/ace-trump-tech__MindPaw/MindPaw_main/src/motion_emotion.h>)：`struct OscillatorParams`，L13–L43。 [上游固定提交](https://github.com/ace-trump-tech/MindPaw/blob/21c549252a60126a80874738626f1b8c36efc38c/MindPaw_main/src/motion_emotion.h#L13-L43)；提交 `21c549252a60126a80874738626f1b8c36efc38c`。
- [motion_emotion.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/%E4%BB%93%E5%BA%93/ace-trump-tech__MindPaw/MindPaw_main/src/motion_emotion.cpp>)：`void MotionEmotion::trigger`，L148–L178。 [上游固定提交](https://github.com/ace-trump-tech/MindPaw/blob/21c549252a60126a80874738626f1b8c36efc38c/MindPaw_main/src/motion_emotion.cpp#L148-L178)；提交 `21c549252a60126a80874738626f1b8c36efc38c`。
- [motion_emotion.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/%E4%BB%93%E5%BA%93/ace-trump-tech__MindPaw/MindPaw_main/src/motion_emotion.cpp>)：`void MotionEmotion::loop`，L273–L303。 [上游固定提交](https://github.com/ace-trump-tech/MindPaw/blob/21c549252a60126a80874738626f1b8c36efc38c/MindPaw_main/src/motion_emotion.cpp#L273-L303)；提交 `21c549252a60126a80874738626f1b8c36efc38c`。
- [motion_emotion.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/%E4%BB%93%E5%BA%93/ace-trump-tech__MindPaw/MindPaw_main/src/motion_emotion.cpp>)：`void MotionEmotion::stop`，L228–L258。 [上游固定提交](https://github.com/ace-trump-tech/MindPaw/blob/21c549252a60126a80874738626f1b8c36efc38c/MindPaw_main/src/motion_emotion.cpp#L228-L258)；提交 `21c549252a60126a80874738626f1b8c36efc38c`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
