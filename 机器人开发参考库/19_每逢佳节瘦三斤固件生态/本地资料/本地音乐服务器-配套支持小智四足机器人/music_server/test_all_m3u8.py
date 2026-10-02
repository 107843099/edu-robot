# -*- coding: utf-8 -*-
"""批量测试所有 m3u8 电台：连通性 + 分片格式判断（TS / ID3+ADTS / 其他）"""
import re
import ssl
import socket
import urllib.request
import urllib.error

URLS = [
    ("中国之声", "http://ngcdn001.cnr.cn/live/zgzs/index.m3u8"),
    ("音乐之声", "http://ngcdn003.cnr.cn/live/yyzs/index.m3u8"),
    ("经典音乐广播", "http://ngcdn004.cnr.cn/live/dszs/index.m3u8"),
    ("中国交通广播", "http://ngcdn016.cnr.cn/live/gsgljtgb/index.m3u8"),
    ("相声小品频道", "http://ngcdn023.cnr.cn/live/xsxp/index.m3u8"),
    ("环球资讯广播", "http://sk.cri.cn/905.m3u8"),
    ("河南新闻广播", "https://stream.hndt.com/live/xinwen/playlist.m3u8"),
    ("河南交通广播", "https://stream.hndt.com/live/jiaotong/playlist.m3u8"),
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}


def get(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout)


def rel_url(base, seg):
    if seg.startswith("http"):
        return seg
    if seg.startswith("/"):
        m = re.match(r'(https?://[^/]+)', base)
        return m.group(1) + seg if m else base + seg
    slash = base.rfind("/")
    return base[:slash + 1] + seg


def classify(data):
    """判断分片格式"""
    if len(data) < 4:
        return "数据太短"
    if data[0] == 0x47:
        # TS 候选：看 0x47 是否按 188 对齐
        ok = sum(1 for i in range(0, min(len(data), 1880), 188) if data[i] == 0x47)
        total = min(len(data), 1880) // 188
        return f"TS容器 0x47对齐 {ok}/{total}" if ok >= total * 0.8 else f"TS? 对齐率低 {ok}/{total}"
    if data[:3] == b"ID3":
        sz = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
        off = 10 + sz
        if off + 2 <= len(data) and data[off] == 0xFF and (data[off + 1] & 0xF0) == 0xF0:
            return f"ID3+ADTS (ID3={sz}B → ADTS) ✅固件已支持"
        return f"ID3+其他 (ID3={sz}B, 后面 {data[off:off+4].hex() if off+4<=len(data) else '?'})"
    if data[0] == 0xFF and (data[1] & 0xF0) == 0xF0:
        return "裸ADTS (0xFFF) ✅固件已支持"
    return f"未知格式 开头 {data[:8].hex()}"


print("=" * 76)
for name, url in URLS:
    print(f"\n### {name}  {url}")
    try:
        r = get(url)
        ct = r.headers.get("Content-Type", "?")
        data = r.read(4000).decode("utf-8", "replace")
        r.close()
        print(f"  ① master: 200 OK  Content-Type={ct}")
        # 判断 master 还是 media
        lines = [l.strip() for l in data.splitlines() if l.strip()]
        seg_hint = None
        for l in lines:
            if l and not l.startswith("#"):
                seg_hint = l
                break
        if not seg_hint:
            print("  ② 播放列表里没有分片条目!")
            continue
        # 若指向 .m3u8 → 子播放列表
        cur = rel_url(url, seg_hint)
        if cur.lower().endswith(".m3u8"):
            print(f"  ② master→子列表: {cur}")
            try:
                r2 = get(cur)
                d2 = r2.read(4000).decode("utf-8", "replace")
                r2.close()
                seg2 = None
                for l in [x.strip() for x in d2.splitlines() if x.strip()]:
                    if l and not l.startswith("#"):
                        seg2 = l
                        break
                if not seg2:
                    print("  ③ 子列表无分片!")
                    continue
                cur = rel_url(cur, seg2)
            except Exception as e:
                print(f"  ② 子列表失败: {type(e).__name__} {e}")
                continue
        # 下载一个分片
        print(f"  ③ 分片: {cur}")
        try:
            r3 = get(cur)
            seg_data = r3.read(200000)
            r3.close()
            print(f"  ④ 分片 {len(seg_data)}B, 开头 {seg_data[:12].hex()} → {classify(seg_data)}")
        except urllib.error.HTTPError as e:
            print(f"  ④ 分片失败: HTTP {e.code}")
        except Exception as e:
            print(f"  ④ 分片失败: {type(e).__name__} {e}")
    except urllib.error.HTTPError as e:
        print(f"  ① 失败: HTTP {e.code} {e.reason}")
    except ssl.SSLError as e:
        print(f"  ① 失败: SSL {e.reason}")
    except socket.timeout:
        print(f"  ① 失败: 15s 超时")
    except Exception as e:
        print(f"  ① 失败: {type(e).__name__} {e}")

print("\n" + "=" * 76)
print("完成")
