# A03 作者配套本地音乐检索与HTTP流服务

复用等级：**原环境可调用；新硬件需核对**。硬件：电脑/服务器Python＋匹配机器人音乐客户端。语言：Python。

关联项目：[19 每逢佳节瘦三斤固件生态](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/19_%E6%AF%8F%E9%80%A2%E4%BD%B3%E8%8A%82%E7%98%A6%E4%B8%89%E6%96%A4%E5%9B%BA%E4%BB%B6%E7%94%9F%E6%80%81/README.md>)。

检索词：音乐、MP3、歌词、FastAPI、检索、HTTP流。依赖：FastAPI、uvicorn、MusicManager。

## 怎么实现

MusicManager递归扫描mp3/flac/aac/wav/m4a，将文件名和路径转为可检索条目，用相对路径MD5前12字符做ID；歌词按basename匹配。FastAPI提供list/search/song/lyrics/play/stats，文件作为HTTP流返回。

## 如何调用

GET /api/search?keyword=...查询，GET /api/play/{song_id}播放；重新扫描用POST /api/rescan。客户端需要实现音乐获取和解码，源码包提到的app_musicplayer.h未提供，单启动服务器不能赋予任意小智固件播放功能。

## 移植与提取范围

可作为原型音频素材服务，接有限播放工具与字幕/表情事件。路径ID不是内容哈希，重命名会改变ID；本地文件格式仍需机器人解码器支持。

## 限制与核对点

服务默认0.0.0.0:8888、CORS*且无认证；部署配置按实际环境处理。M4A重排moov未修正所有偏移，不当作通用修复算法。项目整体许可未明确。

## 源码入口与固定版本

以下行段是符号附近的定位窗口，完整逻辑应继续阅读所属文件。

- [server.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/19_%E6%AF%8F%E9%80%A2%E4%BD%B3%E8%8A%82%E7%98%A6%E4%B8%89%E6%96%A4%E5%9B%BA%E4%BB%B6%E7%94%9F%E6%80%81/%E6%9C%AC%E5%9C%B0%E8%B5%84%E6%96%99/%E6%9C%AC%E5%9C%B0%E9%9F%B3%E4%B9%90%E6%9C%8D%E5%8A%A1%E5%99%A8-%E9%85%8D%E5%A5%97%E6%94%AF%E6%8C%81%E5%B0%8F%E6%99%BA%E5%9B%9B%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/music_server/server.py>)：`class MusicManager`，L69–L99。 本地材料，以索引中的 Git blob/文本校验哈希追踪。
- [server.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/19_%E6%AF%8F%E9%80%A2%E4%BD%B3%E8%8A%82%E7%98%A6%E4%B8%89%E6%96%A4%E5%9B%BA%E4%BB%B6%E7%94%9F%E6%80%81/%E6%9C%AC%E5%9C%B0%E8%B5%84%E6%96%99/%E6%9C%AC%E5%9C%B0%E9%9F%B3%E4%B9%90%E6%9C%8D%E5%8A%A1%E5%99%A8-%E9%85%8D%E5%A5%97%E6%94%AF%E6%8C%81%E5%B0%8F%E6%99%BA%E5%9B%9B%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/music_server/server.py>)：`@app.get("/api/search")`，L313–L343。 本地材料，以索引中的 Git blob/文本校验哈希追踪。
- [server.py](<../../%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%BC%80%E5%8F%91%E5%8F%82%E8%80%83%E5%BA%93/19_%E6%AF%8F%E9%80%A2%E4%BD%B3%E8%8A%82%E7%98%A6%E4%B8%89%E6%96%A4%E5%9B%BA%E4%BB%B6%E7%94%9F%E6%80%81/%E6%9C%AC%E5%9C%B0%E8%B5%84%E6%96%99/%E6%9C%AC%E5%9C%B0%E9%9F%B3%E4%B9%90%E6%9C%8D%E5%8A%A1%E5%99%A8-%E9%85%8D%E5%A5%97%E6%94%AF%E6%8C%81%E5%B0%8F%E6%99%BA%E5%9B%9B%E8%B6%B3%E6%9C%BA%E5%99%A8%E4%BA%BA/music_server/server.py>)：`@app.post("/api/rescan")`，L370–L400。 本地材料，以索引中的 Git blob/文本校验哈希追踪。

许可按源文件、所属仓库 LICENSE/NOTICE 与资源说明分别核对。此卡为静态源码与接口分析，未编译目标固件或驱动实体硬件。

[按需求找能力](<../%E9%9C%80%E6%B1%82%E6%9F%A5%E6%89%BE%E8%A1%A8.md>) · [调用示例与移植路线](<../%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B%E4%B8%8E%E7%A7%BB%E6%A4%8D%E8%B7%AF%E7%BA%BF.md>)
