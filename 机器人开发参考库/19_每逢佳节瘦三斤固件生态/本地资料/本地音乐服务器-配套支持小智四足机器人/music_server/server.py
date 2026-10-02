"""
本地音乐服务器 - 供 ESP32 xiaozhi-esp32 播放本地曲库

直接浏览器打开即可使用。如果服务器在 192.168.3.7:8888，把下面示例中的
地址换成你的服务器 IP 和端口即可。

==================== 常用操作（浏览器直接打开） ====================

1. 查看所有歌曲（JSON格式）
   http://192.168.3.7:8888/api/list
   可选参数: ?page=1&page_size=20

2. 搜索歌曲（同时匹配歌手名和歌曲名）
   http://192.168.3.7:8888/api/search?keyword=周杰伦
   http://192.168.3.7:8888/api/search?keyword=青花瓷
   http://192.168.3.7:8888/api/search?keyword=海阔
   可选参数: &page=1&page_size=20

3. 播放在线试听（浏览器直接播放；MP3/FLAC/AAC/WAV/M4A 均可）
   http://192.168.3.7:8888/api/play/歌曲ID
   先通过 /api/list 或 /api/search 获取歌曲 ID

4. 查看歌词
   http://192.168.3.7:8888/api/lyrics/歌曲ID
   需有同名的 .lrc 文件（如 青花瓷.lrc）

5. 重新扫描曲库（在 music 目录添加/删除文件后执行）
   http://192.168.3.7:8888/api/rescan
   或者用命令行: curl -X POST http://192.168.3.7:8888/api/rescan

6. 健康检查
   http://192.168.3.7:8888/health

==================== 文件名规范 ====================
文件名格式: 歌名-歌手.扩展名（用半角减号 - 分隔）
  示例: 青花瓷-周杰伦.mp3
  示例: 海阔天空-Beyond.flac
  示例: 泡沫-邓紫棋.m4a
  示例: Beat_It-Michael_Jackson.wav

支持格式: .mp3 .flac .aac .wav .m4a（ESP32 全部直接解码播放，无需转码；OGG 不支持）
歌词文件: 歌曲名.lrc（和音乐文件放一起）

==================== ESP32 语音调用 ====================
对设备说"播放周杰伦的歌" → 自动搜索"周杰伦"
对设备说"搜索青花瓷" → 自动搜索"青花瓷"
对设备说"暂停" → 暂停播放
"""

import os
import sys
import struct
import argparse
import mimetypes
import hashlib
import subprocess
import asyncio
import shutil
from pathlib import Path
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ===================== 音乐管理器 =====================

class MusicManager:
    """管理本地音乐文件"""

    def __init__(self, music_dir: str = None):
        self.music_dir = music_dir or os.path.join(os.path.dirname(__file__), "music")
        self.songs: List[Dict] = []
        self._scan()

    def _scan(self):
        self.songs.clear()
        music_path = Path(self.music_dir)
        if not music_path.exists():
            music_path.mkdir(parents=True, exist_ok=True)
            return

        # ★ 2026-08-15 支持所有 ESP32 能直接解码的格式：mp3/flac/aac/wav/m4a
        #   （OGG 除外：esp_audio_codec 无 OGG 容器解析器，播不了，别扫进来）
        SUPPORTED_EXTS = {".mp3", ".flac", ".aac", ".wav", ".m4a"}
        for f in music_path.rglob("*"):
            if f.suffix.lower() in SUPPORTED_EXTS:
                info = self._extract_info(f)
                if info:
                    self.songs.append(info)

        self.songs.sort(key=lambda x: (x["artist"], x["title"]))

    @staticmethod
    def _normalize_for_search(text: str) -> str:
        """归一化文本用于模糊搜索：转小写，将分隔符统一替换为空格"""
        import re
        t = text.lower()
        # 将各种分隔符统一替换为空格
        t = re.sub(r'[_\-—–()（）\[\]【】,.，。、/\\|&]+', ' ', t)
        # 合并多个空格
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    def _extract_info(self, file_path: Path) -> Optional[Dict]:
        rel_path = file_path.relative_to(Path(self.music_dir))
        parts = rel_path.parts
        song_id = hashlib.md5(str(rel_path).encode("utf-8")).hexdigest()[:12]
        stem = file_path.stem

        artist = "未知歌手"
        title = stem

        # ★ 优先匹配 " - "（带空格的标准格式：歌手 - 歌名）
        if " - " in stem:
            parts_name = stem.split(" - ", 1)
            artist = parts_name[0].strip()
            title = parts_name[1].strip()
        # ★ 回退匹配 "-"（不带空格，实际文件格式：歌名-歌手）
        elif "-" in stem:
            parts_name = stem.rsplit("-", 1)
            if len(parts_name) == 2 and len(parts_name[0]) > 0 and len(parts_name[1]) > 0:
                # 实际文件全部是"歌名-歌手"格式，左边是歌名，右边是歌手
                title = parts_name[0].strip()
                artist = parts_name[1].strip()

        if len(parts) >= 2:
            dir_name = parts[0] if len(parts) == 2 else parts[-2]
            if artist == "未知歌手" or artist == stem:
                artist = dir_name

        lrc_path = file_path.with_suffix(".lrc")
        return {
            "id": song_id,
            "title": title,
            "artist": artist,
            "file": str(rel_path).replace("\\", "/"),
            "path": str(file_path),
            "format": file_path.suffix[1:].lower(),
            "has_lrc": lrc_path.exists(),
            "size": file_path.stat().st_size,
        }

    def search(self, keyword: str, page: int = 1, page_size: int = 20) -> Dict:
        if not keyword:
            return self.list_all(page, page_size)

        # ★ 模糊搜索：归一化关键词和歌曲信息后再匹配
        kw_norm = self._normalize_for_search(keyword)
        if not kw_norm:
            return self.list_all(page, page_size)

        results = []
        for s in self.songs:
            title_norm = self._normalize_for_search(s["title"])
            artist_norm = self._normalize_for_search(s["artist"])

            # 匹配条件：
            # 1. 归一化后的标题包含关键词
            # 2. 归一化后的歌手名包含关键词
            # 3. 原始标题包含关键词（精确子串匹配作为回退）
            if (kw_norm in title_norm or
                kw_norm in artist_norm or
                keyword.lower() in s["title"].lower() or
                keyword.lower() in s["artist"].lower()):
                results.append(s)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        return {"code": 200, "data": results[start:end], "total": total, "page": page, "page_size": page_size}

    def list_all(self, page: int = 1, page_size: int = 20) -> Dict:
        total = len(self.songs)
        start = (page - 1) * page_size
        end = start + page_size
        return {"code": 200, "data": self.songs[start:end], "total": total, "page": page, "page_size": page_size}

    def get_song(self, song_id: str) -> Optional[Dict]:
        for s in self.songs:
            if s["id"] == song_id:
                return s
        return None

    def get_lyrics(self, song_id: str) -> Optional[str]:
        song = self.get_song(song_id)
        if not song:
            return None
        music_path = Path(self.music_dir)
        # ★ 修复：用 with_suffix 替换扩展名，避免 rsplit 在特殊文件名上出错
        lrc_path = music_path / song["file"]
        lrc_path = lrc_path.with_suffix(".lrc")
        if lrc_path.exists():
            try:
                return lrc_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"  ⚠️ 读取歌词失败: {lrc_path}, 错误: {e}")
                return None
        # ★ 回退：尝试直接用歌曲名 + .lrc
        fallback = music_path / (Path(song["file"]).stem + ".lrc")
        if fallback.exists() and fallback != lrc_path:
            try:
                return fallback.read_text(encoding="utf-8")
            except Exception as e:
                print(f"  ⚠️ 读取歌词失败(回退): {fallback}, 错误: {e}")
                return None
        return None

    def get_file_path(self, song_id: str) -> Optional[str]:
        song = self.get_song(song_id)
        return song["path"] if song else None

    # ★ 2026-08-15 M4A/MP4 非 faststart 按段流式发送（供 ESP32 播放）：
    #   ESP32 的 es_parser（预编译库）不支持 mdat-before-moov 的 M4A。
    #   服务器不用 ffmpeg 转码，直接按 ftyp→moov→mdat 顺序把文件内容
    #   流式发出去，ESP32 收到的就是"看起来像 faststart 的流"，直接解码。
    #   返回读取段顺序 [(off,size),...]；faststart/非 M4A 返回 None（正常发原文件）。
    def get_faststart_order(self, path: str):
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".m4a", ".mp4"):
            return None
        try:
            boxes = []
            with open(path, "rb") as f:
                f.seek(0, 2)
                file_size = f.tell()
                f.seek(0)
                off = 0
                while off + 8 <= file_size:
                    f.seek(off)
                    hdr = f.read(8)
                    if len(hdr) < 8:
                        break
                    size, btype = struct.unpack(">I4s", hdr)
                    btype = btype.decode("latin1")
                    hdr_size = 8
                    if size == 1:
                        ext64 = f.read(8)
                        if len(ext64) < 8:
                            break
                        size = struct.unpack(">Q", ext64)[0]
                        hdr_size = 16
                    elif size == 0:
                        size = file_size - off
                    if size < hdr_size:
                        break
                    boxes.append((btype, off, size))
                    off += size
        except Exception:
            return None
        mdat_off = next((o for t, o, s in boxes if t == "mdat"), None)
        moov_off = next((o for t, o, s in boxes if t == "moov"), None)
        if mdat_off is None or moov_off is None or moov_off < mdat_off:
            return None  # faststart（moov 在前）或无法解析 → 正常发原文件
        order = []
        for t, o, s in boxes:
            if t == "ftyp":
                order.append((o, s))
        for t, o, s in boxes:
            if t == "moov":
                order.append((o, s))
        for t, o, s in boxes:
            if t == "mdat":
                order.append((o, s))
        for t, o, s in boxes:
            if t not in ("ftyp", "moov", "mdat"):
                order.append((o, s))
        return order

    def rescan(self):
        self._scan()


def iter_faststart(path: str, order) -> bytes:
    """按 ftyp→moov→mdat 顺序流式读取文件块，供 StreamingResponse 使用。"""
    try:
        with open(path, "rb") as f:
            for off, size in order:
                f.seek(off)
                remain = size
                while remain > 0:
                    chunk = f.read(min(65536, remain))
                    if not chunk:
                        break
                    yield chunk
                    remain -= len(chunk)
    except Exception:
        return


# ===================== FastAPI 应用 =====================

DEFAULT_PORT = 8888
DEFAULT_MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")

app = FastAPI(title="本地音乐服务器 - xiaozhi-esp32", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

music_manager: Optional[MusicManager] = None


@app.get("/health")
async def health():
    return {"status": "ok", "songs_count": len(music_manager.songs) if music_manager else 0}


@app.get("/api/list")
async def list_songs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    return music_manager.list_all(page, page_size)


@app.get("/api/search")
async def search(keyword: str = Query(""), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    print(f"  🔍 搜索关键字: {keyword}")  # 显示中文关键字
    return music_manager.search(keyword, page, page_size)


@app.get("/api/song/{song_id}")
async def get_song(song_id: str):
    song = music_manager.get_song(song_id)
    if not song:
        raise HTTPException(status_code=404, detail="歌曲不存在")
    return {"code": 200, "data": song}


@app.get("/api/lyrics/{song_id}")
async def get_lyrics_api(song_id: str):
    """获取歌词 - 返回纯文本 LRC 格式（无歌词返回 404）"""
    try:
        lyrics = music_manager.get_lyrics(song_id)
        if lyrics is None:
            raise HTTPException(status_code=404, detail="歌词不存在")
        from fastapi.responses import Response
        return Response(content=lyrics, media_type="text/plain; charset=utf-8")
    except HTTPException:
        raise
    except Exception as e:
        print(f"  ❌ 歌词接口异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/play/{song_id}")
async def play_song(song_id: str):
    file_path = music_manager.get_file_path(song_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="歌曲不存在")

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "audio/mpeg"

    # ★ 2026-08-15 非 faststart 的 M4A：按 ftyp→moov→mdat 顺序流式发送（免转码、免缓存）
    order = music_manager.get_faststart_order(file_path)
    if order:
        print(f"  🔧 M4A 非 faststart，按段流式发送: {os.path.basename(file_path)}")
        return StreamingResponse(
            iter_faststart(file_path, order),
            media_type=mime_type or "audio/mpeg",
        )

    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=os.path.basename(file_path),
        headers={"Accept-Ranges": "bytes"},
    )


@app.post("/api/rescan")
async def rescan():
    music_manager.rescan()
    return {"code": 200, "message": f"扫描完成，共 {len(music_manager.songs)} 首歌曲"}


@app.get("/api/stats")
async def stats():
    if not music_manager:
        return {"code": 200, "data": {"total": 0}}
    artists = {}
    for s in music_manager.songs:
        artists[s["artist"]] = artists.get(s["artist"], 0) + 1
    return {
        "code": 200,
        "data": {
            "total": len(music_manager.songs),
            "artists": len(artists),
            "artist_list": [{"name": k, "count": v} for k, v in sorted(artists.items())],
        },
    }


# ===================== 启动入口 =====================

def main():
    parser = argparse.ArgumentParser(description="本地音乐服务器")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"端口（默认: {DEFAULT_PORT}）")
    parser.add_argument("--music-dir", type=str, default=DEFAULT_MUSIC_DIR, help="音乐目录")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="绑定地址（默认: 0.0.0.0）")
    args = parser.parse_args()

    global music_manager
    music_manager = MusicManager(args.music_dir)

    server_ip = "本机IP"
    # 尝试获取本机IP
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        server_ip = s.getsockname()[0]
        s.close()
    except:
        pass

    print("=" * 60)
    print("  本地音乐服务器 - xiaozhi-esp32")
    print("=" * 60)
    print(f"  服务器: http://{server_ip}:{args.port}")
    print(f"  曲库:   {args.music_dir}")
    print(f"  歌曲:   {len(music_manager.songs)} 首")
    print()
    print("  ─── 网页端操作（复制到浏览器直接打开） ───")
    print()
    print(f"  [查看所有歌曲]")
    print(f"  http://{server_ip}:{args.port}/api/list")
    print()
    print(f"  [搜索歌曲 — 改 keyword= 后面的字即可]")
    print(f"  http://{server_ip}:{args.port}/api/search?keyword=周杰伦")
    print(f"  http://{server_ip}:{args.port}/api/search?keyword=青花瓷")
    print(f"  http://{server_ip}:{args.port}/api/search?keyword=海阔天空")
    print(f"  http://{server_ip}:{args.port}/api/search?keyword=邓紫棋")
    print()
    print(f"  [重新扫描曲库 - 添加/删除歌曲后执行]")
    print(f"  http://{server_ip}:{args.port}/api/rescan")
    print()
    print(f"  [在线试听 - 先通过 /api/list 获取歌曲 ID]")
    print(f"  http://{server_ip}:{args.port}/api/play/歌曲ID")
    print(f"  http://{server_ip}:{args.port}/api/lyrics/歌曲ID")
    print()
    print(f"  ─── 文件名示例（放在 music 文件夹，支持全格式） ───")
    print(f"  青花瓷-周杰伦.mp3")
    print(f"  海阔天空-BEYOND.flac")
    print(f"  泡沫-邓紫棋.m4a")
    print(f"  Beat_It-Michael_Jackson.wav")
    print(f"  支持格式: .mp3 .flac .aac .wav .m4a（ESP32 直接解码，无需转码；OGG 不支持）")
    print()
    print(f"  ─── 小工具（双击运行） ───")
    print(f"  下载所有歌词.bat     从网易云/QQ音乐抓取歌词")
    print(f"  查看歌词状态.bat     看哪些歌有/没有歌词")
    print(f"  搜索下载歌词.bat     只下载指定歌手的歌词")
    print(f"  转MP3格式.bat        旧歌转mp3备用（仅某些旧播放器需要）")
    print("=" * 60)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()