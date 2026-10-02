# -*- coding: utf-8 -*-
"""健壮版：批量测试各类 m3u8 电台源（全局超时防挂起）"""
import re
import socket
import urllib.request
import urllib.error

socket.setdefaulttimeout(7)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      "Referer": "http://www.cnr.cn/"}

SOURCES = [
    ("CRI环球资讯905", "http://sk.cri.cn/905.m3u8"),
    ("CRI轻松调频915", "http://sk.cri.cn/915.m3u8"),
    ("CNR中国之声", "http://ngcdn001.cnr.cn/live/zgzs/index.m3u8"),
    ("CNR经济之声", "http://ngcdn002.cnr.cn/live/jjzs/index.m3u8"),
    ("青岛新闻广播", "http://media.qtv.com.cn/live/fm1076.m3u8"),
    ("深圳新闻广播", "http://live.szmg.com.cn/live/fm898.m3u8"),
    ("深圳交通广播", "http://live.szmg.com.cn/live/fm1062.m3u8"),
    ("山东人民广播", "http://live.iqilu.com/radio/sdgb.m3u8"),
    ("四川新闻广播", "http://live.sctv.com/live/newsradio.m3u8"),
    ("南京新闻广播", "http://live.nanjingtv.com.cn/live/xwgb.m3u8"),
    ("杭州新闻广播", "http://live.hoolo.tv/radio/hzxw.m3u8"),
]

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=7)

def rel(base, seg):
    if seg.startswith("http"):
        return seg
    if seg.startswith("/"):
        m = re.match(r'(https?://[^/]+)', base)
        return (m.group(1) + seg) if m else (base + seg)
    return base[:base.rfind("/") + 1] + seg

def classify(data):
    if len(data) < 4:
        return "数据太短"
    if data[0] == 0x47:
        ok = sum(1 for i in range(0, min(len(data), 1880), 188) if data[i] == 0x47)
        total = min(len(data), 1880) // 188
        return f"TS 0x47对齐 {ok}/{total} → 固件已支持"
    if data[:3] == b"ID3":
        sz = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
        off = 10 + sz
        if off + 2 <= len(data) and data[off] == 0xFF and (data[off + 1] & 0xF0) == 0xF0:
            return f"ID3+ADTS (ID3={sz}B) → 固件已支持"
        return f"ID3+其他 开头{data[off:off+4].hex()}"
    if data[0] == 0xFF and (data[1] & 0xF0) == 0xF0:
        return "裸ADTS → 固件已支持"
    if data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return "MP3帧 → MP3路径"
    if data[:4] in (b"\x00\x00\x00\x18", b"\x00\x00\x00\x1c") or data[4:8] == b"ftyp":
        return f"fMP4! 开头{data[:16].hex()} → 固件不支持"
    return f"未知 开头{data[:8].hex()}"

for name, url in SOURCES:
    try:
        r = get(url)
        data = r.read(4000).decode("utf-8", "replace")
        r.close()
        lines = [l.strip() for l in data.splitlines() if l.strip() and not l.startswith("#")]
        if not lines:
            print(f"{name}: 列表无分片")
            continue
        cur = rel(url, lines[0])
        if cur.lower().endswith(".m3u8"):
            try:
                r2 = get(cur)
                d2 = r2.read(4000).decode("utf-8", "replace")
                r2.close()
                seg2 = next((l.strip() for l in d2.splitlines() if l.strip() and not l.startswith("#")), None)
                if not seg2:
                    print(f"{name}: 子列表无分片")
                    continue
                cur = rel(cur, seg2)
            except Exception as e:
                print(f"{name}: 子列表失败 {type(e).__name__} {e}")
                continue
        try:
            r3 = get(cur)
            seg = r3.read(200000)
            r3.close()
            print(f"{name}: ✅ {len(seg)}B → {classify(seg)}")
        except Exception as e:
            print(f"{name}: 分片失败 {type(e).__name__} {e}")
    except urllib.error.HTTPError as e:
        print(f"{name}: ❌ HTTP {e.code}")
    except Exception as e:
        print(f"{name}: ❌ {type(e).__name__} {e}")
print("=" * 60)
print("批量测试完成")
