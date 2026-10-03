# C06 小智 Otto MCP 22动作与校准工具

复用等级：**原环境可调用；新硬件需核对**。硬件：Otto分支 ESP-IDF主控＋小智MCP协议。语言：C++/JSON。

关联项目：[09 Otto闪猫侠机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：MCP、self.otto.action、steps、speed、trim。依赖：McpServer、OttoController、动作任务、NVS。

## 怎么实现

注册表把22个action名映射到有限ActionType并QueueAction执行。还有servo_sequences、stop及trim保存等工具；Property约束steps、speed、amount、arm_swing、dir。MCP仅暴露实际注册项。

## 如何调用

调用self.otto.action，arguments包含action与需要的参数。steps1..100，speed100..3000是毫秒周期、越小越快；amount/arm_swing0..170，dir为1/-1/0。回中使用action="home"，不能据文档文字假定存在独立self.otto.home。

## 移植与提取范围

纸壳可以沿AddTool注册有限pan/tilt预设，但需自己的执行器、软限位和即时停止路径。不要把LLM输出直接传给servo_sequences，先有可验证的有限动作集合。

## 限制与核对点

工具名以源码注册表为准，中文描述不是API。stop回调涉及任务和回姿态，需保持原实现上下文；trim范围-50..50并保存NVS，不适用于所有新舵机。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [otto_controller.cc](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/txp666__xiaozhi-esp32/main/boards/otto-robot/otto_controller.cc>)：`self.otto.action`，L533–L563。 [上游固定提交](https://github.com/txp666/xiaozhi-esp32/blob/becc84f58908d96a8aaeae046dcd22e099aad7e9/main/boards/otto-robot/otto_controller.cc#L533-L563)；提交 `becc84f58908d96a8aaeae046dcd22e099aad7e9`。
- [otto_controller.cc](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/txp666__xiaozhi-esp32/main/boards/otto-robot/otto_controller.cc>)：`self.otto.stop`，L708–L738。 [上游固定提交](https://github.com/txp666/xiaozhi-esp32/blob/becc84f58908d96a8aaeae046dcd22e099aad7e9/main/boards/otto-robot/otto_controller.cc#L708-L738)；提交 `becc84f58908d96a8aaeae046dcd22e099aad7e9`。
- [otto_controller.cc](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/09_Otto%E9%97%AA%E7%8C%AB%E4%BE%A0%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/txp666__xiaozhi-esp32/main/boards/otto-robot/otto_controller.cc>)：`self.otto.servo_sequences`，L669–L699。 [上游固定提交](https://github.com/txp666/xiaozhi-esp32/blob/becc84f58908d96a8aaeae046dcd22e099aad7e9/main/boards/otto-robot/otto_controller.cc#L669-L699)；提交 `becc84f58908d96a8aaeae046dcd22e099aad7e9`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
