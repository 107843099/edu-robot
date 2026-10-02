# -*- coding: utf-8 -*-
"""测试 4 个直播流：B站HLS / 快手FLV / 斗鱼HLS / 虎牙FLV"""
import re
import socket
import urllib.request
import urllib.error

socket.setdefaulttimeout(10)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

STREAMS = [
    ("B站直播HLS", "https://cn-lnsy-cu-01-04.bilivideo.com/live-bvc/105790/live_get06_SbWUXqR_5bn36_minihevc/index.m3u8?expires=1786734422&len=0&oi=720079484&pt=html5&qn=250&trid=10073d6e215f615df1f2339899ff7c6a7f59&bmt=2&sigparams=cdn,expires,len,oi,pt,qn,trid,bmt&cdn=cn-gotcha01&sign=bbbbce95e317840f497016638bcad1d5&site=cc90a082c1f4d121749424873c7941aa&free_type=0&mid=0&sche=ban&bvchls=1&sid=cn-lnsy-cu-01-04&chash=1&sg=lr&trace=8388641&isp=cu&rg=Central&pv=Henan&media_type=0&sl=2&deploy_env=prod&strategy_types=0,1&hot_cdn=909705&flvsk=8962a384f71263fade544d380bffd9eb&suffix=minihevc&ld=jchz&score=55&codec=1&strategy_id=25&hdr_type=0&strategy_ids=25,122&p2p_type=-1&strategy_type=0&origin_bitrate=920&expected_qn=250&source=puv3_onetier&pp=rtmp&info_source=cache&sk=b47ae0b83de4e4ef54530695dbae0c6e&vd=nc&zoneid_l=151388162&sid_l=live_get06_SbWUXqR_5bn36_minihevc&src=puv3&order=1"),
    ("快手直播FLV", "https://ws-origin.pull.yximgs.com/gifshow/S-06lbnp5Ek_GameHevcHdL0.flv?wsTime=6a80abe7&wsSecret=97510ef78906002aa453b0e5e488bf18&stat=GNFEapbD5O9gui0ILRSaE0AaB33BKbryK79qrgJHY6Z1SuIJq0SP3IUFvd2MVl9b&tsc=origin&oidc=edgeWm&sidc=2527&no_script=1&ss=s20&tfc_buyer=0&kabr_spts=-5000"),
    ("斗鱼直播HLS", "https://8ddca311e293b672ebd1cc5dfb38442e.livehwc4.com/openhls-hw.douyucdn2.cn/live/10040721rse3fggE_2000.m3u8?token=h5-douyu-0-10040721-ce2d230e5ebc7f373869c20683d901ba&vhost=play3&origin=hw&txTime=6a7f750a&sub_m3u8=true&did=5002694d785ac4482107cf39000717p1&txSecret=d50843bce6bcb62fe444177172ef6e4a&edge_slice=true&user_session_id=acfeb186a3a3e57adf003424bb3faaed&sid=435084644"),
    ("虎牙直播FLV", "https://tx.flv.huya.com/src/2208606321-2208606321-9485891918433878016-4417336098-10057-A-0-1-imgplus.flv?wsSecret=d27254c670c1d0505219ab89a44ace34&wsTime=6a80aa12&seqid=3257946344093&ctype=tars_mobile&ver=1&fs=bgct&t=103&ratio=2000&dMod=mseh-0&sdkPcdn=1_1&uid=1471215686253&uuid=444065043&t=103&sv=202603162019&sdk_sid=1786730657817&a_block=0"),
]

HEADERS = {"User-Agent": UA, "Referer": "https://live.bilibili.com/"}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=10)

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
        return f"TS容器 {ok}/{total}"
    if data[:3] == b"ID3":
        sz = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
        off = 10 + sz
        if off + 2 <= len(data) and data[off] == 0xFF and (data[off + 1] & 0xF0) == 0xF0:
            return f"ID3+ADTS"
        return f"ID3+其他({data[off:off+4].hex()})"
    if data[0] == 0xFF and (data[1] & 0xF0) == 0xF0:
        return "裸ADTS"
    if data[4:8] == b"ftyp" or data[:3] == b"\x00\x00\x00":
        return f"fMP4/MP4! {data[8:12] if len(data)>=12 else ''}"
    return f"未知 {data[:8].hex()}"

def analyze_flv(data):
    pos = 9
    if data[pos:pos+4] == b"\x00\x00\x00\x00" and data[pos+4] in (8, 9, 18):
        pos += 4
    audio = 0
    video = 0
    sfmt = set()
    aac_seq = 0
    for _ in range(300):
        if pos + 11 > len(data):
            break
        ttype = data[pos]
        dsize = (data[pos+1] << 16) | (data[pos+2] << 8) | data[pos+3]
        if ttype not in (8, 9, 18) or dsize <= 0 or dsize > (1 << 22):
            pos += 1
            continue
        if pos + 11 + dsize + 4 > len(data):
            break
        tag = data[pos+11: pos+11+dsize]
        if ttype == 8:
            audio += 1
            sfmt.add(tag[0] >> 4)
            if len(tag) >= 2 and tag[1] == 0:
                aac_seq += 1
                if len(tag) >= 4:
                    sf = ((tag[2] & 7) << 1) | (tag[3] >> 7)
                    ch = (tag[3] >> 3) & 0x0F
        elif ttype == 9:
            video += 1
        pos += 11 + dsize + 4
    return audio, video, sfmt, aac_seq

for name, url in STREAMS:
    print(f"\n{'='*70}\n### {name}")
    try:
        r = get(url)
        ct = r.headers.get("Content-Type", "?")
        print(f"  连接OK Content-Type={ct}")
        if ".m3u8" in url.lower() or ct.find("mpegurl") >= 0:
            data = r.read(4000).decode("utf-8", "replace")
            r.close()
            lines = [l.strip() for l in data.splitlines() if l.strip() and not l.startswith("#")]
            if not lines:
                print("  列表无分片")
                continue
            cur = rel(url, lines[0])
            if cur.lower().endswith(".m3u8"):
                r2 = get(cur)
                d2 = r2.read(4000).decode("utf-8", "replace")
                r2.close()
                print(f"  子列表: {cur.split('?')[0][-60:]}")
                seg2 = next((l.strip() for l in d2.splitlines() if l.strip() and not l.startswith("#")), None)
                if not seg2:
                    print("  子列表无分片")
                    continue
                cur = rel(cur, seg2)
            r3 = get(cur)
            seg = r3.read(200000)
            r3.close()
            print(f"  分片: {cur.split('?')[0][-70:]}")
            print(f"  分片 {len(seg)}B → {classify(seg)}")
        else:
            data = r.read(524288)
            r.close()
            print(f"  数据 {len(data)}B 开头 {data[:16].hex()}")
            if data[:3] == b"FLV":
                a, v, sf, aacseq = analyze_flv(data)
                print(f"  FLV: audio={a} video={v} SoundFormat={sf} AAC_seq={aacseq}")
                if 10 in sf:
                    print("  ✅ AAC 音频 → 固件 FLV 支持可播")
                else:
                    print(f"  ⚠️ 音频 SoundFormat={sf}（10=AAC），非 AAC 则不支持")
            else:
                print(f"  非FLV → {classify(data[:64])}")
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP {e.code}")
    except socket.timeout:
        print(f"  ❌ 超时")
    except Exception as e:
        print(f"  ❌ {type(e).__name__} {e}")
print("\n" + "="*70 + "\n完成")
