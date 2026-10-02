# -*- coding: utf-8 -*-
"""精确解析 B站 init moov（音频 track/ASC）+ 分片 moof（trun sample 表）"""
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

# 精确 box 遍历：返回子 box 列表 [(type, offset, size)]
def children(data, start, end):
    out = []
    p = start
    while p + 8 <= end:
        size = struct.unpack(">I", data[p:p+4])[0]
        btype = data[p+4:p+8].decode("latin1", "replace")
        h = 8
        if size == 1:
            size = struct.unpack(">Q", data[p+8:p+16])[0]
            h = 16
        elif size == 0:
            size = end - p
        if size < h:
            break
        out.append((btype, p, p + size))
        p += size
    return out

# m3u8
r = get(BASE)
m3u8 = r.read().decode("utf-8", "replace")
r.close()
m = re.search(r'#EXT-X-MAP:URI="([^"]+)"', m3u8)
init_url = rel(BASE, m.group(1))
r = get(init_url)
init = r.read()
r.close()
print(f"init {len(init)}B")

# 遍历 init 找 moov
moov = None
for t, s, e in children(init, 0, len(init)):
    if t == "moov":
        moov = (s, e)
        break
print(f"moov @ {moov}")

audio_track_id = None
if moov:
    for t, s, e in children(init, moov[0], moov[1]):
        if t != "trak":
            continue
        # trak 里找 tkhd 的 track_id + mdia/hdlr
        tid = None
        handler = None
        for t2, s2, e2 in children(init, s, e):
            if t2 == "tkhd":
                # version 0: track_id @ +16 (4B)；version 1: @+20
                ver = init[s2+8]
                tid = struct.unpack(">I", init[s2 + (16 if ver == 0 else 20): s2 + (20 if ver == 0 else 24)])[0]
            elif t2 == "mdia":
                for t3, s3, e3 in children(init, s2, e2):
                    if t3 == "hdlr":
                        handler = init[s3+16:s3+20].decode("latin1", "replace")
                    elif t3 == "minf":
                        for t4, s4, e4 in children(init, s3, e3):
                            if t4 == "stbl":
                                for t5, s5, e5 in children(init, s4, e4):
                                    if t5 == "stsd":
                                        # entry: 4 size + 4 'mp4a'/'avc1'
                                        for t6, s6, e6 in children(init, s5 + 8, e5):
                                            codec = t6
                                            if codec in ("mp4a", "avc1", "hvc1", "hev1", "ac-3", "ec-3"):
                                                print(f"  trak_id={tid} handler={handler} codec={codec}")
                                                if codec == "mp4a":
                                                    audio_track_id = tid
                                                    # esds 里找 ASC
                                                    for t7, s7, e7 in children(init, s6, e6):
                                                        if t7 == "esds":
                                                            blob = init[s7+8:s7+e7]
                                                            # DecoderSpecificInfo: 05 80 80 80 len ... ASC
                                                            i = blob.find(b"\x05\x80\x80\x80")
                                                            if i >= 0:
                                                                asc = blob[i+5:i+9]
                                                                print(f"    esds ASC={asc.hex()}")
                                                                aot = (asc[0] >> 3) & 0x1F
                                                                sf = ((asc[0] & 7) << 1) | (asc[1] >> 7)
                                                                ch = (asc[1] >> 3) & 0x0F
                                                                sr = [96000,88200,64000,48000,44100,32000,24000,22050,16000,12000,11025,8000,7350]
                                                                print(f"    AOT={aot} sf_idx={sf}({sr[sf] if sf<len(sr) else '?'}Hz) ch={ch}")
                                        break

print(f"\n音频 track_id = {audio_track_id}")

# 下载第一个分片
lines = [l.strip() for l in m3u8.splitlines() if l.strip() and not l.startswith("#")]
seg_url = rel(BASE, lines[0])
r = get(seg_url)
seg = r.read(500000)
r.close()
print(f"\n分片 {len(seg)}B")

# 解析分片的 moof 们
pos = 0
while pos + 8 <= len(seg):
    size = struct.unpack(">I", seg[pos:pos+4])[0]
    btype = seg[pos+4:pos+8].decode("latin1", "replace")
    if size < 8 or size > len(seg):
        break
    if btype == "moof":
        print(f"\nmoof @{pos} size={size}")
        for t, s, e in children(seg, pos + 8, pos + size):
            if t == "traf":
                tfid = None
                default_sz = None
                trun_info = None
                for t2, s2, e2 in children(seg, s, e):
                    if t2 == "tfhd":
                        flags = struct.unpack(">I", seg[s2+12:s2+16])[0]
                        tfid = struct.unpack(">I", seg[s2+16:s2+20])[0]
                        off = s2 + 20
                        if flags & 0x1: off += 8
                        if flags & 0x2: off += 4
                        if flags & 0x8:
                            default_sz = struct.unpack(">I", seg[off:off+4])[0]
                            off += 4
                        if flags & 0x10:
                            default_sz = struct.unpack(">I", seg[off:off+4])[0]
                            off += 4
                        if flags & 0x20: off += 4
                        print(f"  traf: track={tfid} flags={flags:#x} default_sz={default_sz}")
                    elif t2 == "trun":
                        ver_flags = struct.unpack(">I", seg[s2+12:s2+16])[0]
                        n = struct.unpack(">I", seg[s2+16:s2+20])[0]
                        off = s2 + 20
                        data_off = None
                        if ver_flags & 0x1:
                            data_off = struct.unpack(">i", seg[off:off+4])[0]
                            off += 4
                        if ver_flags & 0x4: off += 4
                        sizes = []
                        for i in range(n):
                            if ver_flags & 0x100: off += 4  # duration
                            sz = 0
                            if ver_flags & 0x200:
                                sz = struct.unpack(">I", seg[off:off+4])[0]
                                off += 4
                            if ver_flags & 0x400: off += 4
                            if ver_flags & 0x800: off += 4
                            if sz:
                                sizes.append(sz)
                        trun_info = (n, data_off, sizes)
                        print(f"    trun: n={n} data_off={data_off} 前5个sample={sizes[:5]}")
    elif btype == "mdat":
        print(f"mdat @{pos} size={size}")
    pos += size
    if pos > 400000:
        break
