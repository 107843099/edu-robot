# M14 ElectronBot 可用底层六关节接口

复用等级：**原环境可调用；新硬件需核对**。硬件：Windows PC＋ElectronBot USB驱动与六关节。语言：C++。

关联项目：[11 ElectronBot类人桌面机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/11_ElectronBot%E7%B1%BB%E4%BA%BA%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：六关节、USB关节、SetJointAngles、姿态反馈。依赖：ElectronLowLevel、USB驱动、OpenCV。

## 怎么实现

SetJointAngles 把6个 float 与 enable 标志写入发送额外数据缓冲，Sync 才沿 USB 图像帧发送；GetJointAngles 从接收缓冲读6个 float。此函数未做通用角度限幅，范围由设备固件和机械构型决定。

## 如何调用

Connect 成功后 SetJointAngles(j1,j2,j3,j4,j5,j6,true)，再 Sync()；默认 enable=false，所以不能省略参数后便期待关节动作。读取反馈使用 float[6]。

## 移植与提取范围

可用于匹配 ElectronBot 的主机控制或借数据打包。新 ESP32 工程需重建 USB/串口/网络传输、关节映射与显式边界；不要直接照六个未知角度推新硬件。

## 限制与核对点

ElectronPlayer::SetPose 在归档中函数体为空；GetPose 返回默认结构。Player 名字不能证明其动作封装已实现。原 SDK Windows __declspec 和 USB DLL ABI 不是跨平台即用库。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [electron_low_level.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/11_ElectronBot%E7%B1%BB%E4%BA%BA%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/peng-zhihui__ElectronBot/3.Software/SDK/ElectronBotSDK-LowLevel/src/electron_low_level.cpp>)：`void ElectronLowLevel::SetJointAngles`，L157–L186。 [上游固定提交](https://github.com/peng-zhihui/ElectronBot/blob/819927015323181a9a10e0184d64ad2bddfcb407/3.Software/SDK/ElectronBotSDK-LowLevel/src/electron_low_level.cpp#L157-L186)；提交 `819927015323181a9a10e0184d64ad2bddfcb407`。
- [electron_low_level.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/11_ElectronBot%E7%B1%BB%E4%BA%BA%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/peng-zhihui__ElectronBot/3.Software/SDK/ElectronBotSDK-LowLevel/src/electron_low_level.cpp>)：`void ElectronLowLevel::GetJointAngles`，L179–L186。 [上游固定提交](https://github.com/peng-zhihui/ElectronBot/blob/819927015323181a9a10e0184d64ad2bddfcb407/3.Software/SDK/ElectronBotSDK-LowLevel/src/electron_low_level.cpp#L179-L186)；提交 `819927015323181a9a10e0184d64ad2bddfcb407`。
- [electron_player.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/11_ElectronBot%E7%B1%BB%E4%BA%BA%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/peng-zhihui__ElectronBot/3.Software/SDK/ElectronBotSDK-Player/src/electron_player.cpp>)：`void ElectronPlayer::SetPose`，L56–L86。 [上游固定提交](https://github.com/peng-zhihui/ElectronBot/blob/819927015323181a9a10e0184d64ad2bddfcb407/3.Software/SDK/ElectronBotSDK-Player/src/electron_player.cpp#L56-L86)；提交 `819927015323181a9a10e0184d64ad2bddfcb407`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
