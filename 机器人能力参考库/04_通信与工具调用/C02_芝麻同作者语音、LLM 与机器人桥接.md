# C02 芝麻同作者语音、LLM 与机器人桥接

复用等级：**原环境可调用；新硬件需核对**。硬件：电脑Python＋麦克风扬声器＋芝麻HTTP。语言：Python。

关联项目：[01 芝麻机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：语音对话、芝麻配套、ASR、TTS、Gemini、LLM。依赖：SpeechRecognition、pyttsx3、requests、可选LLM/TTS后端。

## 怎么实现

电脑应用识别语音，生成带动作/情绪约束的模型请求，再由 RobotController POST到机器人。TTS 从电脑播放，并通过线程/表情循环让机器人显示 talk_*；Local LLM与Gemini是可选后端。

## 如何调用

原应用设置机器人地址和对应服务配置后，沿 process_input入口使用。AVAILABLE_COMMANDS与表情列表是配套协议，应和固件版本核对。不要把主机类误当能在ESP32 import的库。

## 移植与提取范围

纸壳第一版若先用电脑作为语音大脑，可保留电脑ASR/LLM/TTS，替换RobotController为串口适配器。之后再迁移小智云端对话；新增适配器需要开发，当前没有提供。

## 限制与核对点

recognize_google 使用在线识别，即使选择Local LLM也不是完整离线。动作分支可能传face=None，说话表情另线程驱动；不能保证任意动作与任意表情都原子同步。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [sesame_companion.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/dorianborian__sesame-companion-app/sesame_companion.py>)：`class VoiceInterface`，L161–L191。 [上游固定提交](https://github.com/dorianborian/sesame-companion-app/blob/86f82c137b9954445f55d249c966e8f9984bd87b/sesame_companion.py#L161-L191)；提交 `86f82c137b9954445f55d249c966e8f9984bd87b`。
- [sesame_companion.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/dorianborian__sesame-companion-app/sesame_companion.py>)：`class SesameRobotController`，L443–L473。 [上游固定提交](https://github.com/dorianborian/sesame-companion-app/blob/86f82c137b9954445f55d249c966e8f9984bd87b/sesame_companion.py#L443-L473)；提交 `86f82c137b9954445f55d249c966e8f9984bd87b`。
- [sesame_companion.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/dorianborian__sesame-companion-app/sesame_companion.py>)：`def process_input`，L631–L661。 [上游固定提交](https://github.com/dorianborian/sesame-companion-app/blob/86f82c137b9954445f55d249c966e8f9984bd87b/sesame_companion.py#L631-L661)；提交 `86f82c137b9954445f55d249c966e8f9984bd87b`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
