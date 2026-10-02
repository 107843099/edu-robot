"""测试各种音乐源能否获取真实MP3下载链接"""
import json, ssl, re, urllib.request, urllib.parse

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_source(name, url, headers=None, extract_mp3=True):
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"URL: {url}")
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.baidu.com/',
            **(headers or {})
        })
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        text = resp.read().decode('utf-8', errors='replace')
        print(f"状态: {resp.status} | 大小: {len(text)}")
        
        if extract_mp3:
            # 查找所有.mp3链接
            mp3s = re.findall(r'https?://[^"\'\s]+\.mp3[^"\'<\s]*', text)
            if mp3s:
                print(f"✅ 找到 {len(mp3s)} 个MP3文件!")
                for m in mp3s[:3]:
                    print(f"   {m[:120]}")
            else:
                print("❌ 未找到MP3链接")
                # 显示前200字符
                print(f"   内容预览: {text[:200]}")
        else:
            print(f"   内容: {text[:200]}")
    except Exception as e:
        print(f"❌ 失败: {type(e).__name__}: {e}")

kw = urllib.parse.quote('周杰伦')

# 1. 歌曲宝 - 使用HTML搜索页
test_source("歌曲宝 HTML搜索", f"https://www.gequbao.com/s/{kw}")

# 2. 歌曲宝 - 测试一个已知歌曲详情页
test_source("歌曲宝 已知MP3测试", "https://www.gequbao.com/music/1986353106")

# 3. 音乐-163 (netease 公开api, 不需要cookie)
test_source("网易云公开API", f"https://music.163.com/api/search/get/web?type=1&s={kw}&limit=3",
            {'Referer': 'https://music.163.com/'})

# 4. 试试新的AA1接口 (type=2 可能不同)
test_source("aa1.cn type=2", f"https://zj.v.api.aa1.cn/api/qqmusic/demo.php?type=2&q={kw}",
            {'Referer': 'https://zj.v.api.aa1.cn/'})

# 5. 另一个免费API
test_source("free-api", f"https://api.uomg.com/api/rand.music?format=json&sort=热歌榜&keyword={kw}")

# 6. 直接测试: 歌曲宝已知MP3 CDN
print("\n\n=== 手动测试歌曲宝MP3 CDN ===")
test_ids = ['1986353106', '1986351298', '1986350542']
for sid in test_ids:
    test_source(f"歌曲宝详情 #{sid}", f"https://www.gequbao.com/music/{sid}")