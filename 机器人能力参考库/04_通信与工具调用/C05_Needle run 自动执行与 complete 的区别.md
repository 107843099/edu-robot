# C05 Needle run 自动执行与 complete 的区别

复用等级：**原环境可调用；新硬件需核对**。硬件：Needle Python原生运行环境。语言：Python。

关联项目：[17 Needle端侧模型](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/17_Needle%E7%AB%AF%E4%BE%A7%E6%A8%A1%E5%9E%8B/README.md>)。

检索词：自动执行、run、dispatcher、function_calls、工具函数。依赖：Needle、Python可调用工具。

## 怎么实现

run 在complete之后循环处理 function_calls，将注册的Python函数按arguments真实调用，并把结果喂回下一轮。complete只返回提案；@tool只加schema元数据。这三个层级不能因都叫工具调用而混为一谈。

## 如何调用

需要自动执行时只注册已确定、有限参数的函数；机器人开发通常先complete，再经过显式dispatcher。函数内必须处理连接失败、命令结果、忙状态与停止，run不替你补齐硬件协议。

## 移植与提取范围

若要Codex快速复用，先从能力索引获取原函数签名和单位，再编写最薄的网络/串口适配。模型的动作名与固件预设白名单一一对应，避免生成任意角度或GPIO。

## 限制与核对点

run可触发外部效果；原代码的strict工具名检查不是完整动作权限/参数/时序系统。reset/close管理会话与引擎资源，不等同停止实体机器人。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [__init__.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/17_Needle%E7%AB%AF%E4%BE%A7%E6%A8%A1%E5%9E%8B/%E4%BB%93%E5%BA%93/cactus-compute__needle/needle/__init__.py>)：`def run(`，L326–L356。 [上游固定提交](https://github.com/cactus-compute/needle/blob/8881c1ceada54814465fa5edddc6599f32383985/needle/__init__.py#L326-L356)；提交 `8881c1ceada54814465fa5edddc6599f32383985`。
- [__init__.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/17_Needle%E7%AB%AF%E4%BE%A7%E6%A8%A1%E5%9E%8B/%E4%BB%93%E5%BA%93/cactus-compute__needle/needle/__init__.py>)：`def reset(`，L371–L401。 [上游固定提交](https://github.com/cactus-compute/needle/blob/8881c1ceada54814465fa5edddc6599f32383985/needle/__init__.py#L371-L401)；提交 `8881c1ceada54814465fa5edddc6599f32383985`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
