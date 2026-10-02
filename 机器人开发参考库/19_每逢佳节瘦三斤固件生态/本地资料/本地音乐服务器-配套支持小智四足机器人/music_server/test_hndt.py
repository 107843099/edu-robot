# -*- coding: utf-8 -*-
"""测试河南电台是否可播：不同请求头组合，TLS 是否被拒。"""
import ssl
import socket
import urllib.request
import urllib.error

URLS = [
    ("河南新闻广播", "https://stream.hndt.com/live/xinwen/playlist.m3u8"),
    ("河南交通广播", "https://stream.hndt.com/live/jiaotong/playlist.m3u8"),
    ("中国之声(对照)", "http://ngcdn001.cnr.cn/live/zgzs/index.m3u8"),
]

HEADER_SETS = [
    ("无Header", None),
    ("UA", {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}),
    ("UA+Referer", {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                     "Referer": "https://www.hndt.com/"}),
    ("UA+Origin", {"User-Agent": "Mozilla/5.0", "Origin": "https://www.hndt.com"}),
]

# 不验证证书的 context（用于区分"证书问题"还是"服务器拒绝"）
INSECURE_CTX = ssl.create_default_context()
INSECURE_CTX.check_hostname = False
INSECURE_CTX.verify_mode = ssl.CERT_NONE


def get(url, headers, use_secure_verify=True, timeout=15):
    req = urllib.request.Request(url, headers=headers or {})
    ctx = INSECURE_CTX if not use_secure_verify else ssl.create_default_context()
    return urllib.request.urlopen(req, timeout=timeout, context=ctx)


def fetch(url, headers, verify):
    resp = get(url, headers, verify)
    ct = resp.headers.get("Content-Type")
    data = resp.read(4000)
    resp.close()
    return ct, data


def test_one(name, url, hname, headers, verify=True):
    try:
        ct, data = fetch(url, headers, verify)
        ok = len(data) > 0
        preview = data.decode("utf-8", "replace")[:300].replace("\n", " | ")
        return (True, ct, len(data), preview)
    except urllib.error.HTTPError as e:
        return (False, f"HTTP {e.code}", 0, str(e.reason))
    except ssl.SSLError as e:
        return (False, "SSL", 0, f"{e.reason} ({e})")
    except socket.timeout:
        return (False, "TIMEOUT", 0, "15s 超时")
    except Exception as e:
        return (False, type(e).__name__, 0, str(e))


print("=" * 70)
for name, url in URLS:
    print(f"\n########## {name}  {url} ##########")
    for hname, headers in HEADER_SETS:
        ok, ct, n, preview = test_one(name, url, hname, headers)
        print(f"  [{hname}] -> {'✅' if ok else '❌'} {ct} ({n}B) {preview[:120]}")
    # 河南的额外试：不验证证书
    if "hndt" in url:
        for hname, headers in HEADER_SETS:
            ok, ct, n, preview = test_one(name, url, hname + "+免证书", headers, verify=False)
            print(f"  [{hname}+免证书] -> {'✅' if ok else '❌'} {ct} ({n}B) {preview[:120]}")

print("\n" + "=" * 70)
print("测试完成")
