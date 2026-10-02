"""
格式转换工具 - 将 ogg/wav/flac/m4a 批量转为 mp3
需要安装 ffmpeg: https://ffmpeg.org/download.html

下载 ffmpeg 后把 ffmpeg.exe 所在目录添加到系统 PATH 环境变量，
或者把 ffmpeg.exe 放到本脚本同目录下。

使用方法:
  python convert_to_mp3.py                           # 转换 music 目录下所有非 mp3 文件
  python convert_to_mp3.py --delete-original          # 转换后删除原文件
  python convert_to_mp3.py --input-dir "E:\其他音乐"   # 转换其他目录
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# ==================== 配置 ====================

MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")
SUPPORTED_INPUT_FORMATS = (".ogg", ".wav", ".flac", ".m4a", ".aac", ".wma", ".ape")

# ==================== 工具函数 ====================

def find_ffmpeg():
    """查找 ffmpeg 可执行文件"""
    # 1. 先看当前目录
    local = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")
    if os.path.exists(local):
        return local

    # 2. 看当前目录下的 ffmpeg-* 文件夹里的 bin\ffmpeg.exe
    base = os.path.dirname(__file__)
    try:
        for entry in os.listdir(base):
            full = os.path.join(base, entry)
            if os.path.isdir(full) and "ffmpeg" in entry.lower():
                candidate = os.path.join(full, "bin", "ffmpeg.exe")
                if os.path.exists(candidate):
                    return candidate
    except:
        pass

    # 3. 看系统 PATH
    try:
        if sys.platform == "win32":
            result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True)
        else:
            result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except:
        pass

    return None


def get_audio_files(music_dir: str) -> list:
    """扫描目录获取所有非 mp3 音频文件"""
    files = []
    music_path = Path(music_dir)
    if not music_path.exists():
        return files

    for f in music_path.rglob("*"):
        if f.suffix.lower() in SUPPORTED_INPUT_FORMATS:
            files.append({
                "path": str(f),
                "stem": f.stem,
                "suffix": f.suffix,
                "dir": str(f.parent),
            })

    # 按目录分组排序
    files.sort(key=lambda x: x["path"])
    return files


def convert_file(ffmpeg_path: str, input_path: str, output_path: str, bitrate: str = "192k") -> bool:
    """转换单个文件为 mp3"""
    try:
        cmd = [
            ffmpeg_path,
            "-i", input_path,
            "-codec:a", "libmp3lame",
            "-b:a", bitrate,
            "-y",  # 覆盖输出文件
            output_path
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        if result.returncode == 0:
            return True
        else:
            print(f"    ❌ ffmpeg 错误: {result.stderr.strip()[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    ❌ 转换超时")
        return False
    except FileNotFoundError:
        print(f"    ❌ 找不到 ffmpeg.exe，请先安装")
        return False
    except Exception as e:
        print(f"    ❌ 转换失败: {e}")
        return False


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f}KB"
    else:
        return f"{size_bytes/1024/1024:.1f}MB"


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="音频格式转换工具 - 批量转为 MP3")
    parser.add_argument("--input-dir", type=str, default=MUSIC_DIR,
                        help=f"输入目录（默认: {MUSIC_DIR}）")
    parser.add_argument("--delete-original", action="store_true",
                        help="转换成功后删除原文件")
    parser.add_argument("--bitrate", type=str, default="192k",
                        help="MP3 比特率（默认: 192k，可选: 128k/192k/256k/320k）")
    parser.add_argument("--list", "-l", action="store_true",
                        help="列出需要转换的文件，不转换")
    args = parser.parse_args()

    # 查找 ffmpeg
    ffmpeg_path = find_ffmpeg()

    # 打印信息
    print("=" * 60)
    print("  音频格式转换工具 → MP3")
    print("=" * 60)
    print(f"  输入目录: {args.input_dir}")

    if ffmpeg_path:
        print(f"  ffmpeg:   {ffmpeg_path}")
    else:
        print()
        print("  ⚠ 未找到 ffmpeg！")
        print("  请下载 ffmpeg: https://ffmpeg.org/download.html")
        print("  下载后把 ffmpeg.exe 放到脚本同目录，或添加到系统 PATH")
        print()
        print("  或使用命令安装（需要 chocolatey）:")
        print("    choco install ffmpeg")
        print()
        input("  按回车键退出...")
        return

    # 获取文件
    files = get_audio_files(args.input_dir)

    if not files:
        print(f"\n  ✅ 没有需要转换的非 mp3 文件")
        print()
        return

    print(f"  需要转换: {len(files)} 个文件")
    print()

    # 列出文件
    print(f"  {'':2} {'文件名':<36} {'格式':<6} {'大小':<10}")
    print(f"  {'':2} {'─'*36} {'─'*6} {'─'*10}")
    for i, f in enumerate(files):
        fname = os.path.basename(f["path"])
        fname_display = fname[:34] if len(fname) > 34 else fname
        try:
            size = os.path.getsize(f["path"])
            size_str = format_size(size)
        except:
            size_str = "?"
        print(f"  {i+1:2} {fname_display:<36} {f['suffix'].upper():<6} {size_str:<10}")
    print()

    if args.list:
        return

    # 确认
    print(f"  将转换 {len(files)} 个文件到 MP3 (比特率: {args.bitrate})")
    if args.delete_original:
        print("  ⚠ 转换后将删除原文件")
    print()
    try:
        confirm = input("  是否继续? (y/N): ")
    except:
        confirm = "n"
    if confirm.lower() != "y":
        print("  已取消")
        return

    # 开始转换
    print(f"\n  {'='*50}")
    print(f"  开始转换...")
    print(f"  {'='*50}\n")

    success = 0
    failed = 0
    skipped = 0

    for i, f in enumerate(files):
        input_path = f["path"]
        output_path = os.path.join(f["dir"], f["stem"] + ".mp3")

        # 如果目标 mp3 已存在
        if os.path.exists(output_path):
            print(f"  [{i+1}/{len(files)}] ⏭ {f['stem']}.mp3 已存在 (跳过)")
            skipped += 1
            continue

        print(f"  [{i+1}/{len(files)}] 🔄 转换: {os.path.basename(input_path)}")
        print(f"        → {f['stem']}.mp3")

        if convert_file(ffmpeg_path, input_path, output_path, args.bitrate):
            success += 1
            print(f"        ✅ 转换成功")

            # 删除原文件
            if args.delete_original:
                try:
                    os.remove(input_path)
                    print(f"        🗑 已删除原文件: {os.path.basename(input_path)}")
                except Exception as e:
                    print(f"        ⚠ 删除原文件失败: {e}")
        else:
            failed += 1

    # 总结
    print(f"\n  {'='*50}")
    print(f"  转换完成!")
    total = success + failed + skipped
    print(f"  总计: {total} 个 | ✅ 成功: {success} | ❌ 失败: {failed} | ⏭ 跳过: {skipped}")

    if success > 0:
        print(f"\n  💡 提示: 重启音乐服务器后新歌曲会生效")
        print(f"    http://{args.input_dir.replace(MUSIC_DIR, '')}")
        print(f"    cd {os.path.dirname(__file__)} && python server.py")


if __name__ == "__main__":
    main()