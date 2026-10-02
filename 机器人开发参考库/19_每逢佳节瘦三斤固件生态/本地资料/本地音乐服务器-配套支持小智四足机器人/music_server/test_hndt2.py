# -*- coding: utf-8 -*-
"""深入测试河南电台：chunklist / TS 分片 / TLS1.2-only(模拟ESP32)"""
import ssl
import socket
import urllib.request
import urllib.error
import re

BASE = "https://stream.hndt.com/live/xinwen"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}


def get(url, ctx=None, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    if ctx is None:
        ctx = ssl.create_default_context()
    return urllib.request.urlopen(req, timeout=timeout, context=ctx)


print("=" * 70)
print("1) 下载 master playlist")
master_url = BASE + "/playlist.m3u8"
data = get(master_url).read().decode("utf-8", "replace")
print(data)
m = re.search(r'([\w.]+\.m3u8)', data)
chunklist = m.group(1) if m else None
print(f"  → chunklist: {chunklist}")

if chunklist:
    print("\n2) 下载 chunklist:", chunklist)
    cl_url = BASE + "/" + chunklist
    cl = get(cl_url).read().decode("utf-8", "replace")
    print(cl[:600])
    ts_m = re.search(r'([\w.\-]+\.ts)', cl)
    if ts_m:
        ts_name = ts_m.group(1)
        print(f"\n3) 下载 TS 分片: {ts_name}")
        ts_url = BASE + "/" + ts_name
        ts = get(ts_url).read()
        print(f"   TS 大小: {len(ts)} 字节, 开头: {ts[:16].hex()}")
        is_ts = len(ts) > 4 and ts[0] == 0x47
        print(f"   是 TS 流(0x47开头)? {'✅' if is_ts else '❌'}")
        # TS 里找 ADTS AAC 帧
        adts = 0
        for i in range(len(ts) - 8):
            if ts[i] == 0xFF and (ts[i+1] & 0xF0) == 0xF0:
                adts += 1
                if adts > 3:
                    break
        print(f"   TS 中含 ADTS AAC 帧? {'✅ (找到)' if adts else '❌ 没有'}")
    else:
        print("   chunklist 里没找到 .ts（可能是别的格式）")

print("\n" + "=" * 70)
print("4) 模拟 ESP32：TLS 1.2-only（mbedtls 最高 TLS1.2）")
try:
    ctx12 = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx12.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx12.maximum_version = ssl.TLSVersion.TLSv1_2
    ctx12.check_hostname = False
    ctx12.verify_mode = ssl.CERT_NONE
    r = get(master_url, ctx=ctx12)
    d = r.read(200).decode("utf-8", "replace")
    print(f"  TLS1.2-only: ✅ 成功 ({len(d)}B): {d[:80]}")
except Exception as e:
    print(f"  TLS1.2-only: ❌ {type(e).__name__}: {e}")

print("\n5) 模拟 ESP32：HTTP/1.0 请求（很多嵌入式客户端默认）")
try:
    class HTTP10Handler(urllib.request.HTTPHandler):
        def http_request(self, req):
            req.has_host = True
            req.add_unredirected_header('Host', req.host)
            req.add_unredirected_header('Connection', 'close')
            req.add_unredirected_header('Accept-Encoding', 'identity')
            req.unverifiable = True
            return req
    opener = urllib.request.build_opener(HTTP10Handler())
    req = urllib.request.Request(master_url, headers=UA, method="GET")
    r = opener.open(req, timeout=15)
    d = r.read(200).decode("utf-8", "replace")
    print(f"  HTTP/1.0: ✅ 成功 ({len(d)}B): {d[:80]}")
except Exception as e:
    print(f"  HTTP/1.0: ❌ {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("完成")
