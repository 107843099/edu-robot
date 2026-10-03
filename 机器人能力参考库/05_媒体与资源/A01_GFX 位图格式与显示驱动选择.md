# A01 GFX 位图格式与显示驱动选择

复用等级：**可单独提取；需接入驱动**。硬件：Arduino Adafruit_GFX兼容屏幕。语言：C++。

关联项目：[01 芝麻机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/01_%E8%8A%9D%E9%BA%BB%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)、[03 MindPaw机器狗](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/README.md>)、[05 AlbertMicro机器小狗](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/05_AlbertMicro%E6%9C%BA%E5%99%A8%E5%B0%8F%E7%8B%97/README.md>)、[15 小纸壳机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/15_%E5%B0%8F%E7%BA%B8%E5%A3%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)、[16 TinyEngineer桌面编程机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：drawBitmap、drawXBitmap、SSD1306、SH1106、位序、framebuffer。依赖：Adafruit_GFX、Adafruit_SSD1306、Adafruit_SH110x、Adafruit_BusIO。

## 怎么实现

GFX提供几何和位图绘制，不直接代表屏幕控制器。drawBitmap逐行MSB在前；XBM低位在前，需drawXBitmap。SSD1306/SH110x管理控制器和显存传输，display把缓冲区送屏。

## 如何调用

先明确OLED型号、分辨率、I2C地址和reset脚，使用匹配驱动begin。帧循环clearDisplay→drawBitmap/drawXBitmap→display。Tiny128×32帧在128×64屏居中，芝麻为128×64；不要把page式OLED内存布局误当行式位图。

## 移植与提取范围

资源与渲染分离后可以跨项目借图案；转换要确认位序、宽度补齐、黑白极性、透明覆盖与帧时长。屏幕替换应改变驱动，而非到处修改表情逻辑。

## 限制与核对点

下载的Adafruit库包含原BSD/MIT许可和完整例子；GFX不能自动播放GIF。I2C带宽、芯片RAM和总线争用需目标机测试。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [Adafruit_GFX.cpp](<../%E9%80%9A%E7%94%A8%E5%BA%93%E6%BA%90%E7%A0%81/adafruit__Adafruit-GFX-Library/Adafruit_GFX.cpp>)：`void Adafruit_GFX::drawBitmap`，L974–L1004。 [上游固定提交](https://github.com/adafruit/Adafruit-GFX-Library/blob/ac6d7c3869a693d406f77b9bfcd486b0673169f0/Adafruit_GFX.cpp#L974-L1004)；提交 `ac6d7c3869a693d406f77b9bfcd486b0673169f0`。
- [Adafruit_GFX.cpp](<../%E9%80%9A%E7%94%A8%E5%BA%93%E6%BA%90%E7%A0%81/adafruit__Adafruit-GFX-Library/Adafruit_GFX.cpp>)：`void Adafruit_GFX::drawXBitmap`，L1108–L1138。 [上游固定提交](https://github.com/adafruit/Adafruit-GFX-Library/blob/ac6d7c3869a693d406f77b9bfcd486b0673169f0/Adafruit_GFX.cpp#L1108-L1138)；提交 `ac6d7c3869a693d406f77b9bfcd486b0673169f0`。
- [Adafruit_SSD1306.h](<../%E9%80%9A%E7%94%A8%E5%BA%93%E6%BA%90%E7%A0%81/adafruit__Adafruit_SSD1306/Adafruit_SSD1306.h>)：`void display`，L152–L182。 [上游固定提交](https://github.com/adafruit/Adafruit_SSD1306/blob/d94f699451d72286357cba7259055ffff2c2940b/Adafruit_SSD1306.h#L152-L182)；提交 `d94f699451d72286357cba7259055ffff2c2940b`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
