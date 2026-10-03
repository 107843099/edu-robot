# C08 坦克 WebSocket、路径回放与超时停车

复用等级：**原环境可调用；新硬件需核对**。硬件：ESP-IDF网络固件＋浏览器控制台。语言：C/JavaScript。

关联项目：[18 桌面小坦克](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/18_%E6%A1%8C%E9%9D%A2%E5%B0%8F%E5%9D%A6%E5%85%8B/README.md>)。

检索词：WebSocket、500ms、断线、心跳、路径回放、NVS。依赖：esp_http_server、cJSON、FreeRTOS、NVS。

## 怎么实现

/ws 将收到的控制消息交给固件处理；命令时间戳由看门狗监视。配置默认超时500ms、任务周期100ms，超过时停车，但配网与未记录首条命令有例外。浏览器路径按Date.now计时，并发80ms心跳保持控制。

## 如何调用

消息内容为 {"left":30,"right":30}、{"stop":true} 或 {"speed":70}，不是 {linear,angular} JSON；解析器采用字符串查找。路径保存接口虽把steps写NVS，动作回放仍在浏览器；浏览器关闭不等于主控继续自主执行。

## 移植与提取范围

新轮式机器人可复用超时停车和时间戳设计；分开keepalive与改变目标，确保停止独立处理。路径部署到主控需要新增任务，不在现有行为内。

## 限制与核对点

一些速度/校准消息也更新时间戳，故超时不是严格“最后移动命令”。公开私钥已脱敏，HTTPS复刻需自己的证书；整体许可未明确。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [wifi_web_control.c](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/18_%E6%A1%8C%E9%9D%A2%E5%B0%8F%E5%9D%A6%E5%85%8B/%E6%9C%AC%E5%9C%B0%E8%B5%84%E6%96%99/%E6%A1%8C%E9%9D%A2%E5%9D%A6%E5%85%8B%E5%BC%80%E6%BA%90%E8%B5%84%E6%96%99/%E6%A1%8C%E9%9D%A2%E5%9D%A6%E5%85%8B%E5%BC%80%E6%BA%90%E8%B5%84%E6%96%99/2.ESP32%E6%BA%90%E7%A0%81/esp32_tank/main/wifi_web_control.c>)：`static esp_err_t ws_handler`，L784–L814。 本地材料，以索引中的 Git blob/文本校验哈希追踪。
- [wifi_web_control.c](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/18_%E6%A1%8C%E9%9D%A2%E5%B0%8F%E5%9D%A6%E5%85%8B/%E6%9C%AC%E5%9C%B0%E8%B5%84%E6%96%99/%E6%A1%8C%E9%9D%A2%E5%9D%A6%E5%85%8B%E5%BC%80%E6%BA%90%E8%B5%84%E6%96%99/%E6%A1%8C%E9%9D%A2%E5%9D%A6%E5%85%8B%E5%BC%80%E6%BA%90%E8%B5%84%E6%96%99/2.ESP32%E6%BA%90%E7%A0%81/esp32_tank/main/wifi_web_control.c>)：`static void watchdog_task(void *arg)`，L119–L149。 本地材料，以索引中的 Git blob/文本校验哈希追踪。
- [wifi_web_control.c](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/18_%E6%A1%8C%E9%9D%A2%E5%B0%8F%E5%9D%A6%E5%85%8B/%E6%9C%AC%E5%9C%B0%E8%B5%84%E6%96%99/%E6%A1%8C%E9%9D%A2%E5%9D%A6%E5%85%8B%E5%BC%80%E6%BA%90%E8%B5%84%E6%96%99/%E6%A1%8C%E9%9D%A2%E5%9D%A6%E5%85%8B%E5%BC%80%E6%BA%90%E8%B5%84%E6%96%99/2.ESP32%E6%BA%90%E7%A0%81/esp32_tank/main/wifi_web_control.c>)：`CONFIG_TANK_CMD_TIMEOUT_MS`，L1191–L1221。 本地材料，以索引中的 Git blob/文本校验哈希追踪。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
