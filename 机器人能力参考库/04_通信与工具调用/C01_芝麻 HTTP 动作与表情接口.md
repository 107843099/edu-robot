# C01 芝麻 HTTP 动作与表情接口

复用等级：**原环境可调用；新硬件需核对**。硬件：芝麻固件网络服务＋局域网客户端。语言：HTTP/C++。

关联项目：[01 芝麻机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：HTTP、远程控制、api/command、JSON、face。依赖：WebServer、WiFi。

## 怎么实现

固件注册 POST /api/command 和状态接口。命令体包含 command/face 等，处理器更新 currentCommand 或切换表情；主循环选择已实现的运动。face-only 与动作请求分别有处理路径。

## 如何调用

文档示例可 POST {"face":"happy"}，或 {"command":"wave"}；主机IP使用真实设备地址。原处理器采用字符串搜索式解析，调用端应生成简单字段和预设白名单。

## 移植与提取范围

可作为纸壳外部控制协议参考，但新固件应正式解析JSON、区分ACK/完成事件、限制命令长度和次数，并实现断线策略。显示与动作是否同时执行需依原分支确认。

## 限制与核对点

原命令白名单与姿势函数名不完全同形。不要把函数runWalkPose写成HTTP命令名，应该用注册/分派中的 forward。本次未向真实设备发送请求。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [sesame-firmware-main.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/dorianborian__sesame-robot/firmware/sesame-firmware-main.ino>)：`void handleApiCommand`，L210–L240。 [上游固定提交](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/firmware/sesame-firmware-main.ino#L210-L240)；提交 `d106cbc8e158c982f408db421134f23273c5f51f`。
- [sesame-firmware-main.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/dorianborian__sesame-robot/firmware/sesame-firmware-main.ino>)：`server.on("/api/command"`，L719–L749。 [上游固定提交](https://github.com/dorianborian/sesame-robot/blob/d106cbc8e158c982f408db421134f23273c5f51f/firmware/sesame-firmware-main.ino#L719-L749)；提交 `d106cbc8e158c982f408db421134f23273c5f51f`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
