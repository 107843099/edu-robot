# -*- coding: utf-8 -*-
"""抓 iptv-org 全量列表 → 筛电台(m3u8) → 批量测试格式"""
import re
import socket
import urllib.request
import urllib.error

socket.setdefaulttimeout(25)
UA = {"User-Agent": "Mozilla/5.0"}

INDEX = "https://iptv-org.github.io/iptv/index.m3u"

print("下载 index.m3u ...")
req = urllib.request.Request(INDEX, headers=UA)
text = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
print(f"下载完成 {len(text)//1024} KB")

# 解析
items = []
cur_meta = ""
for line in text.splitlines():
    if line.startswith("#EXTINF"):
        cur_meta = line
    elif line.strip() and not line.startswith("#"):
        items.append((cur_meta, line.strip()))
print(f"总条目 {len(items)}")

# 筛电台：group-title 含 radio / 名称含广播·电台·之声等
radio_kw = ["广播", "电台", "之声", "radio", "fm", "交通台", "音乐台", "轻松调频"]
tv_kw = ["tv", "卫视", "频道", "cctv", "电影", "纪实", "少儿", "动画", "cctv-"]
radio_items = []
for meta, url in items:
    low = (meta + " " + url).lower()
    gt = re.search(r'group-title="([^"]*)"', meta)
    group = gt.group(1).lower() if gt else ""
    is_radio = ("radio" in group) or (any(k in low for k in radio_kw) and not any(k in low for k in tv_kw))
    if is_radio:
        radio_items.append((meta, url))

print(f"电台条目 {len(radio_items)}")

# 只保留 m3u8
m3u8 = [(meta, u) for meta, u in radio_items if ".m3u8" in u.lower() or "hls" in u.lower()]
print(f"m3u8 电台 {len(m3u8)}")
for meta, u in m3u8[:30]:
    name = meta.split(",")[-1].strip() if "," in meta else meta
    print(f"  {name:<40} {u[:70]}")

with open(r"E:\music_server\radio_m3u8_candidates.txt", "w", encoding="utf-8") as f:
    for meta, u in m3u8:
        name = meta.split(",")[-1].strip() if "," in meta else meta
        f.write(f"{name}\t{u}\n")
print("已保存 radio_m3u8_candidates.txt")
