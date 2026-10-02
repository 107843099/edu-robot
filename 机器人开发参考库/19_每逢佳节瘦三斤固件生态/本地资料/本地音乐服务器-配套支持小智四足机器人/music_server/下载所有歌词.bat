@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==================================================
echo  下载所有歌曲的歌词
echo ==================================================
echo.
python download_lyrics.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ 运行失败，请先安装依赖: pip install requests
    pause
    exit /b
)
echo.
pause