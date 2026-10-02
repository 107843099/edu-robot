# -*- coding: utf-8 -*-
"""系统测试 CNR(央广) 各频道 m3u8 直播地址的可用性"""
import urllib.request
import socket

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      "Referer": "http://www.cnr.cn/"}

# 频道标识: (名称, 编号, 标识)
CHANNELS = [
    ("中国之声", 1, "zgzs"),
    ("经济之声", 2, "jjzs"),
    ("音乐之声", 3, "yyzs"),
    ("经典音乐广播", 4, "dszs"),
    ("中华之声", 5, "zhzs"),
    ("神州之声", 6, "szzs"),
    ("华夏之声", 7, "hxzs"),
    ("香港之声", 8, "xgzs"),
    ("文艺之声", 9, "wyzs"),
    ("老年之声", 10, "lnzs"),
    ("藏语广播", 11, "cyzs"),
    ("娱乐广播", 12, "ylgb"),
    ("维吾尔语广播", 13, "wyyzs"),
    ("中国乡村之声", 15, "xczs"),
    ("中国交通广播", 16, "gsgljtgb"),
    ("中国交通广播2", 16, "jtgb"),
    ("中国交通广播3", 16, "gsjtgb"),
]

def test(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=8)
        d = r.read(150)
        r.close()
        ct = r.headers.get("Content-Type", "?")
        return True, ct, d[:80]
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}", ""
    except socket.timeout:
        return False, "TIMEOUT", ""
    except Exception as e:
        return False, type(e).__name__, ""

print("=" * 80)
print("ngcdn00X.cnr.cn 频道批量探测（http/https）")
print("=" * 80)
for name, num, ch in CHANNELS:
    for scheme in ("http", "https"):
        url = f"{scheme}://ngcdn{num:03d}.cnr.cn/live/{ch}/index.m3u8"
        ok, info, preview = test(url)
        mark = "✅" if ok else "❌"
        print(f"  {mark} {name:<10} {url}  {info}")
        if ok:
            break
    else:
        pass
print()
print("=" * 80)
print("其他已知 CNR 直播域名/变体")
print("=" * 80)
alt_urls = [
    ("中国之声-https", "https://ngcdn001.cnr.cn/live/zgzs/index.m3u8"),
    ("音乐之声-httpn1", "http://ngcdn001.cnr.cn/live/yyzs/index.m3u8"),
    ("音乐之声-httpn3-http-alt", "http://ngcdn003.cnr.cn/live/yyzs/index.m3u8"),
    ("经典音乐-httpn4-http-alt", "http://ngcdn004.cnr.cn/live/dszs/index.m3u8"),
    ("中国交通-httpn16-http-alt", "http://ngcdn016.cnr.cn/live/gsgljtgb/index.m3u8"),
]
for name, url in alt_urls:
    ok, info, preview = test(url)
    mark = "✅" if ok else "❌"
    print(f"  {mark} {name:<18} {info}  {url}")
print("=" * 80)
print("完成")
