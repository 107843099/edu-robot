"""
音乐下载助手 - 下载MP3到本地曲库
源: 聚合搜索 + 酷狗音乐免费试听

搜索流程:
  1. 通过酷狗音乐开放API搜索歌曲
  2. 获取歌曲的免费试听MP3地址
  3. 下载MP3到本地 music/ 文件夹

用法:
  python download_music.py             交互模式
  python download_music.py 周杰伦      直接搜索
"""

import os
import sys
import json
import ssl
import re
import hashlib
import urllib.request
import urllib.parse
import time
import random

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
]

def get_headers(referer=None):
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': referer or 'https://www.baidu.com/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
    }


def search_kugou(keyword, max_results=15):
    """
    酷狗音乐搜索API
    
    酷狗提供开放的搜索接口，搜索返回song ID，
    再用play/getinfo接口获取真实的MP3播放地址。
    """
    url = 'http://mobilecdn.kugou.com/api/v3/search/song'
    params = {
        'format': 'json',
        'keyword': keyword,
        'page': 1,
        'pagesize': max_results,
        'showtype': 1,
        'platform': 'AndroidFilter',
        'version': 8000,
    }
    full_url = url + '?' + urllib.parse.urlencode(params)
    
    req = urllib.request.Request(full_url, headers=get_headers('http://kugou.com/'))
    resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    data = json.loads(resp.read().decode('utf-8'))
    
    songs = data.get('data', {}).get('info', [])
    results = []
    
    for song in songs:
        hash_val = song.get('hash', '')
        song_id = str(song.get('songid', ''))
        album_id = song.get('album_id', '')
        
        if not hash_val:
            continue
            
        results.append({
            'name': song.get('songname', '未知歌曲'),
            'singer': song.get('singername', '未知歌手'),
            'hash': hash_val,
            'id': song_id,
            'album_id': str(album_id),
            'duration': song.get('duration', 0),
            'source': 'kugou'
        })
    
    return results


def get_kugou_mp3_url(hash_val, album_id=''):
    """
    从酷狗获取真实MP3播放地址
    
    使用酷狗的 play/getinfo 接口获取带签名的MP3下载地址
    """
    # 构造key (酷狗的签名算法)
    key = hashlib.md5(hash_val.encode() + 'kgcloudv2'.encode()).hexdigest()
    
    url = 'http://trackercdn.kugou.com/i/v2/'
    params = {
        'hash': hash_val,
        'key': key,
        'pid': '1',
        'behavior': 'play',
        'cmd': '25',
        'version': '8000',
        'appid': '1005',
    }
    
    if album_id:
        params['album_id'] = album_id
    
    full_url = url + '?' + urllib.parse.urlencode(params)
    
    req = urllib.request.Request(full_url, headers=get_headers('http://kugou.com/'))
    resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    data = json.loads(resp.read().decode('utf-8'))
    
    play_urls = data.get('url', [])
    if play_urls:
        # 第一个就是MP3
        return play_urls[0]
    
    # 备用: 从 bitrate 中提取
    bitrates = data.get('bitrate', {})
    for br_key in ['320', '256', '192', '128', '64']:
        br_data = bitrates.get(br_key, {})
        br_url = br_data.get('url', '')
        if br_url:
            return br_url
    
    return None


def download_mp3(mp3_url, output_path):
    """下载MP3文件到本地"""
    req = urllib.request.Request(mp3_url, headers=get_headers())
    resp = urllib.request.urlopen(req, timeout=120, context=ctx)
    
    total_size = int(resp.headers.get('Content-Length', 0))
    
    with open(output_path, 'wb') as f:
        downloaded = 0
        chunk = resp.read(8192)
        
        # 检查是否是真实的MP3
        is_mp3 = chunk[:3] == b'ID3' or (chunk[0] == 0xff and chunk[1] & 0xe0 == 0xe0)
        
        if not is_mp3 and len(chunk) > 100:
            # 可能被重定向到网页，检查
            text = chunk.decode('utf-8', errors='replace')
            if 'html' in text.lower():
                print("  收到HTML而不是MP3")
                return 0
        
        while chunk:
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                pct = downloaded * 100 // total_size
                print("\r  下载进度: %d%% (%dKB/%dKB)" % (pct, downloaded//1024, total_size//1024), end="", flush=True)
            else:
                print("\r  已下载: %dKB" % (downloaded//1024), end="", flush=True)
            chunk = resp.read(8192)
    
    print()
    return downloaded


def interactive(keyword=None):
    print("=" * 50)
    print("  音乐下载助手 - 酷狗音乐 -> 本地曲库")
    print("=" * 50)
    print()

    if not keyword:
        keyword = input("请输入搜索关键词（歌手/歌名）: ").strip()
    if not keyword:
        print("已取消")
        return

    print("\n正在搜索: %s ...\n" % keyword)
    results = search_kugou(keyword)

    if not results:
        print("未找到相关歌曲，请换个关键词试试")
        return

    print("找到 %d 首歌曲:\n" % len(results))
    for i, r in enumerate(results, 1):
        print("  %d. %s - %s" % (i, r['singer'], r['name']))
        if r.get('duration'):
            mins = r['duration'] // 60
            secs = r['duration'] % 60
            print("     时长: %d:%02d" % (mins, secs))

    print("\n  0. 取消")
    print()

    choice = input("请选择要下载的歌曲 (1-%d): " % len(results)).strip()
    if not choice.isdigit():
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(results):
        return

    song = results[idx]

    # 输出到 music 目录
    music_dir = os.path.join(os.path.dirname(__file__), "music")
    os.makedirs(music_dir, exist_ok=True)

    def clean_name(s):
        return re.sub(r'[<>:"/\\|?*]', '', s)

    filename = "%s - %s.mp3" % (clean_name(song['singer']), clean_name(song['name']))
    output_path = os.path.join(music_dir, filename)

    # 检查是否已存在
    if os.path.exists(output_path):
        overwrite = input("\n文件已存在: %s\n  是否覆盖? (y/N): " % filename).strip().lower()
        if overwrite != 'y':
            print("已取消")
            return

    print("\n正在获取MP3下载地址...")
    mp3_url = get_kugou_mp3_url(song['hash'], song.get('album_id', ''))

    if not mp3_url:
        print("无法获取MP3下载地址（酷狗可能限制了此歌曲的试听）")
        return

    print("MP3地址: %s" % mp3_url[:120])
    print("\n下载中: %s - %s" % (song['singer'], song['name']))

    try:
        total = download_mp3(mp3_url, output_path)
        if total > 10240:  # 至少10KB才认为是有效的MP3
            print("\n\u2714 下载完成！保存在: %s (%dKB)" % (output_path, total//1024))
            print("   重启音乐服务器或调用 /api/rescan 即可看到新歌曲")
        else:
            print("\n\u26a0 文件太小 (%d字节)，可能不是有效的MP3，已删除" % total)
            if os.path.exists(output_path):
                os.remove(output_path)
    except Exception as e:
        print("\n\u2718 下载失败: %s" % e)


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        interactive(keyword)
    except KeyboardInterrupt:
        print("\n已取消")
    except Exception as e:
        print("\n错误: %s" % e)
        input("\n按回车键退出...")