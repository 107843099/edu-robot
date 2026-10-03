# M15 VerdureBuddyRover 双电机差速与 LED情绪

复用等级：**原环境可调用；新硬件需核对**。硬件：ESP32-C3 电机板＋DRV8833。语言：Arduino C++。

关联项目：[12 VerdureLab外壳资源](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/12_VerdureLab%E5%A4%96%E5%A3%B3%E8%B5%84%E6%BA%90/README.md>)。

检索词：小车、差速、DRV8833、drive、转向、LED情绪。依赖：Arduino-ESP32、UART命令解析。

## 怎么实现

两个 H 桥分别控制左右轮，setMotor 接受有符号 PWM，反转先归零并等待20ms。setDrive 组合双轮输出；handleCommand 将百分比 drive、forward/back、turn/spin、limit、stop 转为输出。板上灯可用 emotion 模式回应状态。

## 如何调用

原串口行命令如 drive 30 30、stop、status，以换行终止。drive 两轮百分比±100，经速度限制换算；motor 底层命令采用±255 PWM，不可混淆。LED/RGB 是灯效，不等于屏幕表情。

## 移植与提取范围

新轮式机器人可保留命令解析和驱动分层，改 GPIO、电机方向与供电。配套 Atom Echo S3R 语音板把 MCP 调用转串口，见 C07；不会只烧电机板便获得对话。

## 限制与核对点

GPIO 与 PWM 频率为原板设置；新版本 core API 需匹配。停止命令、串口断开与供电切断需要分清；这里只记录已读代码行为，不承诺未证实的自动断线停止。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [esp32c3_kb_motor.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/12_VerdureLab%E5%A4%96%E5%A3%B3%E8%B5%84%E6%BA%90/%E4%BB%93%E5%BA%93/maker-community__VerdureBuddyRover/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino>)：`void setMotor`，L162–L192。 [上游固定提交](https://github.com/maker-community/VerdureBuddyRover/blob/cf1c772dcc854ae5c19699eebb3970e1c3f64f34/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino#L162-L192)；提交 `cf1c772dcc854ae5c19699eebb3970e1c3f64f34`。
- [esp32c3_kb_motor.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/12_VerdureLab%E5%A4%96%E5%A3%B3%E8%B5%84%E6%BA%90/%E4%BB%93%E5%BA%93/maker-community__VerdureBuddyRover/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino>)：`void setDrive`，L173–L203。 [上游固定提交](https://github.com/maker-community/VerdureBuddyRover/blob/cf1c772dcc854ae5c19699eebb3970e1c3f64f34/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino#L173-L203)；提交 `cf1c772dcc854ae5c19699eebb3970e1c3f64f34`。
- [esp32c3_kb_motor.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/12_VerdureLab%E5%A4%96%E5%A3%B3%E8%B5%84%E6%BA%90/%E4%BB%93%E5%BA%93/maker-community__VerdureBuddyRover/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino>)：`void handleCommand`，L362–L392。 [上游固定提交](https://github.com/maker-community/VerdureBuddyRover/blob/cf1c772dcc854ae5c19699eebb3970e1c3f64f34/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino#L362-L392)；提交 `cf1c772dcc854ae5c19699eebb3970e1c3f64f34`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
