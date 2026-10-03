# E09 曼波 OLED 图案与动作联动

复用等级：**需要移植或配套运行环境**。硬件：STM32F103＋软件 I2C OLED。语言：C。

关联项目：[02 曼波小狗](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/02_%E6%9B%BC%E6%B3%A2%E5%B0%8F%E7%8B%97/README.md>)。

检索词：曼波、BMP、OLED、动作表情、开心值、体力值。依赖：STM32标准外设库、OLED驱动、SYN6288。

## 怎么实现

Mode 函数先选择 BMP 图案，再调用运动函数、更新 previous_mode 和体力/开心变量。mode_happiness、mode_stamina 把数值、文字、TTS 和动作串起来。OLED_ShowImage 是将预存图案写入显示缓冲的入口。

## 如何调用

原模式内可用 OLED_ShowImage(0,0,128,64,BMP2)，刷新行为要按 OLED 实现确认。BMP1、BMP2 等是资源变量，不是稳定的语义枚举；完整模式包装包含 LED、TTS 和 Delay 依赖。

## 移植与提取范围

新机器人适合借鉴“事件→表情→动作→状态变化”的联动结构；把开心/体力更新与硬件行为解耦，给资源取明确语义名称。保留本地包与 GitHub 非阻塞版本两条路径的区别。

## 限制与核对点

这套模式包含长同步等待；不能把显示代码叫作通用异步动画库。部分源文件为 GBK，索引哈希按 UTF-8 解码文本另标明，原文件字节以 Git blob 为准。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [Mode.c](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/02_%E6%9B%BC%E6%B3%A2%E5%B0%8F%E7%8B%97/%E4%BB%93%E5%BA%93/RussellCooper-DJZ__manbo-robot-dog/User/Mode.c>)：`void mode_forward`，L38–L68。 [上游固定提交](https://github.com/RussellCooper-DJZ/manbo-robot-dog/blob/9a3d315cfe50a62d8e6221cccf2aea696f96aedc/User/Mode.c#L38-L68)；提交 `9a3d315cfe50a62d8e6221cccf2aea696f96aedc`。
- [Mode.c](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/02_%E6%9B%BC%E6%B3%A2%E5%B0%8F%E7%8B%97/%E4%BB%93%E5%BA%93/RussellCooper-DJZ__manbo-robot-dog/User/Mode.c>)：`void mode_happiness`，L418–L448。 [上游固定提交](https://github.com/RussellCooper-DJZ/manbo-robot-dog/blob/9a3d315cfe50a62d8e6221cccf2aea696f96aedc/User/Mode.c#L418-L448)；提交 `9a3d315cfe50a62d8e6221cccf2aea696f96aedc`。
- [OLED.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/02_%E6%9B%BC%E6%B3%A2%E5%B0%8F%E7%8B%97/%E4%BB%93%E5%BA%93/RussellCooper-DJZ__manbo-robot-dog/Hardware/OLED.h>)：`OLED_ShowImage`，L45–L64。 [上游固定提交](https://github.com/RussellCooper-DJZ/manbo-robot-dog/blob/9a3d315cfe50a62d8e6221cccf2aea696f96aedc/Hardware/OLED.h#L45-L64)；提交 `9a3d315cfe50a62d8e6221cccf2aea696f96aedc`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
