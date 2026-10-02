# -*- coding: utf-8 -*-
"""分析抖音 FLV：跳过 PreviousTagSize0 后解析 tags，确认 AAC"""
import socket
import urllib.request

socket.setdefaulttimeout(12)

URL = "https://pull-hs-f5.flive.douyincdn.com/thirdgame/stream-408133045733294858_ld.flv?expire=1787334013&sign=cb3d4e6bf8da502f43cca3bbde497dbf&volcSecret=cb3d4e6bf8da502f43cca3bbde497dbf&volcTime=1787334013&arch_hrchy=w1&exp_hrchy=w1&major_anchor_level=common&rtm_expr_tag=reflow_room_info&unique_id=stream-408133045733294858_778_flv_ld&t_id=037-20260815014013FC12803418095659A622-k6AHio"

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
resp = urllib.request.urlopen(req, timeout=12)
data = resp.read(524288)
resp.close()

pos = 9
if data[pos:pos + 4] == b"\x00\x00\x00\x00" and data[pos + 4] in (8, 9, 18):
    pos += 4
print("起始 pos =", pos)

counts = {"audio": 0, "video": 0, "script": 0}
aac_seq = 0
aac_raw = 0
soundfmt = set()
sr_table = [96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050,
            16000, 12000, 11025, 8000, 7350]

while pos + 11 <= len(data):
    ttype = data[pos]
    dsize = (data[pos + 1] << 16) | (data[pos + 2] << 8) | data[pos + 3]
    if ttype not in (8, 9, 18) or dsize <= 0 or dsize > (1 << 22):
        pos += 1
        continue
    if pos + 11 + dsize + 4 > len(data):
        break
    tag = data[pos + 11: pos + 11 + dsize]
    if ttype == 8:
        counts["audio"] += 1
        fmt = tag[0] >> 4
        soundfmt.add(fmt)
        if len(tag) >= 2:
            at = tag[1]
            if at == 0:
                aac_seq += 1
                if len(tag) >= 4 and aac_seq <= 2:
                    sf = (tag[2] >> 3) & 0x0F
                    ch = ((tag[2] & 7) << 1) | (tag[3] >> 7)
                    sr = sr_table[sf] if sf < len(sr_table) else "?"
                    print(f"  [AAC seq#{aac_seq}] ASC={tag[2:4].hex()} 采样率idx={sf}({sr}Hz) 声道={ch}")
            elif at == 1:
                aac_raw += 1
    elif ttype == 9:
        counts["video"] += 1
    else:
        counts["script"] += 1
    pos += 11 + dsize + 4
    if counts["audio"] + counts["video"] > 400:
        break

print("统计:", counts, "SoundFormat=", soundfmt, "AAC_seq=", aac_seq, "AAC_raw=", aac_raw)
if 10 in soundfmt and aac_raw > 0:
    print("结论: AAC 可提取 → ADTS → 现有解码路径 OK")
elif 10 in soundfmt:
    print("结论: AAC 确认（raw 帧少，正常）")
else:
    print("结论: 非 AAC, SoundFormat=", soundfmt)
