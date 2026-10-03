# I02 TinyEngineer 表情与动作状态注册表

复用等级：**可单独提取；需接入驱动**。硬件：C3 Arduino＋Tiny五舵机显示系统。语言：C++。

关联项目：[16 TinyEngineer桌面编程机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：状态机、typing、reading、thinking、最短保持、pending。依赖：animation registry、eyes registry、settings、ServoWrapper。

## 怎么实现

ModeEntry 把同一状态的动作 start/update、眼睛 start/update 和 continuous 标志绑在一起。setAnimation 对换状态施加1秒最短保持，待执行状态仅保留最新 pending。重复持续状态刷新超时，不重新启动；超时转 attention。

## 如何调用

setAnimation(AnimationId::Thinking) 后循环 updateAnimation()，同时继续原 servo 和 eyes 更新。12个注册名可通过 HTTP或 IDE 钩子触发；none 会回 park，稳定后释放输出。

## 移植与提取范围

新机器人可复用注册表结构，替换各状态动作和眼睛实现。表达“思考”“完成”“错误”时应以实际事件触发，控制持续状态超时，避免每帧重启动画。

## 限制与核对点

1秒最短保持有意延迟普通状态切换；停止电机/舵机需独立即时路径。独立16表情库 E02 不等于这里12个状态，两张表用途不同。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [registry.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/jamro__tiny-engineer/src/animation/registry.cpp>)：`kModes`，L128–L158。 [上游固定提交](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/animation/registry.cpp#L128-L158)；提交 `d71eb42a7abd98d81aae17472f35ba9d55ef5c89`。
- [controller.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/jamro__tiny-engineer/src/animation/controller.cpp>)：`void setAnimation`，L85–L115。 [上游固定提交](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/animation/controller.cpp#L85-L115)；提交 `d71eb42a7abd98d81aae17472f35ba9d55ef5c89`。
- [controller.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/jamro__tiny-engineer/src/animation/controller.cpp>)：`void updateAnimation`，L147–L173。 [上游固定提交](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/animation/controller.cpp#L147-L173)；提交 `d71eb42a7abd98d81aae17472f35ba9d55ef5c89`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
