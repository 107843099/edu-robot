# E11 ElectronBot USB 屏幕帧与媒体播放

复用等级：**原环境可调用；新硬件需核对**。硬件：Windows PC＋ElectronBot USB设备。语言：C++。

关联项目：[11 ElectronBot类人桌面机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/11_ElectronBot%E7%B1%BB%E4%BA%BA%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：USB屏幕、240×240、视频、OpenCV、双缓冲。依赖：ElectronLowLevel、OpenCV、USB驱动。

## 怎么实现

底层 SDK 使用 240×240×3 图像双缓冲，通过 USB 将图像与额外关节数据送给整机。Player 根据后缀读取静态图，视频由 OpenCV VideoCapture 和播放线程逐帧送入底层 Sync。

## 如何调用

底层顺序 Connect→SetImageSrc→Sync；Player 可 Play 图像/视频，仍需匹配 DLL、OpenCV 和 USB 驱动。表情素材是屏幕媒体，不是可直接运行在 ESP32 OLED 上的绘制算法。

## 移植与提取范围

可以借图像/动作同帧传输与桌面编排思路。若新机器人用 Wi-Fi，重写传输和资源压缩；若直接复刻 ElectronBot，先固定 Windows ABI、帧格式和 USB VID/PID。

## 限制与核对点

Player 的 SetPose 空实现、GetPose 返回默认值；运动必须走 M14 的实际底层接口。Stop 只改变播放状态，不能推定关闭舵机扭矩。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [electron_low_level.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/11_ElectronBot%E7%B1%BB%E4%BA%BA%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/peng-zhihui__ElectronBot/3.Software/SDK/ElectronBotSDK-LowLevel/src/electron_low_level.h>)：`SetImageSrc`，L23–L51。 [上游固定提交](https://github.com/peng-zhihui/ElectronBot/blob/819927015323181a9a10e0184d64ad2bddfcb407/3.Software/SDK/ElectronBotSDK-LowLevel/src/electron_low_level.h#L23-L51)；提交 `819927015323181a9a10e0184d64ad2bddfcb407`。
- [electron_player.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/11_ElectronBot%E7%B1%BB%E4%BA%BA%E6%A1%8C%E9%9D%A2%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/peng-zhihui__ElectronBot/3.Software/SDK/ElectronBotSDK-Player/src/electron_player.cpp>)：`void ElectronPlayer::Play`，L20–L50。 [上游固定提交](https://github.com/peng-zhihui/ElectronBot/blob/819927015323181a9a10e0184d64ad2bddfcb407/3.Software/SDK/ElectronBotSDK-Player/src/electron_player.cpp#L20-L50)；提交 `819927015323181a9a10e0184d64ad2bddfcb407`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
