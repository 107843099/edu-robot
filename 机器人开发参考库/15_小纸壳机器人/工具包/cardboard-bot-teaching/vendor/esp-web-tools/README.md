# Vendored ESP Web Tools

设备选择补丁（2026-09-20）：安装按钮共用 ../../device-status.js 的原生 USB 候选筛选（303A:1001）和连接状态事件；不提供 COM 号，不以 USB 标识替代安装器芯片识别。升级 vendor 时保留此集成。

本目录包含 ESP Web Tools 10.1.0 的完整浏览器运行文件，供 index.html 通过相对路径加载。文件来源为官方 npm 发布包；许可证见 LICENSE。

本地补丁（2026-09-20）：显示准备阶段及芯片连接日志；串口关闭异常/8 秒超时显示错误并阻止进入刷写；固件资源读取使用 15 秒请求超时。manifest 用 new_install_improv_wait_time=0 跳过本项目不支持的 Improv 配网探测。修正 vendored esptool-js 将 115200 波特率误当重试次数的问题，连接最多尝试 7 轮；本项目仅筛选 303A:1001，并要求用户手动进入下载模式，因此连接时跳过自动 DTR/RTS 复位。SLIP 解析器会跳过同步包前的 ROM 启动文本并继续寻找 0xC0 包边界，保留 panic 文本检测；对应 esptool-js #239。连接阶段还会识别 `SPI_DOWNLOAD_BOOT / wait spi download`，立即停止重试并提示 GPIO8 / GPIO9 必须保持空闲、OLED 应使用 GPIO0 / GPIO1；不会把错误的 SPI 下载模式继续显示为无限 Connecting。未改变镜像地址或写入算法。

更新依赖版本时，请同步替换本目录的完整 dist/web 文件集，并重新做安装页面 Smoke Test。