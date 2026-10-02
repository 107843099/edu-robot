# -*- coding: utf-8 -*-
"""深度分析歌曲宝播放机制 - 找到真实MP3下载地址"""

import ssl
import re
import urllib.request
import urllib.parse
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url, referer=None):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    if referer:
        headers['Referer'] = referer
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    return resp.read().decode('utf-8', errors='replace')

# 搜索周杰伦
html = fetch('https://www.gequbao.com/s/' + urllib.parse.quote('周杰伦'), 'https://www.gequbao.com/')
ids = list(dict.fromkeys(re.findall(r'/music/(\d+)', html)))
print("找到 %d 首歌曲" % len(ids))

# 分析第一个歌曲详情页
sid = ids[0]
print("\n%s" % ('='*60))
print("分析歌曲: %s" % sid)
detail = fetch('https://www.gequbao.com/music/%s' % sid, 'https://www.gequbao.com/s/')

# 提取appData - 注意转义
idx = detail.find("window.appData = JSON.parse(")
if idx >= 0:
    start = detail.find("'", idx) + 1
    end = detail.find("'", start)
    if start > 0 and end > start:
        app_data_str = detail[start:end]
        app_data_str = app_data_str.replace('\\u0022', '"')
        app_data_str = app_data_str.replace("\\'", "'")
        app_data = json.loads(app_data_str)
        print("appData: %s" % json.dumps(app_data, ensure_ascii=False, indent=2)[:500])

        play_id = app_data.get('play_id', '')
        mp3_id = app_data.get('mp3_id', '')
        print("\nmp3_id: %s" % mp3_id)
        print("play_id: %s..." % play_id[:50])

        # 尝试下载端点
        play_urls = [
            'https://www.gequbao.com/play/%s' % sid,
            'https://www.gequbao.com/play/%s' % mp3_id,
            'https://www.gequbao.com/down/%s' % sid,
            'https://www.gequbao.com/down/%s' % mp3_id,
        ]
        
        for url in play_urls:
            try:
                print("\n  尝试: %s" % url)
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': 'https://www.gequbao.com/music/%s' % sid
                })
                resp = urllib.request.urlopen(req, timeout=10, context=ctx)
                ct = resp.headers.get('Content-Type', '')
                print("  HTTP %d | Content-Type: %s" % (resp.status, ct))
                data = resp.read()
                is_mp3 = len(data) >= 3 and (data[:3] == b'ID3' or (data[0] == 0xff and data[1] & 0xe0 == 0xe0))
                if 'audio' in ct or 'octet' in ct or is_mp3:
                    print("  ** 这是MP3! 大小: %d bytes" % len(data))
                    print("  下载URL: %s" % url)
                    break
                else:
                    text = data.decode('utf-8', errors='replace')
                    print("  响应: %s" % text[:200])
                    # 查找重定向
                    loc_start = text.find("window.location = ")
                    if loc_start >= 0:
                        loc_end = text.find("'", loc_start + 18)
                        if loc_end >= 0:
                            redirect = text[loc_start+18:loc_end]
                            print("  JS重定向到: %s" % redirect[:100])
            except urllib.error.HTTPError as e:
                print("  HTTP %d" % e.code)
            except Exception as e:
                print("  错误: %s" % e)

        # 提取所有可能的链接
        print("\n  页面中的关键链接:")
        for line in detail.split('\n'):
            if '/down' in line or '/play' in line or 'audio' in line.lower() or '.mp3' in line.lower():
                print("    %s" % line.strip()[:200])

# 对3个ID都试一下
print("\n%s" % ('='*60))
print("所有歌曲ID的play_id长度:")
for sid_new in ids[:5]:
    url = 'https://www.gequbao.com/music/%s' % sid_new
    detail = fetch(url, 'https://www.gequbao.com/')
    idx = detail.find("window.appData = JSON.parse(")
    if idx >= 0:
        start = detail.find("'", idx) + 1
        end = detail.find("'", start)
        if start > 0 and end > start:
            data_str = detail[start:end]
            data_str = data_str.replace('\\u0022', '"').replace("\\'", "'")
            data = json.loads(data_str)
            pid = data.get('play_id', '')
            mid = data.get('mp3_id', '')
            print("  ID %s: mp3_id=%s, play_id长度=%d" % (sid_new, mid, len(pid)))