# -*- coding: utf-8 -*-
"""深入分析歌曲宝详情页，提取真实MP3下载链接"""

import ssl, re, urllib.request, urllib.parse, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 测试几个不同的歌曲ID
test_ids = ['39466', '4195', '1986353106', '8475848']

for sid in test_ids[:2]:
    print(f"\n{'='*60}")
    print(f"分析歌曲ID: {sid}")
    print(f"{'='*60}")
    
    url = f'https://www.gequbao.com/music/{sid}'
    req = urllib.request.Request(url, headers={
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer':'https://www.gequbao.com/'
    })
    resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    html = resp.read().decode('utf-8', errors='replace')
    print(f"页面大小: {len(html)}")
    
    # 查找所有可能的链接模式
    patterns = [
        (r'audio_url\s*[:=]\s*[\'"]([^\'"]+)[\'"]', 'audio_url变量'),
        (r'<audio[^>]+src=[\'"]([^\'"]+)[\'"]', 'audio标签src'),
        (r'src=[\'"]([^\'"]+\.mp3[^\'"]*)[\'"]', '任何src中.mp3'),
        (r'href=[\'"]([^\'"]+\.mp3[^\'"]*)[\'"]', '任何href中.mp3'),
        (r'https?://[^\'"<\s]*\.mp3[^\'"<\s]*', '裸MP3 URL'),
        (r'url[\s]*[:=][\s]*[\'"]([^\'"]+)[\'"]', 'url变量'),
        (r'\.mp3', '.mp3出现位置'),
    ]
    
    for pat, desc in patterns:
        matches = re.findall(pat, html, re.IGNORECASE)
        if matches:
            print(f"\n  找到 ({desc}):")
            for m in matches[:5]:
                print(f"    {m[:150]}")

    # 查找可能的API端点
    api_urls = re.findall(r'https?://[^\'"<\s]*(?:api|download|play|music)[^\'"<\s]*', html)
    if api_urls:
        print(f"\n  可能API端点:")
        for u in api_urls[:5]:
            print(f"    {u[:120]}")

    # 查找JS中可能的关键变量
    for line in html.split('\n'):
        if any(kw in line.lower() for kw in ['audio_url', 'music_url', 'src_url', 'play_url', 'down_url']):
            print(f"\n  JS变量行: {line.strip()[:200]}")
    
    # 查找页面脚本标签
    scripts = re.findall(r'<script[^>]*>([^<]+)</script>', html)
    for sc in scripts:
        if any(kw in sc.lower() for kw in ['mp3', 'audio', 'music', 'play', 'src', 'url']):
            print(f"\n  脚本片段: {sc.strip()[:300]}")

print("\n\n=== 尝试歌曲宝下载API ===")
for sid in test_ids[:3]:
    # 歌曲宝有 /download/{id} 端点
    dl_url = f'https://www.gequbao.com/d/{sid}'
    req = urllib.request.Request(dl_url, headers={
        'User-Agent':'Mozilla/5.0',
        'Referer':f'https://www.gequbao.com/music/{sid}'
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        print(f"\nID {sid}: 状态 {resp.status} | 类型: {resp.headers.get('Content-Type','')} | 位置: {resp.headers.get('Location','无')}")
        data = resp.read()
        ct = resp.headers.get('Content-Type','')
        if 'audio' in ct or 'octet' in ct:
            print(f"  直接返回音频! 大小: {len(data)}")
        elif 'json' in ct:
            print(f"  JSON: {data.decode()[:200]}")
        elif 'html' in ct:
            # 查找重定向
            txt = data.decode('utf-8', errors='replace')
            loc = re.search(r'window\.location\s*=\s*[\'"]([^\'"]+)[\'"]', txt)
            if loc:
                print(f"  JS重定向: {loc.group(1)[:100]}")
            meta = re.search(r'<meta[^>]+url=[\'"]?([^\'"]+)[\'"]?', txt)
            if meta:
                print(f"  meta重定向: {meta.group(1)[:100]}")
            else:
                print(f"  未知HTML: {txt[:200]}")
        else:
            print(f"  其他类型: {len(data)} bytes")
    except urllib.error.HTTPError as e:
        print(f"  ID {sid}: HTTP {e.code}")
        # 检查是否被重定向到其他页面
        if e.code == 302 or e.code == 301:
            print(f"  重定向到: {e.headers.get('Location','?')}")