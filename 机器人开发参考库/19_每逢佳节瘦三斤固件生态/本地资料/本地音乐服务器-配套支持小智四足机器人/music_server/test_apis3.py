# -*- coding: utf-8 -*-
"""测试多个可用的音乐下载源 - 寻找有真实MP3直链的"""

import ssl, re, urllib.request, urllib.parse, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

kw = urllib.parse.quote('周杰伦')

print("="*60)
print("寻找有真实MP3直链的音乐源")
print("="*60)

sources = [
    # 1. slider.kz (知名免费MP3下载站)
    ("slider.kz 搜索", 
     f"https://slider.kz/vk_auth.php?q={kw}&page=1&limit=5", {}),
    
    # 2. myfreemp3 (另一个免费MP3站) 
    ("myfreemp3 搜索",
     f"https://myfreemp3.fun/search?q={kw}&page=1", {}),
    
    # 3. mp3juice (免费MP3下载)
    ("mp3juice 搜索",
     f"https://mp3juice.ing/search?q={kw}", {}),
    
    # 4. music.163.com 网易云直接搜索(公开)  
    ("网易云搜索",
     f"https://music.163.com/api/search/get/web?type=1&s={kw}&limit=5",
     {'Referer': 'https://music.163.com/'}),
     
    # 5. 聚合API - Vercel部署
    ("网抑云API (vercel)",
     f"https://music-5c4o.vercel.app/search?keyword={kw}&type=netease&limit=5",
     {'Referer': 'https://music.163.com/'}),
     
    # 6. 另一个unblock版本
    ("cloudflare unblock",
     f"https://music.unblock.workers.dev/search?keywords={kw}&limit=5",
     {'Referer': 'https://music.163.com/'}),

    # 7. 猫耳FM (bilibili旗下, 可能有公开API)
    ("猫耳FM搜索",
     f"https://api.maoermusic.com/search?keyword={kw}&page=1&size=5",
     {'Referer': 'https://maoermusic.com/'}),
]

for name, url, headers in sources:
    print(f"\n{'-'*60}")
    print(f"测试: {name}")
    print(f"URL: {url[:100]}")
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            **(headers or {})
        })
        resp = urllib.request.urlopen(req, timeout=20, context=ctx)
        text = resp.read().decode('utf-8', errors='replace')
        print(f"状态: {resp.status} | 大小: {len(text)}")
        
        # 检查是否JSON
        try:
            data = json.loads(text)
            print(f"JSON格式: 是")
            # 提取关键信息
            if isinstance(data, list):
                print(f"  数组长度: {len(data)}")
            elif isinstance(data, dict):
                print(f"  keys: {list(data.keys())[:8]}")
                # 查找可能包含URL的字段
                for k in data:
                    if isinstance(data[k], str) and ('mp3' in data[k] or 'music' in data[k] or 'url' in data[k].lower()):
                        print(f"  字段'{k}'含URL: {data[k][:100]}")
        except json.JSONDecodeError:
            print(f"JSON格式: 否")
            # 查找.mp3链接
            mp3s = re.findall(r'https?://[^"\'<\s]+\.mp3[^"\'<\s]*', text)
            if mp3s:
                print(f"  找到 {len(mp3s)} 个MP3链接!")
                for m in mp3s[:3]:
                    print(f"    {m[:120]}")
            else:
                print(f"  无MP3链接")
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e.code}")
        if e.code == 403:
            print("  可能被反爬")
    except Exception as e:
        print(f"失败: {type(e).__name__}: {str(e)[:100]}")

# 如果slider.kz成功，测试下载
print("\n\n" + "="*60)
print("如果slider.kz成功，测试MP3下载")
try:
    url = f'https://slider.kz/vk_auth.php?q={kw}&page=1&limit=3'
    req = urllib.request.Request(url, headers={
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    resp = urllib.request.urlopen(req, timeout=20, context=ctx)
    data = json.loads(resp.read().decode('utf-8', errors='replace'))
    if isinstance(data, dict) and data.get('audios'):
        audios = data['audios']
        print(f"slider.kz 找到 {len(audios)} 首歌")
        for i, audio in enumerate(audios[:3]):
            print(f"\n  歌曲{i+1}:")
            print(f"    标题: {audio.get('title','?')}")
            print(f"    歌手: {audio.get('artist','?')}")
            print(f"    时长: {audio.get('duration',0)}秒")
            # 构造下载URL
            if audio.get('url'):
                print(f"    URL: {audio['url'][:100]}")
            # slider.kz下载链接模式
            if audio.get('id'):
                dl_url = f"https://slider.kz/download/{audio['id']}"
                print(f"    下载链接: {dl_url}")
except Exception as e:
    print(f"slider.kz下载测试失败: {e}")