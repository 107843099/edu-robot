# -*- coding: utf-8 -*-
"""从公开聚合源抓取中国电台 m3u8 直播地址（iptv-org + 其他）"""
import urllib.request
import re

SOURCES = [
    ("iptv-org-cn", "https://iptv-org.github.io/iptv/countries/cn.m3u"),
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

all_items = []
for name, url in SOURCES:
    try:
        text = fetch(url)
        lines = text.splitlines()
        cur_meta = ""
        for line in lines:
            if line.startswith("#EXTINF"):
                cur_meta = line
            elif line.strip() and not line.startswith("#"):
                all_items.append((cur_meta, line.strip()))
        print(f"{name}: 共 {len(all_items)} 条")
    except Exception as e:
        print(f"{name} 抓取失败: {e}")

# 电台关键词（排除电视）
radio_kw = ["广播", "电台", "之声", "radio", "fm", "am", "交通台", "音乐台", "新闻台",
            "经济台", "文艺台", "体育台", "私家车", "音乐广播", "交通广播", "新闻广播",
            "经济广播", "都市广播", "生活广播", "故事广播", "音乐之声", "轻松调频",
            "hitfm", "cri", "cnr"]
tv_kw = ["tv", "卫视", "频道", "电影", "电视剧", "新闻综合", "科教", "公共频道", "cctv",
         "纪实", "少儿", "动画", "体育频道", "影视"]

radio_hits = []
for meta, url in all_items:
    low = meta.lower() + " " + url.lower()
    if any(k in low for k in radio_kw) and not any(k in low for k in tv_kw):
        radio_hits.append((meta, url))

print(f"\n筛选出电台 {len(radio_hits)} 条:")
m3u8_hits = []
seen = set()
for meta, url in radio_hits:
    if url in seen:
        continue
    seen.add(url)
    if ".m3u8" in url.lower() or "hls" in url.lower() or "live" in url.lower() or "stream" in url.lower():
        m3u8_hits.append((meta, url))
        print(f"  {meta[:60]:<62} {url[:80]}")

with open(r"E:\music_server\radio_m3u8_candidates.txt", "w", encoding="utf-8") as f:
    for meta, url in m3u8_hits:
        f.write(f"{meta}\t{url}\n")
print(f"\nm3u8/live 候选 {len(m3u8_hits)} 条 → radio_m3u8_candidates.txt")
