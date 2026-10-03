# E08 EMO 作者的 LVGL Lottie 动画实验

复用等级：**需要移植或配套运行环境**。硬件：ESP32-S3＋PSRAM＋LVGL9。语言：C。

关联项目：[10 EMO-Dot小豆机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/10_EMO-Dot%E5%B0%8F%E8%B1%86%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：Lottie、矢量动画、PSRAM、LVGL9。依赖：LVGL、Lottie/ThorVG。

## 怎么实现

示例创建 lv_lottie 对象，给每个对象分配外部 RAM 绘制缓冲，再绑定 toast、robot、rocket、cuppa 等动画数据。120×120×4 字节加对齐空间用于一个 ARGB 画布，多个对象会累加内存占用。

## 如何调用

核心调用为 lv_lottie_create、lv_lottie_set_buffer、lv_lottie_set_src_data；必须在 LVGL Lottie 功能和渲染依赖已启用的工程里使用，并由 LVGL 的定时处理推进。

## 移植与提取范围

可用于 S3 彩屏表情设计和资源管线参考；先做单对象试验、检查 malloc 返回值，明确缩放与刷新预算。C3 的纸壳方案优先位图或几何眼睛，不沿用 PSRAM 分配。

## 限制与核对点

这是作者单独实验仓，不等同 EMO-Dot 已发布固件的正式渲染内核。库和动画资产分别保留原许可；未进行嵌入式编译或性能测量。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [lv_example_lottie_1.c](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/10_EMO-Dot%E5%B0%8F%E8%B1%86%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/M-D-777__esp32_s3_lvgl9_lottie_test/main/lv_example_lottie_1.c>)：`lv_example_lottie_1`，L15–L45。 [上游固定提交](https://github.com/M-D-777/esp32_s3_lvgl9_lottie_test/blob/6bc01cad2a59cf061ddaf23847235f8f93e0e9b6/main/lv_example_lottie_1.c#L15-L45)；提交 `6bc01cad2a59cf061ddaf23847235f8f93e0e9b6`。
- [lv_example_lottie_1.c](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/10_EMO-Dot%E5%B0%8F%E8%B1%86%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/M-D-777__esp32_s3_lvgl9_lottie_test/main/lv_example_lottie_1.c>)：`lv_lottie_set_src_data`，L27–L57。 [上游固定提交](https://github.com/M-D-777/esp32_s3_lvgl9_lottie_test/blob/6bc01cad2a59cf061ddaf23847235f8f93e0e9b6/main/lv_example_lottie_1.c#L27-L57)；提交 `6bc01cad2a59cf061ddaf23847235f8f93e0e9b6`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
