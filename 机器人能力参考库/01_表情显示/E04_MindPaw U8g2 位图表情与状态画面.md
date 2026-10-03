# E04 MindPaw U8g2 位图表情与状态画面

复用等级：**需要移植或配套运行环境**。硬件：ESP8266 Arduino＋128×64 OLED。语言：C++。

关联项目：[03 MindPaw机器狗](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/README.md>)。

检索词：U8g2、XBM、开心、愤怒、困惑、天气、时钟。依赖：U8g2、ArduinoJson、NTPClient。

## 怎么实现

emojiState 分支选择 hi、angry、error、dowhat、love、sick、yun 等 XBM 资产，再通过 firstPage()/nextPage() 的分页绘制刷新。另有天气、网络、时间和 logo 画面。状态改变时清屏；这套实现主要是静态图案切换。

## 如何调用

沿主循环设置 emojiState 后，由原绘制分支刷新。drawXBMP 的位排列与 GFX drawBitmap 不同；移植应使用 drawXBitmap 或转换位序。Agent 的 expression 数字必须和这一 switch 对照，不能只依据提示词标签猜实际图案。

## 移植与提取范围

提取 image.cpp 对应数组和显示分支，改成单独渲染函数；保持天气/NTP 等页面与机器人表情的所有权关系。迁移到 ESP32 时改 U8g2 构造器和 I2C 引脚。

## 限制与核对点

U8g2 在工程声明为 ^2.36.2；不是 RoboEyes 的参数绘制，也不是连续 GIF。软件、STL 与文档许可不同，按原项目说明核对。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [main.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/%E4%BB%93%E5%BA%93/ace-trump-tech__MindPaw/MindPaw_main/src/main.cpp>)：`switch (emojiState)`，L1760–L1790。 [上游固定提交](https://github.com/ace-trump-tech/MindPaw/blob/21c549252a60126a80874738626f1b8c36efc38c/MindPaw_main/src/main.cpp#L1760-L1790)；提交 `21c549252a60126a80874738626f1b8c36efc38c`。
- [main.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/03_MindPaw%E6%9C%BA%E5%99%A8%E7%8B%97/%E4%BB%93%E5%BA%93/ace-trump-tech__MindPaw/MindPaw_main/src/main.cpp>)：`u8g2.drawXBMP(0, 0, 128, 64, hi)`，L1767–L1797。 [上游固定提交](https://github.com/ace-trump-tech/MindPaw/blob/21c549252a60126a80874738626f1b8c36efc38c/MindPaw_main/src/main.cpp#L1767-L1797)；提交 `21c549252a60126a80874738626f1b8c36efc38c`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
