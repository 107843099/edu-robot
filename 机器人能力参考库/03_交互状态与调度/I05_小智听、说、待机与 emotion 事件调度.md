# I05 小智听、说、待机与 emotion 事件调度

复用等级：**原环境可调用；新硬件需核对**。硬件：匹配小智 ESP-IDF板型＋音频服务＋后端。语言：C++。

关联项目：[08 小智语音机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/08_%E5%B0%8F%E6%99%BA%E8%AF%AD%E9%9F%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)、[09 Otto闪猫侠机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)、[10 EMO-Dot小豆机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/10_EMO-Dot%E5%B0%8F%E8%B1%86%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：语音状态、Listening、Speaking、Schedule、emotion。依赖：Application、DeviceStateMachine、AudioService、Display。

## 怎么实现

Application 把语音通道、播放队列、VAD和设备状态组织起来。TTS消息转 speaking/listening/idle；llm emotion 通过 Schedule 在应用线程更新 display。听说状态和表情是相互关联但不同的状态，不依靠动作函数里长等待实现。

## 如何调用

扩展原板型时沿 SetDeviceState/SetListeningMode 与调度回调接入；音频结束依队列/播放状态判断，不能收到 tts stop 就立刻假定所有样本播放完毕。

## 移植与提取范围

纸壳对话版本可继承当前支持板型，新增两舵机动作执行层，把 speaking事件映射为说话动画、listening映射为注视。动作结束也回报状态，不阻塞音频服务。

## 限制与核对点

后端 ASR/LLM/TTS 并未因此成为芯片上离线全功能模型。08主分支与09分支 API/IDF版本差异见依赖表，不能仅复制 application.cc。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [application.cc](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/08_%E5%B0%8F%E6%99%BA%E8%AF%AD%E9%9F%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/78__xiaozhi-esp32/main/application.cc>)：`bool Application::SetDeviceState`，L59–L89。 [上游固定提交](https://github.com/78/xiaozhi-esp32/blob/d395220a83fb7a16ea5dc761c08a4816177cc880/main/application.cc#L59-L89)；提交 `d395220a83fb7a16ea5dc761c08a4816177cc880`。
- [application.cc](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/08_%E5%B0%8F%E6%99%BA%E8%AF%AD%E9%9F%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/78__xiaozhi-esp32/main/application.cc>)：`auto emotion = cJSON_GetObjectItem(root, "emotion")`，L671–L701。 [上游固定提交](https://github.com/78/xiaozhi-esp32/blob/d395220a83fb7a16ea5dc761c08a4816177cc880/main/application.cc#L671-L701)；提交 `d395220a83fb7a16ea5dc761c08a4816177cc880`。
- [application.cc](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/08_%E5%B0%8F%E6%99%BA%E8%AF%AD%E9%9F%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/78__xiaozhi-esp32/main/application.cc>)：`void Application::SetListeningMode`，L1183–L1213。 [上游固定提交](https://github.com/78/xiaozhi-esp32/blob/d395220a83fb7a16ea5dc761c08a4816177cc880/main/application.cc#L1183-L1213)；提交 `d395220a83fb7a16ea5dc761c08a4816177cc880`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
