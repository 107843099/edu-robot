# -*- coding: utf-8 -*-
"""下载 B站 init 分片(#EXT-X-MAP) 分析 moov：找音频 track 配置(ASC/采样率/track_id)"""
import re
import socket
import struct
import urllib.request

socket.setdefaulttimeout(10)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
BASE = "https://cn-lnsy-cu-01-04.bilivideo.com/live-bvc/105790/live_get06_SbWUXqR_5bn36_minihevc/index.m3u8?expires=1786734422&len=0&oi=720079484&pt=html5&qn=250&trid=10073d6e215f615df1f2339899ff7c6a7f59&bmt=2&sigparams=cdn,expires,len,oi,pt,qn,trid,bmt&cdn=cn-gotcha01&sign=bbbbce95e317840f497016638bcad1d5&site=cc90a082c1f4d121749424873c7941aa&free_type=0&mid=0&sche=ban&bvchls=1&sid=cn-lnsy-cu-01-04&chash=1&sg=lr&trace=8388641&isp=cu&rg=Central&pv=Henan&media_type=0&sl=2&deploy_env=prod&strategy_types=0,1&hot_cdn=909705&flvsk=8962a384f71263fade544d380bffd9eb&suffix=minihevc&ld=jchz&score=55&codec=1&strategy_id=25&hdr_type=0&strategy_ids=25,122&p2p_type=-1&strategy_type=0&origin_bitrate=920&expected_qn=250&source=puv3_onetier&pp=rtmp&info_source=cache&sk=b47ae0b83de4e4ef54530695dbae0c6e&vd=nc&zoneid_l=151388162&sid_l=live_get06_SbWUXqR_5bn36_minihevc&src=puv3&order=1"

def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://live.bilibili.com/"}), timeout=10)

def rel(base, seg):
    if seg.startswith("http"):
        return seg
    if seg.startswith("/"):
        m = re.match(r'(https?://[^/]+)', base)
        return (m.group(1) + seg) if m else (base + seg)
    return base[:base.rfind("/") + 1] + seg

# m3u8 → 找 #EXT-X-MAP
r = get(BASE)
m3u8 = r.read().decode("utf-8", "replace")
r.close()
m = re.search(r'#EXT-X-MAP:URI="([^"]+)"', m3u8)
if not m:
    print("无 #EXT-X-MAP"); raise SystemExit
init_name = m.group(1)
init_url = rel(BASE, init_name)
print(f"init 分片: {init_url.split('?')[0][-60:]}")

r = get(init_url)
data = r.read(400000)
r.close()
print(f"init {len(data)}B 开头 {data[:32].hex()}")

# 递归遍历 box，找 moov/trak/mdia/hdlr(音频)/stsd/mp4a/esds
def walk(data, start, end, depth=0, path=""):
    p = start
    while p + 8 <= end:
        size = struct.unpack(">I", data[p:p+4])[0]
        btype = data[p+4:p+8].decode("latin1")
        h = 8
        if size == 1:
            size = struct.unpack(">Q", data[p+8:p+16])[0]
            h = 16
        elif size == 0:
            size = end - p
        if size < h:
            break
        full = path + "/" + btype
        print("  " * depth + f"{full} (off={p} size={size})")
        if btype == "hdlr":
            handler = data[p+16:p+20].decode("latin1", "replace")
            print("  " * (depth+1) + f"handler={handler}")
        elif btype == "mp4a" or btype == "esds":
            pass
        # 音频 stsd entry
        if btype == "mp4a":
            print("  " * (depth+1) + f"mp4a: data={data[p+8:p+40].hex()}")
        if btype == "esds":
            # 里面是 ES_Descriptor → DecoderSpecificInfo (ASC)
            blob = data[p+8:p+size]
            idx = blob.find(b"\x05\x80\x80\x80")  # DecoderSpecificInfo tag
            if idx < 0:
                idx = blob.find(b"\x05")
            print("  " * (depth+1) + f"esds data={blob[:60].hex()}")
            # 找 ASC（2-4 字节）
            asc_idx = blob.find(b"\x11\x90")  # 48k stereo 常见
            if asc_idx < 0:
                asc_idx = blob.find(b"\x12\x10")
            if asc_idx >= 0:
                print("  " * (depth+1) + f"疑似 ASC: {blob[asc_idx:asc_idx+4].hex()}")
        if size > h and p + h < end:
            walk(data, p + h, p + size, depth + 1, full)
        p += size
        if depth > 4:
            break

walk(data, 0, len(data))
