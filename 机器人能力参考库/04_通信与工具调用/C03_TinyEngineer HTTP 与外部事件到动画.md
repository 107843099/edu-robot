# C03 TinyEngineer HTTP 与外部事件到动画

复用等级：**原环境可调用；新硬件需核对**。硬件：电脑事件钩子＋Tiny C3网络固件。语言：JavaScript/HTTP/C++。

关联项目：[16 TinyEngineer桌面编程机器人](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/README.md>)。

检索词：IDE事件、HTTP、anim、thinking、typing、auth。依赖：WebServer、animation controller、Node/Python钩子。

## 怎么实现

HTTP处理器从 name 参数解析 AnimationId，再交给状态控制器。电脑侧IDE/助手事件映射为 typing/reading/thinking等动画；持续状态需要刷新，结束时回none或相应完成状态。

## 如何调用

向设备 POST /anim?name=thinking，再用 GET /anim查询；启用token时遵守源码认证方式。setAnimation仍可能因1秒保持进入pending，不是请求即完成。

## 移植与提取范围

可直接在原固件上连接电脑事件；纸壳可复用事件名与路由模式，替换动作/眼睛注册表和硬件。把状态协议和IDE供应商事件转换分开。

## 限制与核对点

默认空token不提供访问限制。原代码不是通用LLM动作协议；n8n/YOVA关联项目需要另接适配，不因同作者便自动连通。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [anim_handlers.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/jamro__tiny-engineer/src/http/anim_handlers.cpp>)：`void handleAnimPost`，L30–L53。 [上游固定提交](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/http/anim_handlers.cpp#L30-L53)；提交 `d71eb42a7abd98d81aae17472f35ba9d55ef5c89`。
- [routes.cpp](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/16_TinyEngineer%E6%A1%8C%E9%9D%A2%E7%BC%96%E7%A8%8B%E6%9C%BA%E5%99%A8%E4%BA%BA/%E4%BB%93%E5%BA%93/jamro__tiny-engineer/src/http/routes.cpp>)：`/anim`，L6–L36。 [上游固定提交](https://github.com/jamro/tiny-engineer/blob/d71eb42a7abd98d81aae17472f35ba9d55ef5c89/src/http/routes.cpp#L6-L36)；提交 `d71eb42a7abd98d81aae17472f35ba9d55ef5c89`。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
