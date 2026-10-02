from PIL import Image
import argparse

# ---------------- 配置区域 ----------------
# 使用前请修改下方路径为实际文件位置
# 或者通过命令行参数传入: python bmp.py -i input.png -o output.bmp
INPUT_PATH = r"input.png"      # ← 请改为你的输入图片路径
OUTPUT_PATH = r"output.bmp"    # ← 请改为你的输出文件路径
TARGET_W = 128
TARGET_H = 64
# 二值化阈值：灰度大于阈值=白色；小于=黑色，0~255，可微调
THRESHOLD = 128
# ------------------------------------------

def main():
    global INPUT_PATH, OUTPUT_PATH
    parser = argparse.ArgumentParser(description='Convert image to 128x64 monochrome BMP')
    parser.add_argument('-i', '--input', help='Input image path')
    parser.add_argument('-o', '--output', help='Output BMP path')
    parser.add_argument('-t', '--threshold', type=int, default=THRESHOLD, help='Binarization threshold (0-255)')
    args = parser.parse_args()

    input_path = args.input or INPUT_PATH
    output_path = args.output or OUTPUT_PATH
    threshold = args.threshold

    # 打开原图
    im = Image.open(input_path)
    # 缩放至128×64，使用像素插值，适合像素画
    im = im.resize((TARGET_W, TARGET_H), Image.Resampling.NEAREST)
    # 转灰度图
    gray = im.convert("L")

    # 二值化处理（只有黑、白两种像素）
    def binarize(pixel):
        return 255 if pixel > threshold else 0

    bin_img = gray.point(binarize, mode="1")

    # 保存BMP
    bin_img.save(output_path, format="BMP")
    print(f"转换完成！输出文件：{output_path}")
    print("图片尺寸：", bin_img.size)
    print(f"阈值：{threshold}")
    print("✅ 严格128×64 黑白二值图，可直接PCtoLCD2002导入")

if __name__ == '__main__':
    main()