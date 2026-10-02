# -*- coding: utf-8 -*-
"""分析 B站直播 fMP4 分片结构：确认音频 track / AAC 采样方式"""
import re
import socket
import struct
import urllib.request

socket.setdefaulttimeout(10)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

URL = "https://cn-lnsy-cu-01-04.bilivideo.com/live-bvc/105790/live_get06_SbWUXqR_5bn36_minihevc/index.m3u8?expires=1786734422&len=0&oi=720079484&pt=html5&qn=250&trid=10073d6e215f615df1f2339899ff7c6a7f59&bmt=2&sigparams=cdn,expires,len,oi,pt,qn,trid,bmt&cdn=cn-gotcha01&sign=bbbbce95e317840f497016638bcad1d5&site=cc90a082c1f4d121749424873c7941aa&free_type=0&mid=0&sche=ban&bvchls=1&sid=cn-lnsy-cu-01-04&chash=1&sg=lr&trace=8388641&isp=cu&rg=Central&pv=Henan&media_type=0&sl=2&deploy_env=prod&strategy_types=0,1&hot_cdn=909705&flvsk=8962a384f71263fade544d380bffd9eb&suffix=minihevc&ld=jchz&score=55&codec=1&strategy_id=25&hdr_type=0&strategy_ids=25,122&p2p_type=-1&strategy_type=0&origin_bitrate=920&expected_qn=250&source=puv3_onetier&pp=rtmp&info_source=cache&sk=b47ae0b83de4e4ef54530695dbae0c6e&vd=nc&zoneid_l=151388162&sid_l=live_get06_SbWUXqR_5bn36_minihevc&src=puv3&order=1"

def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://live.bilibili.com/"}), timeout=10)

def rel(base, seg):
    if seg.startswith("http"):
        return seg
    if seg.startswith("/"):
        m = re.match(r'(https?://[^/]+)', base)
        return (m.group(1) + seg) if m else (base + seg)
    return base[:base.rfind("/") + 1] + seg

# 1) m3u8 完整内容
print("=== B站 m3u8 内容 ===")
r = get(URL)
m3u8 = r.read().decode("utf-8", "replace")
r.close()
print(m3u8)

# 找第一个分片
lines = [l.strip() for l in m3u8.splitlines() if l.strip() and not l.startswith("#")]
if not lines:
    print("无分片"); raise SystemExit
seg_url = rel(URL, lines[0])

# 2) 下载 fMP4 分片
print(f"\n=== 分片: {seg_url.split('?')[0][-70:]} ===")
r = get(seg_url)
data = r.read(400000)
r.close()
print(f"分片 {len(data)}B 开头 {data[:32].hex()}")

# 3) 解析顶层 box
pos = 0
boxes = []
while pos + 8 <= len(data):
    size = struct.unpack(">I", data[pos:pos+4])[0]
    btype = data[pos+4:pos+8].decode("latin1")
    hdr = 8
    if size == 1:
        size = struct.unpack(">Q", data[pos+8:pos+16])[0]
        hdr = 16
    elif size == 0:
        size = len(data) - pos
    if size < hdr:
        break
    boxes.append((btype, pos, size))
    print(f"  box: {btype} off={pos} size={size}")
    pos += size
    if len(boxes) > 20:
        break

# 4) 解析 moof → traf → tfhd/trun（找音频 track 的 sample）
def parse_box(data, start, size, target):
    """在 box 内递归找 target 类型"""
    p = start + 8
    end = start + size
    while p + 8 <= end:
        s = struct.unpack(">I", data[p:p+4])[0]
        t = data[p+4:p+8].decode("latin1")
        h = 8
        if s == 1:
            s = struct.unpack(">Q", data[p+8:p+16])[0]
            h = 16
        if s < h:
            break
        if t == target:
            return p, s
        p += s
    return None, 0

for btype, bstart, bsize in boxes:
    if btype == "moof":
        print(f"\n=== moof @{bstart} ===")
        p = bstart + 8
        while p + 8 <= bstart + bsize:
            s = struct.unpack(">I", data[p:p+4])[0]
            t = data[p+4:p+8].decode("latin1")
            if s < 8:
                break
            if t == "traf":
                print(f"  traf @{p} size={s}")
                tp = p + 8
                while tp + 8 <= p + s:
                    ts = struct.unpack(">I", data[tp:tp+4])[0]
                    tt = data[tp+4:tp+8].decode("latin1")
                    if ts < 8:
                        break
                    if tt == "tfhd":
                        flags = struct.unpack(">I", data[tp+12:tp+16])[0]
                        track_id = struct.unpack(">I", data[tp+16:tp+20])[0]
                        print(f"    tfhd: track_id={track_id} flags={flags:#x}")
                    elif tt == "trun":
                        n = struct.unpack(">I", data[tp+16:tp+20])[0]
                        print(f"    trun: sample_count={n}")
                    tp += ts
            p += s

# 5) mdat 里看音频样本（找 ADTS 或 raw AAC）
print("\n=== mdat 分析 ===")
mdat = None
for btype, bstart, bsize in boxes:
    if btype == "mdat":
        mdat = data[bstart+8: bstart+bsize]
        break
if mdat:
    print(f"mdat {len(mdat)}B")
    # 音频样本通常很小，找 0xFFF (ADTS) 或小样本
    ff_count = sum(1 for i in range(min(len(mdat), 20000)-1) if mdat[i] == 0xFF and (mdat[i+1] & 0xF0) == 0xF0)
    print(f"  mdat 前20KB 含 ADTS 同步(0xFFF): {ff_count} 个")
    # 找 sample size 分布（音频样本通常 100-500B，视频更大）
    print(f"  mdat 开头 64B: {mdat[:64].hex()}")
