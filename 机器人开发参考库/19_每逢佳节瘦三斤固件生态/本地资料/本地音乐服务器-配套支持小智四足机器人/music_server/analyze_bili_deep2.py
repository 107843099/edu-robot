# -*- coding: utf-8 -*-
"""精确分析 B站 init(stsd/hdlr) + 分片(moof/traf/trun)，确认音频 track"""
import re
import socket
import struct
import urllib.request

socket.setdefaulttimeout(10)
UA = "Mozilla/5.0"
BASE = "https://cn-lnsy-cu-01-04.bilivideo.com/live-bvc/105790/live_get06_SbWUXqR_5bn36_minihevc/index.m3u8?expires=1786734422&len=0&oi=720079484&pt=html5&qn=250&trid=10073d6e215f615df1f2339899ff7c6a7f59&bmt=2&sigparams=cdn,expires,len,oi,pt,qn,trid,bmt&cdn=cn-gotcha01&sign=bbbbce95e317840f497016638bcad1d5&site=cc90a082c1f4d121749424873c7941aa&free_type=0&mid=0&sche=ban&bvchls=1&sid=cn-lnsy-cu-01-04&chash=1&sg=lr&trace=8388641&isp=cu&rg=Central&pv=Henan&media_type=0&sl=2&deploy_env=prod&strategy_types=0,1&hot_cdn=909705&flvsk=8962a384f71263fade544d380bffd9eb&suffix=minihevc&ld=jchz&score=55&codec=1&strategy_id=25&hdr_type=0&strategy_ids=25,122&p2p_type=-1&strategy_type=0&origin_bitrate=920&expected_qn=250&source=puv3_onetier&pp=rtmp&info_source=cache&sk=b47ae0b83de4e4ef54530695dbae0c6e&vd=nc&zoneid_l=151388162&sid_l=live_get06_SbWUXqR_5bn36_minihevc&src=puv3&order=1"


def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://live.bilibili.com/"}), timeout=10)


def rel(base, seg):
    if seg.startswith("http"):
        return seg
    if seg.startswith("/"):
        m = re.match(r"(https?://[^/]+)", base)
        return m.group(1) + seg if m else base + seg
    return base[:base.rfind("/") + 1] + seg


r = get(BASE)
m3u8 = r.read().decode("utf-8", "replace")
r.close()
m = re.search(r'#EXT-X-MAP:URI="([^"]+)"', m3u8)
init = get(rel(BASE, m.group(1))).read()
print("init", len(init), "B")

# 打印所有 4cc 出现位置
for codec in [b"avc1", b"mp4a", b"hvc1", b"hev1", b"ac-3", b"ec-3", b"Opus", b"esds", b"stsd", b"hdlr", b"trak", b"tkhd"]:
    pos = 0
    while True:
        j = init.find(codec, pos)
        if j < 0:
            break
        print(f"  {codec.decode()} @ {j}")
        pos = j + 1

# 打印 hdlr handler
h = init.find(b"hdlr")
while h >= 0:
    print(f"  hdlr @{h} handler={init[h+16:h+20].decode('latin1','replace')}")
    h = init.find(b"hdlr", h + 1)

# stsd dump
i = init.find(b"stsd")
if i >= 0:
    print("  stsd @", i, "hex:", init[i:i + 96].hex())

# 分片
lines = [l.strip() for l in m3u8.splitlines() if l.strip() and not l.startswith("#")]
seg = get(rel(BASE, lines[0])).read()
print("\nseg", len(seg), "B 开头:", seg[:80].hex())

# 解析分片 moof 的 traf/tfhd/trun
pos = 0
while pos + 8 <= len(seg):
    size = struct.unpack(">I", seg[pos:pos+4])[0]
    btype = seg[pos+4:pos+8].decode("latin1", "replace")
    if size < 8 or pos + size > len(seg):
        break
    if btype == "moof":
        p = pos + 8
        end = pos + size
        while p + 8 <= end:
            s = struct.unpack(">I", seg[p:p+4])[0]
            t = seg[p+4:p+8].decode("latin1", "replace")
            if s < 8:
                break
            if t == "traf":
                tp = p + 8
                te = p + s
                while tp + 8 <= te:
                    ts = struct.unpack(">I", seg[tp:tp+4])[0]
                    tt = seg[tp+4:tp+8].decode("latin1", "replace")
                    if ts < 8:
                        break
                    if tt == "tfhd":
                        flags = struct.unpack(">I", seg[tp+12:tp+16])[0]
                        track_id = struct.unpack(">I", seg[tp+16:tp+20])[0]
                        o = tp + 20
                        dflt = None
                        if flags & 0x1: o += 8
                        if flags & 0x2: o += 4
                        if flags & 0x8:
                            dflt = struct.unpack(">I", seg[o:o+4])[0]; o += 4
                        if flags & 0x10:
                            dflt = struct.unpack(">I", seg[o:o+4])[0]; o += 4
                        if flags & 0x20: o += 4
                        print(f"  moof@{pos} traf: track={track_id} flags={flags:#x} default_size={dflt}")
                    elif tt == "trun":
                        vf = struct.unpack(">I", seg[tp+12:tp+16])[0]
                        n = struct.unpack(">I", seg[tp+16:tp+20])[0]
                        o = tp + 20
                        if vf & 0x1: o += 4
                        if vf & 0x4: o += 4
                        sizes = []
                        for _ in range(min(n, 8)):
                            if vf & 0x100: o += 4
                            if vf & 0x200:
                                sizes.append(struct.unpack(">I", seg[o:o+4])[0])
                                o += 4
                            if vf & 0x400: o += 4
                            if vf & 0x800: o += 4
                        print(f"     trun: n={n} flags={vf:#x} 前8sample={sizes}")
                    tp += ts
            p += s
    elif btype == "mdat":
        print(f"  mdat @{pos} size={size}")
    pos += size
