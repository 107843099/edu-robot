# -*- coding: utf-8 -*-
"""测试各种音乐源能否获取真实MP3下载链接"""

import ssl, re, urllib.request, urllib.parse, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

kw = urllib.parse.quote('周杰伦')

# 1. 歌曲宝 HTML搜索页
print("="*60)
print("1. 歌曲宝 HTML搜索")
url = 'https://www.gequbao.com/s/' + kw
req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.gequbao.com/'})
resp = urllib.request.urlopen(req, timeout=15, context=ctx)
html = resp.read().decode('utf-8', errors='replace')
print(f"状态: {resp.status} | 大小: {len(html)}")

# 提取歌曲ID
ids = re.findall(r'/music/(\d+)', html)
unique_ids = list(dict.fromkeys(ids))
print(f"找到 {len(unique_ids)} 个歌曲ID: {unique_ids[:5]}")

# 2. 测试详情页提取MP3
if unique_ids:
    print("\n" + "="*60)
    sid = unique_ids[0]
    print(f"2. 测试歌曲详情页 #{sid}")
    url2 = f'https://www.gequbao.com/music/{sid}'
    req2 = urllib.request.Request(url2, headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.gequbao.com/'})
    resp2 = urllib.request.urlopen(req2, timeout=15, context=ctx)
    html2 = resp2.read().decode('utf-8', errors='replace')
    
    # 查找MP3链接
    m = re.search(r'audio_url\s*[:=]\s*[\'"]+([^\'"]+)[\'"]', html2, re.IGNORECASE)
    if m:
        print(f"audio_url: {m.group(1)[:100]}")
    m2 = re.search(r'<audio[^>]+src=[\'"]+([^\'"]+)[\'"]', html2, re.IGNORECASE)
    if m2:
        print(f"audio src: {m2.group(1)[:100]}")
    
    # 查找任何.mp3出现
    lines = [l.strip() for l in html2.split('\n') if '.mp3' in l]
    for l in lines[:3]:
        print(f"mp3行: {l[:200]}")
    
    # 查找下载按钮
    for l in html2.split('\n'):
        if 'download' in l.lower() and ('href' in l or 'url' in l):
            print(f"下载: {l.strip()[:200]}")

print("\n" + "="*60)
print("3. 测试aa1.cn (type=3)")
url3 = f'https://zj.v.api.aa1.cn/api/qqmusic/?type=3&q={kw}&num=3'
req3 = urllib.request.Request(url3, headers={'User-Agent':'Mozilla/5.0','Referer':'https://zj.v.api.aa1.cn/'})
try:
    resp3 = urllib.request.urlopen(req3, timeout=15, context=ctx)
    text3 = resp3.read().decode('utf-8', errors='replace')
    print(f"状态: {resp3.status} | 内容: {text3[:300]}")
except Exception as e:
    print(f"失败: {e}")

print("\n" + "="*60)
print("4. 测试uomg.com音乐")
url4 = f'https://api.uomg.com/api/rand.music?format=json&sort=热歌榜'
req4 = urllib.request.Request(url4, headers={'User-Agent':'Mozilla/5.0'})
try:
    resp4 = urllib.request.urlopen(req4, timeout=15, context=ctx)
    data4 = json.loads(resp4.read().decode('utf-8', errors='replace'))
    print(f"状态: {resp4.status} | 内容: {json.dumps(data4, ensure_ascii=False)[:300]}")
except Exception as e:
    print(f"失败: {e}")