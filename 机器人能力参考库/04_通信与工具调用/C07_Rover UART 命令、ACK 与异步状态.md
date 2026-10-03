# C07 Rover UART 命令、ACK 与异步状态

复用等级：**原环境可调用；新硬件需核对**。硬件：Atom Echo S3R语音板＋C3电机板。语言：串口文本/Arduino。

关联项目：[12 VerdureLab外壳资源](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/12_VerdureLab%E5%A4%96%E5%A3%B3%E8%B5%84%E6%BA%90/README.md>)。

检索词：UART、MCP桥接、OK、ERR、EVT、电机板。依赖：Rover固件、匹配小智板型分支。

## 怎么实现

电机板接收换行文本命令并返回OK/ERR；电量等EVT是异步事件。语音主板的匹配分支将MCP工具转串口，处理返回状态。不能把收到任意一行都当作刚发送命令的ACK。

## 如何调用

先ping/status确认固件，再发送drive、forward、turn、stop等原命令。命令百分比与motor底层PWM不同，LED emotion另用灯效参数。

## 移植与提取范围

纸壳双板方案可复用“语音板负责协议/模型，执行板负责驱动”的划分，自己建立命令编号、超时和忙/完成通知。沿原分支对照实际串口引脚和波特率。

## 限制与核对点

原驱动反转20ms等待可能影响响应；尚不能据已读片段保证串口断开自动停车。是否有自动停止必须通过目标固件验证。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [esp32c3_kb_motor.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/12_VerdureLab%E5%A4%96%E5%A3%B3%E8%B5%84%E6%BA%90/%E4%BB%93%E5%BA%93/maker-community__VerdureBuddyRover/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino>)：`void handleCommand`，L362–L392。 [上游固定提交](https://github.com/maker-community/VerdureBuddyRover/blob/cf1c772dcc854ae5c19699eebb3970e1c3f64f34/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino#L362-L392)；提交 `cf1c772dcc854ae5c19699eebb3970e1c3f64f34`。
- [esp32c3_kb_motor.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/12_VerdureLab%E5%A4%96%E5%A3%B3%E8%B5%84%E6%BA%90/%E4%BB%93%E5%BA%93/maker-community__VerdureBuddyRover/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino>)：`EVT`，L10–L40。 [上游固定提交](https://github.com/maker-community/VerdureBuddyRover/blob/cf1c772dcc854ae5c19699eebb3970e1c3f64f34/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino#L10-L40)；提交 `cf1c772dcc854ae5c19699eebb3970e1c3f64f34`。
- [esp32c3_kb_motor.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/12_VerdureLab%E5%A4%96%E5%A3%B3%E8%B5%84%E6%BA%90/%E4%BB%93%E5%BA%93/maker-community__VerdureBuddyRover/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino>)：`OK`，L358–L388。 [上游固定提交](https://github.com/maker-community/VerdureBuddyRover/blob/cf1c772dcc854ae5c19699eebb3970e1c3f64f34/firmware/esp32c3_kb_motor/esp32c3_kb_motor.ino#L358-L388)；提交 `cf1c772dcc854ae5c19699eebb3970e1c3f64f34`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
