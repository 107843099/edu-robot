# I04 MindPaw Agent 响应到动作、表情和强度

复用等级：**需要移植或配套运行环境**。硬件：MindPaw主控＋外部Agent服务。语言：C++/JSON。

关联项目：[03 MindPaw机器狗](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/README.md>)。

检索词：情绪联动、AgentResponse、PAD、动作白名单。依赖：ArduinoJson、MotionEmotion、EmotionEngine。

## 怎么实现

AgentResponse 包含 action、expression、melody、repeat、emotion，dispatch 将动作11..18交给 MotionEmotion，旧1..10走既有分支。PAD强度先影响运动参数；同一主循环检查情感动作播放状态，避免旧控制器同时写舵机。

## 如何调用

不要把 LLM 的任意字符串或数字直接写 PWM；沿原 parser 和枚举解析，再映射到有限函数。expression 的含义必须核对 E04 的画面 switch。

## 移植与提取范围

可以借响应结构和单一输出所有者，给纸壳定义有限 express/motion enum、次数和持续时长。语音后端仍在外部服务，主控只执行已定义能力。

## 限制与核对点

提示词允许的动作不保证全部具备同等中断性；旧路径与新振荡器不同。模型生成数字需检查范围/字段，固定预设比任意角度更易复用。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [main.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/%E4%BB%93%E5%BA%93/ace-trump-tech__MindPaw/MindPaw_main/src/main.cpp>)：`dispatchAgentResponse`，L116–L146。 [上游固定提交](https://github.com/ace-trump-tech/MindPaw/blob/21c549252a60126a80874738626f1b8c36efc38c/MindPaw_main/src/main.cpp#L116-L146)；提交 `21c549252a60126a80874738626f1b8c36efc38c`。
- [doubao_config.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/%E4%BB%93%E5%BA%93/ace-trump-tech__MindPaw/MindPaw_main/src/doubao_config.h>)：`struct AgentResponse`，L49–L79。 [上游固定提交](https://github.com/ace-trump-tech/MindPaw/blob/21c549252a60126a80874738626f1b8c36efc38c/MindPaw_main/src/doubao_config.h#L49-L79)；提交 `21c549252a60126a80874738626f1b8c36efc38c`。
- [main.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/%E4%BB%93%E5%BA%93/ace-trump-tech__MindPaw/MindPaw_main/src/main.cpp>)：`motionEmotion.isPlaying()`，L1696–L1726。 [上游固定提交](https://github.com/ace-trump-tech/MindPaw/blob/21c549252a60126a80874738626f1b8c36efc38c/MindPaw_main/src/main.cpp#L1696-L1726)；提交 `21c549252a60126a80874738626f1b8c36efc38c`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
