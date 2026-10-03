# E02 TinyEngineer 独立 16 种位图表情

复用等级：**可单独提取；需接入驱动**。硬件：纯 C++ 输出 128×32 单色帧；可适配 OLED。语言：C++。

关联项目：[16 TinyEngineer桌面编程机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)、[15 小纸壳机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/15_%E5%B0%8F%E7%BA%B8%E5%A3%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：位图、bitmap、哭泣、思考、单眼眨眼、表情库。依赖：TinyEngineerExpressions、显示驱动。

## 怎么实现

独立库将枚举和经过整理的帧资产封装起来。每种表情 30 帧，每帧 100ms，循环 3 秒；render 按 elapsedMs 计算帧并把结果写入调用者缓冲区。它不拥有显示设备或计时器，适合从整机工程中单独取出。

## 如何调用

tiny_engineer::expressions::render(Expression::Happy, elapsedMs, buffer, sizeof(buffer)) 返回 bool。缓冲区至少 512 字节，128×32、逐行 MSB 在前，可交给 GFX drawBitmap。name() 将枚举转为名字。

## 移植与提取范围

提取 lib/TinyEngineerExpressions 的完整源码和资产头，不只复制声明。128×64 OLED 可在 y=16 居中；若要纵向拉伸，应另写尺寸转换。外部负责切换时重置动画起点，并选择刷新周期。

## 限制与核对点

独立示例 expression-demo 与整机默认 classic 眼睛不是同一显示路线。render 失败时不能把旧缓冲区当新帧。软件 MIT 与仓库结构文件许可范围分别核对。此前主机帧检查不等于 OLED 实物验证。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [TinyEngineerExpressions.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/jamro__tiny-engineer/lib/TinyEngineerExpressions/src/TinyEngineerExpressions.h>)：`enum class Expression`，L25–L55。 [上游固定提交](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/lib/TinyEngineerExpressions/src/TinyEngineerExpressions.h#L25-L55)；提交 `d71eb42a7abd98d81aae17472f35ba9d55ef5c89`。
- [TinyEngineerExpressions.h](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/jamro__tiny-engineer/lib/TinyEngineerExpressions/src/TinyEngineerExpressions.h>)：`bool render`，L62–L66。 [上游固定提交](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/lib/TinyEngineerExpressions/src/TinyEngineerExpressions.h#L62-L66)；提交 `d71eb42a7abd98d81aae17472f35ba9d55ef5c89`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
