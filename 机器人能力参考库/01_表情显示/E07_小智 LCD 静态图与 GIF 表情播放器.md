# E07 小智 LCD 静态图与 GIF 表情播放器

复用等级：**原环境可调用；新硬件需核对**。硬件：ESP-IDF＋LVGL LCD 显示分支。语言：C++。

关联项目：[08 小智语音机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/08_%E5%B0%8F%E6%99%BA%E8%AF%AD%E9%9F%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)、[09 Otto闪猫侠机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)、[10 EMO-Dot小豆机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/10_EMO-Dot%E5%B0%8F%E8%B1%86%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：GIF、LVGL、表情资源、SetEmotion、彩屏。依赖：ESP-IDF、LVGL、esp_lvgl_port、xiaozhi-fonts。

## 怎么实现

LcdDisplay::SetEmotion 从当前主题的 EmojiCollection 找资源。停止旧 GIF 后区分静态图与 GIF；GIF 构造 LvglGif，注册帧回调更新 lv_image，然后开始播放。资源缺失时走字体图标或文本后备；UI 修改受 DisplayLockGuard 保护。

## 如何调用

原工程经 Board::GetInstance().GetDisplay()->SetEmotion("happy") 进入具体显示实现。llm emotion 消息也是这一入口。GIF 命名必须存在于实际主题资源，不能任意新增字符串便期待画面出现。

## 移植与提取范围

为新彩屏机器人保留主题集合、GIF 解码器、LVGL 对象、资源打包及锁。单色 OLED 有独立显示路径，不能直接替换为 LCD 的 GIF 分支。先明确硬件板型和堆内存预算。

## 限制与核对点

归档主分支要求 IDF>=6.0.1、LVGL~9.5.0；Otto 分支要求 IDF>=5.5.2。新增7个 Arduino 通用库不提供 IDF 工具链，版本不能混用。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [lcd_display.cc](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/08_%E5%B0%8F%E6%99%BA%E8%AF%AD%E9%9F%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/78__xiaozhi-esp32/main/display/lcd_display.cc>)：`void LcdDisplay::SetEmotion`，L1132–L1162。 [上游固定提交](https://github.com/78/xiaozhi-esp32/blob/d395220a83fb7a16ea5dc761c08a4816177cc880/main/display/lcd_display.cc#L1132-L1162)；提交 `d395220a83fb7a16ea5dc761c08a4816177cc880`。
- [lcd_display.cc](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/08_%E5%B0%8F%E6%99%BA%E8%AF%AD%E9%9F%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/78__xiaozhi-esp32/main/display/lcd_display.cc>)：`gif_controller_->Start()`，L1063–L1093。 [上游固定提交](https://github.com/78/xiaozhi-esp32/blob/d395220a83fb7a16ea5dc761c08a4816177cc880/main/display/lcd_display.cc#L1063-L1093)；提交 `d395220a83fb7a16ea5dc761c08a4816177cc880`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
