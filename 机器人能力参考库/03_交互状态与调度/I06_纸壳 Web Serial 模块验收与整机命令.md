# I06 纸壳 Web Serial 模块验收与整机命令

复用等级：**原环境可调用；新硬件需核对**。硬件：浏览器支持 Web Serial＋USB115200串口。语言：JavaScript。

关联项目：[15 小纸壳机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/15_%E5%B0%8F%E7%BA%B8%E5%A3%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：串口、Web Serial、校准、pan、tilt、验收。依赖：TestConnection、TextEncoder、Web Serial。

## 怎么实现

TestConnection 管理串口写链，UTF-8命令以换行结尾；模块模式发送 PING/START/STOP，整机模式发送1/2/B/C/A/D/W/S/V/X/R及问号心跳。网页解析 CB_TEST与位置状态，区分校准、正常与中心设置。

## 如何调用

115200串口；A/D 水平、W/S 垂直每次1°，V保存中心，X停止 PWM，R恢复 PWM但不自动回中心。必须等待对应模式/响应再开始，避免将模块固件命令发给完整机器人固件。

## 移植与提取范围

第一版复刻保留这一验收工具；后续自己的固件应定义带版本/板型/能力的明确握手与 ACK，而非仅根据串口字符串判定所有功能存在。

## 限制与核对点

disconnect 对模块会发送 STOP，对完整机器人不会，关闭网页不等于整机紧停。先前模拟检查发现部分身份判定不严谨；串口网页调用证据不等于完整固件源码。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [test-connection.js](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/15_%E5%B0%8F%E7%BA%B8%E5%A3%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E5%B7%A5%E5%85%B7%E5%8C%85/cardboard-bot-teaching/test-connection.js>)：`class TestConnection`，L3–L33。 本地材料，以索引中的 Git blob/文本校验哈希追踪。
- [test-connection.js](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/15_%E5%B0%8F%E7%BA%B8%E5%A3%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E5%B7%A5%E5%85%B7%E5%8C%85/cardboard-bot-teaching/test-connection.js>)：`async robotCommand`，L171–L201。 本地材料，以索引中的 Git blob/文本校验哈希追踪。
- [test-connection.js](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/15_%E5%B0%8F%E7%BA%B8%E5%A3%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/%E5%B7%A5%E5%85%B7%E5%8C%85/cardboard-bot-teaching/test-connection.js>)：`async disconnect`，L215–L245。 本地材料，以索引中的 Git blob/文本校验哈希追踪。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
