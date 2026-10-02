"""
歌词下载工具
自动扫描 music 目录下的 MP3 歌曲，从网上搜索并下载 LRC 歌词文件

使用方法:
  python download_lyrics.py                     # 下载所有歌曲的歌词
  python download_lyrics.py --keyword 周杰伦     # 只下载指定歌手/歌曲的歌词
  python download_lyrics.py --overwrite          # 覆盖已有的 .lrc 文件

依赖安装:
  pip install requests
"""

import os
import re
import sys
import json
import time
import hashlib
import argparse
import requests

# ==================== 配置 ====================

MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")
REQUEST_TIMEOUT = 10
SLEEP_BETWEEN_REQUESTS = 0.5  # 每次搜索间隔，避免被封

# ==================== 歌词 API（内置多个源，自动切换） ====================

class LyricFetcher:
    """歌词获取器 - 多源自动切换"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://music.163.com/",
        })

    def search(self, keyword: str, artist: str = "") -> list:
        """
        搜索歌曲，返回列表 [{"id": "...", "title": "...", "artist": "...", "source": "..."}]
        自动尝试多个来源
        """
        results = []

        # 源1: 网易云音乐搜索
        try:
            r = self.session.get(
                "https://music.163.com/api/search/get",
                params={"s": f"{artist} {keyword}".strip(), "type": 1, "offset": 0, "limit": 5},
                timeout=REQUEST_TIMEOUT
            )
            data = r.json()
            if data.get("code") == 200:
                for song in data.get("result", {}).get("songs", []):
                    artists = ",".join(a["name"] for a in song.get("artists", []))
                    results.append({
                        "id": str(song["id"]),
                        "title": song["name"],
                        "artist": artists,
                        "source": "netease"
                    })
        except Exception as e:
            print(f"  ⚠ 网易云搜索失败: {e}")

        if results:
            return results

        # 源2: QQ音乐搜索 (备用)
        try:
            r = self.session.get(
                "https://c.y.qq.com/soso/fcgi-bin/client_search_cp",
                params={
                    "w": f"{artist} {keyword}".strip(),
                    "format": "json",
                    "inCharset": "utf-8",
                    "outCharset": "utf-8",
                    "p": 1,
                    "n": 5,
                    "cr": 1,
                },
                timeout=REQUEST_TIMEOUT
            )
            # QQ音乐返回的是 jsonp，需要提取 JSON
            text = r.text
            match = re.search(r'\{.*\}', text)
            if match:
                data = json.loads(match.group())
                songs = (data.get("data", {})
                         .get("song", {})
                         .get("list", []))
                for song in songs:
                    singers = ",".join(s["name"] for s in song.get("singer", []))
                    results.append({
                        "id": str(song.get("mid", song.get("id", ""))),
                        "title": song.get("songname", ""),
                        "artist": singers,
                        "source": "qqmusic"
                    })
        except Exception as e:
            print(f"  ⚠ QQ音乐搜索失败: {e}")

        return results

    def get_lyric(self, song_id: str, source: str) -> str:
        """根据歌曲ID获取LRC歌词文本"""
        if source == "netease":
            return self._get_netease_lyric(song_id)
        elif source == "qqmusic":
            return self._get_qqmusic_lyric(song_id)
        return ""

    def _get_netease_lyric(self, song_id: str) -> str:
        """从网易云音乐获取歌词"""
        try:
            r = self.session.get(
                "https://music.163.com/api/song/lyric",
                params={"id": song_id, "lv": 1, "kv": 1, "tv": -1},
                timeout=REQUEST_TIMEOUT
            )
            data = r.json()
            if data.get("code") == 200:
                lrc_data = data.get("lrc", {})
                if lrc_data.get("lyric"):
                    return lrc_data["lyric"]
        except Exception as e:
            print(f"    ⚠ 网易云歌词下载失败: {e}")
        return ""

    def _get_qqmusic_lyric(self, song_mid: str) -> str:
        """从QQ音乐获取歌词"""
        try:
            # QQ音乐需要先获取歌曲ID
            r = self.session.get(
                "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg",
                params={
                    "songmid": song_mid,
                    "format": "json",
                    "inCharset": "utf-8",
                    "outCharset": "utf-8",
                },
                timeout=REQUEST_TIMEOUT
            )
            text = r.text
            match = re.search(r'\{.*\}', text)
            if match:
                data = json.loads(match.group())
                if data.get("code") == 0 and data.get("lyric"):
                    import base64
                    lyric = base64.b64decode(data["lyric"]).decode("utf-8")
                    return lyric
        except Exception as e:
            print(f"    ⚠ QQ音乐歌词下载失败: {e}")
        return ""


# ==================== 本地文件工具 ====================

def get_music_files(music_dir: str) -> list:
    """扫描目录获取所有音乐文件信息"""
    files = []
    for f in os.listdir(music_dir):
        if f.lower().endswith((".mp3", ".ogg", ".wav", ".flac", ".m4a")):
            filepath = os.path.join(music_dir, f)
            stem = os.path.splitext(f)[0]

            # 从文件名解析歌手和歌曲名
            artist = ""
            title = stem
            if " - " in stem:
                parts = stem.split(" - ", 1)
                artist = parts[0].strip()
                title = parts[1].strip()

            lrc_path = os.path.join(music_dir, stem + ".lrc")

            files.append({
                "filename": f,
                "stem": stem,
                "filepath": filepath,
                "artist": artist,
                "title": title,
                "lrc_path": lrc_path,
                "has_lrc": os.path.exists(lrc_path),
            })
    return files


def save_lyric(filepath: str, lyric_text: str) -> bool:
    """保存LRC歌词文件"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(lyric_text)
        return True
    except Exception as e:
        print(f"    ❌ 保存歌词失败: {e}")
        return False


def print_banner():
    """打印启动信息"""
    print("=" * 60)
    print("  歌词下载工具")
    print("=" * 60)
    print(f"  音乐目录: {MUSIC_DIR}")
    print("=" * 60)


def print_table(files):
    """打印歌曲列表"""
    if not files:
        print("  📭 没有找到音乐文件")
        return

    print(f"\n  📀 找到 {len(files)} 首歌曲:")
    print(f"  {'':2} {'歌曲名':<20} {'歌手':<16} {'歌词':<6}")
    print(f"  {'':2} {'─'*20} {'─'*16} {'─'*6}")
    for i, f in enumerate(files):
        lrc_flag = "✅" if f["has_lrc"] else "❌"
        title = f["title"][:18] if len(f["title"]) > 18 else f["title"]
        artist = f["artist"][:14] if len(f["artist"]) > 14 else f["artist"]
        print(f"  {i+1:2} {title:<20} {artist:<16} {lrc_flag}")
    print()


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="歌词下载工具 - 自动从网上获取LRC歌词")
    parser.add_argument("--keyword", "-k", type=str, default="",
                        help="只下载包含指定关键字的歌曲（歌手名/歌曲名）")
    parser.add_argument("--overwrite", "-o", action="store_true",
                        help="覆盖已有的 .lrc 文件")
    parser.add_argument("--index", "-i", type=int, default=None,
                        help="只下载指定序号（从 1 开始），用 --list 查看序号")
    parser.add_argument("--list", "-l", action="store_true",
                        help="列出歌曲并显示歌词状态，不下载")
    args = parser.parse_args()

    print_banner()

    # 获取所有歌曲
    files = get_music_files(MUSIC_DIR)
    print_table(files)

    if args.list:
        return

    if not files:
        print("  ❌ 没有找到音乐文件")
        return

    # 过滤
    if args.keyword:
        kw = args.keyword.lower()
        files = [f for f in files if kw in f["title"].lower() or kw in f["artist"].lower()]
        if not files:
            print(f"  ❌ 没有找到包含 '{args.keyword}' 的歌曲")
            return
        print(f"\n  🔍 过滤后剩余 {len(files)} 首:")
        for f in files:
            artist_str = f" - {f['artist']}" if f["artist"] else ""
            print(f"    {f['title']}{artist_str}")
        print()

    if args.index is not None:
        if args.index < 1 or args.index > len(files):
            print(f"  ❌ 序号无效，有效范围: 1-{len(files)}")
            return
        files = [files[args.index - 1]]

    # 下载歌词
    fetcher = LyricFetcher()
    success = 0
    failed = 0
    skipped = 0

    print(f"\n  📥 开始下载歌词...\n")

    for i, f in enumerate(files):
        # 已有歌词且不覆盖
        if f["has_lrc"] and not args.overwrite:
            print(f"  [{i+1}/{len(files)}] ⏭ {f['title']} - 已有歌词 (跳过)")
            skipped += 1
            continue

        # 确定搜索关键词
        keyword = f["title"]
        artist = f["artist"]

        artist_str = f" - {artist}" if artist else ""
        print(f"  [{i+1}/{len(files)}] 🔍 搜索: {keyword}{artist_str}")

        time.sleep(SLEEP_BETWEEN_REQUESTS)

        # 搜索歌曲
        results = fetcher.search(keyword, artist)

        if not results:
            # 只用歌曲名再搜一次
            results = fetcher.search(keyword)
            if not results:
                print(f"    ❌ 未找到匹配歌曲")
                failed += 1
                continue

        # 用第一个结果
        song = results[0]
        print(f"    ✅ 找到: {song['title']} - {song['artist']} ({song['source']})")

        time.sleep(SLEEP_BETWEEN_REQUESTS)

        # 获取歌词
        lyric = fetcher.get_lyric(song["id"], song["source"])

        if not lyric:
            # 尝试第二个结果
            if len(results) > 1:
                song = results[1]
                print(f"    🔄 尝试第二个结果: {song['title']} - {song['artist']}")
                lyric = fetcher.get_lyric(song["id"], song["source"])

        if lyric:
            # 保存
            if save_lyric(f["lrc_path"], lyric):
                print(f"    ✅ 歌词已保存: {os.path.basename(f['lrc_path'])}")
                success += 1
            else:
                failed += 1
        else:
            print(f"    ❌ 未找到歌词")
            failed += 1

    # 总结
    print(f"\n  {'='*50}")
    print(f"  下载完成!")
    total = success + failed + skipped
    print(f"  总计: {total} 首 | ✅ 成功: {success} | ❌ 失败: {failed} | ⏭ 跳过: {skipped}")

    if success > 0:
        print(f"\n  💡 提示: 重启音乐服务器后，歌词会自动生效")
        print(f"    cd {os.path.dirname(__file__)} && python server.py")


if __name__ == "__main__":
    main()