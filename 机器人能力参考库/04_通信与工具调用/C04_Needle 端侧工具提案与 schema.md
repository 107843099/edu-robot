# C04 Needle 端侧工具提案与 schema

复用等级：**原环境可调用；新硬件需核对**。硬件：支持的电脑/移动原生运行时＋对应模型与ABI。语言：Python。

关联项目：[17 Needle端侧模型](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/17_Needle%E7%AB%AF%E4%BE%A7%E6%A8%A1%E5%9E%8B/README.md>)。

检索词：工具调用、tool calling、schema、自然语言、端侧模型。依赖：needle 3.1.0、原生引擎、模型权重、tool schema。

## 怎么实现

@tool与build_schema 根据签名、注解、docstring和Field约束构造JSONSchema。Needle.complete生成function_calls提案，不自动执行Python函数。模型、generation、原生共享库与token/工具索引配套决定是否可推理。

## 如何调用

在支持环境给有限工具schema创建Needle，complete(文本)后读取函数名/arguments，检查白名单、枚举与范围，再由自己的机器人dispatcher调用实际固件接口。

## 移植与提取范围

可将E01/M06/C01等稳定能力包装为set_expression或nod提案工具；这些工具是待建适配器名字，不是库中自带机器人功能。先从少量枚举和固定次数开始。

## 限制与核对点

SDK为Apache-2.0；模型/原生运行资源另核对。C3不是当前Python/原生ABI目标。已有离线主机试验不证明中文识别效果，也不证明机器人动作被执行。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [tools.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/17_Needle%E7%AB%AF%E4%BE%A7%E6%A8%A1%E5%9E%8B/%E4%BB%93%E5%BA%93/cactus-compute__needle/needle/agent/tools.py>)：`def tool(`，L173–L180。 [上游固定提交](https://github.com/cactus-compute/needle/blob/8881c1ceada54814465fa5edddc6599f32383985/needle/agent/tools.py#L173-L180)；提交 `8881c1ceada54814465fa5edddc6599f32383985`。
- [tools.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/17_Needle%E7%AB%AF%E4%BE%A7%E6%A8%A1%E5%9E%8B/%E4%BB%93%E5%BA%93/cactus-compute__needle/needle/agent/tools.py>)：`def build_schema`，L120–L150。 [上游固定提交](https://github.com/cactus-compute/needle/blob/8881c1ceada54814465fa5edddc6599f32383985/needle/agent/tools.py#L120-L150)；提交 `8881c1ceada54814465fa5edddc6599f32383985`。
- [__init__.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/17_Needle%E7%AB%AF%E4%BE%A7%E6%A8%A1%E5%9E%8B/%E4%BB%93%E5%BA%93/cactus-compute__needle/needle/__init__.py>)：`def complete(`，L266–L296。 [上游固定提交](https://github.com/cactus-compute/needle/blob/8881c1ceada54814465fa5edddc6599f32383985/needle/__init__.py#L266-L296)；提交 `8881c1ceada54814465fa5edddc6599f32383985`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
