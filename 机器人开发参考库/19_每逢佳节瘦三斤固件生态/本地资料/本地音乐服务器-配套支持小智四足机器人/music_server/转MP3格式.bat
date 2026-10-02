@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==================================================
echo  批量转换音频格式 → MP3
echo  支持的格式: ogg wav flac m4a aac wma ape
echo ==================================================
echo.
echo  注意: 需要安装 ffmpeg
echo  下载地址: https://ffmpeg.org/download.html
echo  下载后把 ffmpeg.exe 放到本目录即可
echo.
python convert_to_mp3.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ 运行失败
    pause
    exit /b
)
echo.
pause