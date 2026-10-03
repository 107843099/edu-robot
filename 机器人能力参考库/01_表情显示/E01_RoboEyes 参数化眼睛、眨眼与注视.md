# E01 RoboEyes 参数化眼睛、眨眼与注视

复用等级：**可单独提取；需接入驱动**。硬件：Arduino＋Adafruit_GFX 单色屏；Albert 使用 SH1106 128×64。语言：C++。

关联项目：[05 AlbertMicro机器小狗](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/05_AlbertMicro%E6%9C%BA%E5%99%A8%E5%B0%8F%E7%8B%97/README.md>)、[15 小纸壳机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/15_%E5%B0%8F%E7%BA%B8%E5%A3%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：眨眼、blink、注视、gaze、开心、困倦、OLED。依赖：RoboEyes、Adafruit_GFX、SSD1306或SH110x。

## 怎么实现

不保存整套逐帧图片，而用眼睛宽高、圆角、眼睑和位置参数绘制形状。update() 按 millis() 限帧，drawEyes() 更新开合与位置并刷新屏幕；自动眨眼和随机游走由独立计时器驱动。AlbertMicro 在此之上切换情绪并持续调用 update()。

## 如何调用

创建 RoboEyes<具体显示类> 对象，传入已初始化的显示实例；begin(width,height,fps)，setMood(HAPPY)，setPosition(E)，setAutoblinker(ON,3,2)，在 loop 中 update()。blink()、anim_confused()、anim_laugh() 是已有入口。自动眨眼间隔与变化量单位为秒。

## 移植与提取范围

纸壳 OLED 原型可先单独接入这一库；确认 SSD1306 与 SH1106 驱动，调整眼睛宽高和间距。表情只接管屏幕；点头仍交给舵机层。新增快照 v1.1.2 与 Albert 当时使用版本不能等同。

## 限制与核对点

库为 GPL-3.0，保留许可。AlbertMicro 本体未找到整体许可证，不能借 RoboEyes 的许可推定它可任意复制。阻塞动作中的长 delay 会降低眨眼更新频率；本次没有真机刷新率验证。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [FluxGarage_RoboEyes.h](<../%E9%80%9A%E7%94%A8%E5%BA%93%E6%BA%90%E7%A0%81/FluxGarage__RoboEyes/src/FluxGarage_RoboEyes.h>)：`void setMood`，L286–L316。 [上游固定提交](https://github.com/FluxGarage/RoboEyes/blob/b42f8e596535234932be3514ac7a813d4ced0046/src/FluxGarage_RoboEyes.h#L286-L316)；提交 `b42f8e596535234932be3514ac7a813d4ced0046`。
- [FluxGarage_RoboEyes.h](<../%E9%80%9A%E7%94%A8%E5%BA%93%E6%BA%90%E7%A0%81/FluxGarage__RoboEyes/src/FluxGarage_RoboEyes.h>)：`void setAutoblinker`，L367–L397。 [上游固定提交](https://github.com/FluxGarage/RoboEyes/blob/b42f8e596535234932be3514ac7a813d4ced0046/src/FluxGarage_RoboEyes.h#L367-L397)；提交 `b42f8e596535234932be3514ac7a813d4ced0046`。
- [AlbertMicro.ino](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/05_AlbertMicro%E6%9C%BA%E5%99%A8%E5%B0%8F%E7%8B%97/%E4%BB%93%E5%BA%93/thinking0things__AlbertMicro/AlbertMicro.ino>)：`roboEyes.begin`，L508–L538。 [上游固定提交](https://github.com/thinking0things/AlbertMicro/blob/8d0ae147e967c798469a551c1dc49da781fc5587/AlbertMicro.ino#L508-L538)；提交 `8d0ae147e967c798469a551c1dc49da781fc5587`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
