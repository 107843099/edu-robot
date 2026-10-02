# -*- coding: utf-8 -*-
"""测试 slider.kz 音乐源 - 已知提供真实MP3下载链接"""

import ssl, urllib.request, urllib.parse, json, sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

kw = '周杰伦'
encoded = urllib.parse.quote(kw)

print("="*60)
print(f"测试 slider.kz 搜索: {kw}")
print("="*60)

# 1. 搜索
url = f'https://slider.kz/vk_auth.php?q={encoded}&page=1&limit=5'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    resp = urllib.request.urlopen(req, timeout=10, context=ctx)
    data = json.loads(resp.read().decode('utf-8'))
    audios = data.get('audios', [])
    print(f"找到 {len(audios)} 首歌曲\n")
    
    for i, a in enumerate(audios[:5], 1):
        artist = a.get('artist', '?')
        title = a.get('title', '?')
        duration = a.get('duration', 0)
        aid = a.get('id', '')
        print(f"  {i}. {artist} - {title} [{duration}s] id: {aid[:30]}...")
    
    # 2. 测试下载第一首
    if audios:
        a = audios[0]
        artist = a.get('artist', '?')
        title = a.get('title', '?')
        aid = a.get('id', '')
        dl_url = f'https://slider.kz/download/{aid}'
        
        print(f"\n{'='*60}")
        print(f"下载测试: {artist} - {title}")
        print(f"URL: {dl_url[:100]}")
        
        req2 = urllib.request.Request(dl_url, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        resp2 = urllib.request.urlopen(req2, timeout=10, context=ctx)
        print(f"HTTP {resp2.status}")
        print(f"Content-Type: {resp2.headers.get('Content-Type', '?')}")
        print(f"Content-Length: {resp2.headers.get('Content-Length', '?')}")
        
        # 读取前8KB检测是否为MP3
        head = resp2.read(8192)
        if len(head) >= 4:
            is_id3 = head[:3] == b'ID3'
            is_mp3_frame = len(head) >= 2 and head[0] == 0xff and (head[1] & 0xe0) == 0xe0
            print(f"ID3v2头: {is_id3}")
            print(f"MPEG帧头: {is_mp3_frame}")
            if is_id3 or is_mp3_frame:
                print(f"\n✅ 确认为真实MP3文件! 下载大小: {len(head)} bytes")
                print(f"   源可用! 可用于 download_music.py")
            else:
                print(f"  前20字节 hex: {head[:20].hex()}")
        else:
            print(f"  响应太小: {len(head)} bytes")
            print(f"  内容: {head[:200]}")
            
except Exception as e:
    print(f"❌ 失败: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("测试完成")