# E10 Otto 的 21 个 GIF 表情资源

复用等级：**可单独提取；需接入驱动**。硬件：ESP-IDF 资源组件；播放器需另接。语言：C。

关联项目：[09 Otto闪猫侠机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)、[08 小智语音机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/08_%E5%B0%8F%E6%99%BA%E8%AF%AD%E9%9F%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：21表情、GIF资源、neutral、thinking、winking。依赖：otto-emoji-gif-component、GIF播放器。

## 怎么实现

组件将 21 个具名 GIF 及元数据组织为 IDF 资源。名称表是 neutral、happy、laughing 等固定列表；get_count、get_name、get_version 提供资源查询。它本身没有完整的屏幕播放循环。

## 如何调用

使用 otto_emoji_gif_get_count() 和 otto_emoji_gif_get_name(i) 建立资源菜单，按组件 CMake 的嵌入方式取 GIF 字节，再交给原工程播放器。不能写一个 get_name 调用就认为 GIF 已被显示。

## 移植与提取范围

可在小智兼容 LCD 分支沿用相同情绪名，或者离线抽帧转换成纸壳 OLED 的单色帧。转换时保留时长、透明度处理、画幅与原资源许可。

## 限制与核对点

21 是此组件名称表的数量，不是所有小智板型通用表情数。C3/S3、静态/动态资源配置有条件区别，应核对 idf_component.yml 和显示实现。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [otto_emoji_gif.c](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/txp666__otto-emoji-gif-component/src/otto_emoji_gif.c>)：`gif_names[]`，L14–L32。 [上游固定提交](https://github.com/txp666/otto-emoji-gif-component/blob/970cf66906d7c30059faa2704e7002f06b8c3619/src/otto_emoji_gif.c#L14-L32)；提交 `970cf66906d7c30059faa2704e7002f06b8c3619`。
- [otto_emoji_gif.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/txp666__otto-emoji-gif-component/include/otto_emoji_gif.h>)：`otto_emoji_gif_get_name`，L23–L29。 [上游固定提交](https://github.com/txp666/otto-emoji-gif-component/blob/970cf66906d7c30059faa2704e7002f06b8c3619/include/otto_emoji_gif.h#L23-L29)；提交 `970cf66906d7c30059faa2704e7002f06b8c3619`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
